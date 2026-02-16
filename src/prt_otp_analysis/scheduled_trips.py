"""Fetch WPRDC scheduled trip counts per route/month and write to scheduled_trips_monthly and schedule_periods tables."""

import sqlite3
import urllib.request
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
CACHE_DIR = DATA_DIR / "wprdc-schedule"

MONTHLY_URL = (
    "https://data.wprdc.org/dataset/d1eb0fcd-ba60-4407-9969-ceef464d0c00"
    "/resource/1ca23fa8-53ca-43be-a7f7-82d4c7ff10f5"
    "/download/schedule_monthly_agg.csv"
)
PICKS_URL = (
    "https://data.wprdc.org/dataset/b401859c-412b-4cb6-ad88-a4183b83183d"
    "/resource/3f789a37-d02b-4f2e-9212-3b824fb06678"
    "/download/paac_pick_lookup.csv"
)

MONTHLY_CACHE = CACHE_DIR / "schedule_monthly_agg.csv"
PICKS_CACHE = CACHE_DIR / "paac_pick_lookup.csv"

# Map WPRDC rail route codes to our DB route_id format
RAIL_CODE_MAP = {
    "BLLB": "BLUE",
    "RED": "RED",
    "SLVR": "SLVR",
}


def fetch_csv(url: str, cache_path: Path) -> pl.DataFrame:
    """Download a CSV from WPRDC or load from cache."""
    if cache_path.exists():
        print(f"  Loading cached {cache_path.name}")
        return pl.read_csv(
        cache_path,
        schema_overrides={"PickID": pl.String, "dateKey": pl.String, "RouteCode": pl.String},
    )

    print(f"  Downloading {cache_path.name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"\n  ERROR: Failed to fetch {url}: {e}")
        print(f"  Download manually and save to: {cache_path}")
        raise

    # Normalize \r\r\n line endings (WPRDC quirk) to \n
    raw = raw.replace("\r\r\n", "\n").replace("\r\n", "\n")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8", newline="") as f:
        f.write(raw)
    print(f"  Cached to {cache_path}")

    return pl.read_csv(
        cache_path,
        schema_overrides={"PickID": pl.String, "dateKey": pl.String, "RouteCode": pl.String},
    )


def load_db_route_ids() -> set[str]:
    """Load route_ids from the routes table in prt.db."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT route_id FROM routes").fetchall()
    conn.close()
    return {r[0] for r in rows}


def transform_monthly(raw: pl.DataFrame, db_routes: set[str]) -> pl.DataFrame:
    """Clean and transform the monthly schedule CSV."""
    # Map route codes: apply rail mapping, keep others as-is
    df = raw.with_columns(
        route_id=pl.col("RouteCode").replace_strict(
            RAIL_CODE_MAP, default=pl.col("RouteCode")
        ),
    )

    # Convert dateKey (YYYYMM int) to month string (YYYY-MM)
    df = df.with_columns(
        month=pl.col("dateKey").cast(pl.String).str.slice(0, 4)
        + "-"
        + pl.col("dateKey").cast(pl.String).str.slice(4, 2),
    )

    # Rename and select final columns (WPRDC uses R-style names with dots)
    df = df.select(
        "route_id",
        "month",
        pl.col("Day.Type.Join").alias("day_type"),
        pl.col("Daily.Trip.Count").alias("daily_trips"),
        pl.col("Daily.Trip.Dist").alias("daily_trip_dist"),
        pl.col("PickID").cast(pl.String).alias("pick_id"),
        pl.col("Current_Garage").alias("garage"),
        pl.col("Mode").alias("mode"),
    )

    # Handle schedule transitions: when a month has two pick_ids for the same
    # route/day_type, keep the one with more trips (dominant schedule period)
    dupes = df.group_by(["route_id", "month", "day_type"]).len().filter(pl.col("len") > 1)
    if len(dupes) > 0:
        print(f"  Deduplicating {len(dupes)} rows with overlapping schedule periods...")
        df = (
            df.sort("daily_trips", descending=True)
            .unique(subset=["route_id", "month", "day_type"], keep="first")
        )

    # Report unmatched routes
    wprdc_routes = set(df["route_id"].unique().to_list())
    matched = wprdc_routes & db_routes
    wprdc_only = sorted(wprdc_routes - db_routes)
    db_only_sample = sorted(db_routes - wprdc_routes)[:20]

    print(f"  Route matching: {len(matched)} matched, {len(wprdc_only)} WPRDC-only, {len(db_routes - wprdc_routes)} DB-only")
    if wprdc_only:
        print(f"  WPRDC routes not in DB: {wprdc_only}")
    if db_only_sample:
        print(f"  DB routes not in WPRDC (sample): {db_only_sample}")

    return df


def transform_picks(raw: pl.DataFrame) -> pl.DataFrame:
    """Clean and transform the schedule periods CSV."""
    df = raw.select(
        pl.col("pickID").cast(pl.String).alias("pick_id"),
        pl.col("pickStart").alias("start_date"),
        pl.col("pickEnd").alias("end_date"),
    )
    return df


def write_to_db(monthly: pl.DataFrame, picks: pl.DataFrame) -> None:
    """Write scheduled_trips_monthly and schedule_periods tables (drop/recreate)."""
    conn = sqlite3.connect(DB_PATH)

    # --- schedule_periods ---
    conn.execute("DROP TABLE IF EXISTS schedule_periods")
    conn.execute("""
        CREATE TABLE schedule_periods (
            pick_id    TEXT PRIMARY KEY,
            start_date TEXT NOT NULL,
            end_date   TEXT NOT NULL
        )
    """)
    conn.executemany(
        "INSERT INTO schedule_periods (pick_id, start_date, end_date) VALUES (?, ?, ?)",
        picks.rows(),
    )

    # --- scheduled_trips_monthly ---
    conn.execute("DROP TABLE IF EXISTS scheduled_trips_monthly")
    conn.execute("""
        CREATE TABLE scheduled_trips_monthly (
            route_id         TEXT NOT NULL,
            month            TEXT NOT NULL,
            day_type         TEXT NOT NULL,
            daily_trips      INTEGER NOT NULL,
            daily_trip_dist  REAL NOT NULL,
            pick_id          TEXT NOT NULL,
            garage           TEXT,
            mode             TEXT,
            PRIMARY KEY (route_id, month, day_type)
        )
    """)
    conn.executemany(
        """INSERT INTO scheduled_trips_monthly
           (route_id, month, day_type, daily_trips, daily_trip_dist, pick_id, garage, mode)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        monthly.rows(),
    )

    conn.commit()

    stm_count = conn.execute("SELECT COUNT(*) FROM scheduled_trips_monthly").fetchone()[0]
    sp_count = conn.execute("SELECT COUNT(*) FROM schedule_periods").fetchone()[0]
    conn.close()

    print(f"  Wrote {stm_count} rows to scheduled_trips_monthly")
    print(f"  Wrote {sp_count} rows to schedule_periods")


def verify(monthly: pl.DataFrame) -> None:
    """Print verification stats including OTP overlap and COVID signal."""
    conn = sqlite3.connect(DB_PATH)
    otp_months = {r[0] for r in conn.execute("SELECT DISTINCT month FROM otp_monthly").fetchall()}
    conn.close()

    sched_months = set(monthly["month"].unique().to_list())
    overlap = sorted(sched_months & otp_months)

    print(f"\n  Schedule months: {sorted(sched_months)[0]} to {sorted(sched_months)[-1]} ({len(sched_months)} months)")
    print(f"  OTP months: {sorted(otp_months)[0]} to {sorted(otp_months)[-1]} ({len(otp_months)} months)")
    print(f"  Overlap: {len(overlap)} months ({overlap[0]} to {overlap[-1]})")

    # COVID signal: weekday trip counts in Mar vs Apr 2020
    weekday = monthly.filter(pl.col("day_type") == "WEEKDAY")

    mar2020 = weekday.filter(pl.col("month") == "2020-03")["daily_trips"].sum()
    apr2020 = weekday.filter(pl.col("month") == "2020-04")["daily_trips"].sum()
    if mar2020 and apr2020:
        pct_change = (apr2020 - mar2020) / mar2020 * 100
        print(f"\n  COVID check (weekday total daily_trips):")
        print(f"    Mar 2020: {mar2020:,}")
        print(f"    Apr 2020: {apr2020:,}")
        print(f"    Change:   {pct_change:+.1f}%")


def main() -> None:
    """Entry point: fetch WPRDC data, transform, write to DB."""
    print("=" * 60)
    print("WPRDC Scheduled Trip Counts ETL")
    print("=" * 60)

    # Step 1: Fetch CSVs
    print("\n1. Fetching WPRDC data...")
    raw_monthly = fetch_csv(MONTHLY_URL, MONTHLY_CACHE)
    raw_picks = fetch_csv(PICKS_URL, PICKS_CACHE)
    print(f"  Monthly records: {len(raw_monthly)}")
    print(f"  Schedule periods: {len(raw_picks)}")

    # Step 2: Transform
    print("\n2. Transforming data...")
    print(f"  Monthly columns: {raw_monthly.columns}")
    print(f"  Picks columns: {raw_picks.columns}")

    db_routes = load_db_route_ids()
    print(f"  DB routes: {len(db_routes)}")

    monthly = transform_monthly(raw_monthly, db_routes)
    picks = transform_picks(raw_picks)

    print(f"\n  Final monthly: {len(monthly)} rows, {monthly['route_id'].n_unique()} routes, {monthly['month'].n_unique()} months")
    print(f"  Final periods: {len(picks)} rows")

    # Step 3: Write to DB
    print("\n3. Writing to database...")
    write_to_db(monthly, picks)

    # Step 4: Verify
    print("\n4. Verification...")
    date_range = monthly["month"].sort()
    print(f"  Date range: {date_range[0]} to {date_range[-1]}")
    print(f"  Routes: {monthly['route_id'].n_unique()}")
    print(f"  Day types: {monthly['day_type'].unique().to_list()}")

    verify(monthly)

    print("\nDone.")


if __name__ == "__main__":
    main()
