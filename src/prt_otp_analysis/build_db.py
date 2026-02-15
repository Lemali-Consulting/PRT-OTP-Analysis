"""ETL script: load PRT CSV data into a normalized SQLite database."""

import sqlite3
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "prt.db"

# --- Route ID helpers ---

ROUTE_ID_OVERRIDES = {
    "MONONGAHELA INCLINE": "MI",
}

MONTH_MAP = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def parse_route_id(route_label: str) -> str:
    """Extract route_id from labels like '1 - FREEPORT ROAD'."""
    if route_label in ROUTE_ID_OVERRIDES:
        return ROUTE_ID_OVERRIDES[route_label]
    return route_label.split(" - ", 1)[0].strip()


def parse_route_name(route_label: str) -> str:
    """Extract route name from labels like '1 - FREEPORT ROAD'."""
    if " - " in route_label:
        return route_label.split(" - ", 1)[1].strip()
    return route_label


def parse_month_col(col_name: str) -> str:
    """Convert '2019-Jan' → '2019-01'."""
    year, mon = col_name.split("-")
    return f"{year}-{MONTH_MAP[mon]}"


# --- Schema ---

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS routes (
    route_id   TEXT PRIMARY KEY,
    route_name TEXT NOT NULL,
    mode       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id   TEXT PRIMARY KEY,
    stop_code INTEGER,
    stop_name TEXT NOT NULL,
    lat       REAL NOT NULL,
    lon       REAL NOT NULL,
    county    TEXT,
    muni      TEXT,
    hood      TEXT
);

CREATE TABLE IF NOT EXISTS route_stops (
    route_id  TEXT NOT NULL REFERENCES routes(route_id),
    stop_id   TEXT NOT NULL REFERENCES stops(stop_id),
    direction TEXT,
    trips_wd  INTEGER,
    trips_sa  INTEGER,
    trips_su  INTEGER,
    trips_7d  INTEGER,
    svc_days  TEXT,
    PRIMARY KEY (route_id, stop_id, direction)
);

CREATE TABLE IF NOT EXISTS stop_reference (
    stop_id     TEXT PRIMARY KEY,
    stop_code   INTEGER,
    stop_name   TEXT NOT NULL,
    stop_source TEXT,
    public_stop TEXT,
    lat         REAL NOT NULL,
    lon         REAL NOT NULL,
    mode        TEXT,
    first_served TEXT,
    last_served  TEXT,
    county      TEXT,
    muni        TEXT,
    hood        TEXT
);

CREATE TABLE IF NOT EXISTS otp_monthly (
    route_id TEXT NOT NULL REFERENCES routes(route_id),
    month    TEXT NOT NULL,
    otp      REAL,
    PRIMARY KEY (route_id, month)
);

CREATE TABLE IF NOT EXISTS ridership_monthly (
    route_id       TEXT NOT NULL,
    month          TEXT NOT NULL,
    day_type       TEXT NOT NULL,
    avg_riders     REAL,
    day_count      INTEGER,
    route_name     TEXT,
    current_garage TEXT,
    mode           TEXT,
    PRIMARY KEY (route_id, month, day_type)
);
"""


# --- ETL functions ---

def build_routes_table(
    otp_df: pl.DataFrame,
    routes_sys_df: pl.DataFrame,
) -> pl.DataFrame:
    """Union route info from OTP data and the current routes system file."""
    # From OTP data
    otp_routes = otp_df.select("Route").unique().with_columns(
        pl.col("Route").map_elements(parse_route_id, return_dtype=pl.String).alias("route_id"),
        pl.col("Route").map_elements(parse_route_name, return_dtype=pl.String).alias("route_name"),
    ).drop("Route")

    # From current routes system (one row per route, pick first occurrence)
    sys_routes = (
        routes_sys_df
        .select(
            pl.col("routes").cast(pl.String).alias("route_id"),
            pl.col("route_name"),
            pl.col("mode"),
        )
        .unique(subset=["route_id"], keep="first")
    )

    # Merge: prefer system file for name/mode, fill from OTP where missing
    merged = otp_routes.join(sys_routes, on="route_id", how="full", coalesce=True)
    merged = merged.with_columns(
        pl.coalesce("route_name", "route_name_right").alias("route_name"),
        pl.col("mode").fill_null("UNKNOWN"),
    ).select("route_id", "route_name", "mode")

    return merged


def build_otp_table(otp_df: pl.DataFrame) -> pl.DataFrame:
    """Unpivot wide OTP data into long format."""
    month_cols = [c for c in otp_df.columns if c != "Route"]

    long = otp_df.unpivot(
        on=month_cols,
        index="Route",
        variable_name="month_raw",
        value_name="otp",
    )

    long = long.with_columns(
        pl.col("Route").map_elements(parse_route_id, return_dtype=pl.String).alias("route_id"),
        pl.col("month_raw").map_elements(parse_month_col, return_dtype=pl.String).alias("month"),
    ).select("route_id", "month", "otp")

    # Drop rows where otp is null (missing data)
    long = long.filter(pl.col("otp").is_not_null())

    return long


def build_stops_table(stops_df: pl.DataFrame) -> pl.DataFrame:
    """Deduplicate to one row per physical stop."""
    return (
        stops_df
        .select(
            pl.col("stop_id"),
            pl.col("stop_code"),
            pl.col("stop_name"),
            pl.col("stop_lat").alias("lat"),
            pl.col("stop_lon").alias("lon"),
            pl.col("county"),
            pl.col("muni"),
            pl.col("hood"),
        )
        .unique(subset=["stop_id"], keep="first")
    )


def build_route_stops_table(stops_df: pl.DataFrame) -> pl.DataFrame:
    """Build bridge table from route-specific rows (exclude 'All Routes')."""
    filtered = stops_df.filter(pl.col("route_filter") != "All Routes")

    return (
        filtered
        .select(
            pl.col("routes").alias("route_id"),
            pl.col("stop_id"),
            pl.col("direction"),
            pl.col("trips_wd"),
            pl.col("trips_sa"),
            pl.col("trips_su"),
            pl.col("trips_7d"),
            pl.col("svc_days"),
        )
        .unique(subset=["route_id", "stop_id", "direction"], keep="first")
    )


def build_stop_reference_table(ref_df: pl.DataFrame) -> pl.DataFrame:
    """Extract core columns from the stop reference lookup table."""
    return ref_df.select(
        pl.col("stop_id"),
        pl.col("stop_code"),
        pl.col("stop_name"),
        pl.col("stop_source"),
        pl.col("public_stop"),
        pl.col("hastus_lat").alias("lat"),
        pl.col("hastus_lon").alias("lon"),
        pl.col("mode"),
        pl.col("first_served"),
        pl.col("last_served"),
        pl.col("county"),
        pl.col("muni"),
        pl.col("hood"),
    )


def build_ridership_table(ridership_df: pl.DataFrame) -> pl.DataFrame:
    """Normalize ridership CSV into long format keyed by route_id, month, day_type."""
    return ridership_df.select(
        pl.col("route").cast(pl.String).alias("route_id"),
        pl.col("month_start").str.slice(0, 7).alias("month"),  # "2017-01-01" → "2017-01"
        pl.col("day_type"),
        pl.col("avg_riders").cast(pl.Float64),
        pl.col("day_count").cast(pl.Int64),
        pl.col("route_full_name").alias("route_name"),
        pl.col("current_garage"),
        pl.col("mode"),
    )


def insert_df(conn: sqlite3.Connection, table: str, df: pl.DataFrame) -> int:
    """Insert a polars DataFrame into a SQLite table. Returns row count."""
    rows = df.to_dicts()
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in cols)
    col_names = ", ".join(cols)
    conn.executemany(
        f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})",
        [tuple(r[c] for c in cols) for r in rows],
    )
    conn.commit()
    return len(rows)


# --- Main ---

def main():
    print(f"Data directory: {DATA_DIR}")
    print(f"Database path:  {DB_PATH}\n")

    # Read source CSVs
    print("Reading CSVs...")
    otp_df = pl.read_csv(
        DATA_DIR / "routes_by_month.csv",
        infer_schema_length=0,  # read everything as string first
    )
    # Cast OTP columns to float (empty strings become null)
    month_cols = [c for c in otp_df.columns if c != "Route"]
    otp_df = otp_df.with_columns(
        [pl.col(c).replace("", None).cast(pl.Float64, strict=False) for c in month_cols]
    )

    routes_sys_df = pl.read_csv(
        DATA_DIR / "PRT_Current_Routes_Full_System_de0e48fcbed24ebc8b0d933e47b56682.csv",
    )

    stops_df = pl.read_csv(
        DATA_DIR / "Transit_stops_(current)_by_route_e040ee029227468ebf9d217402a82fa9.csv",
    )

    ref_df = pl.read_csv(
        DATA_DIR / "PRT_Stop_Reference_Lookup_Table.csv",
    )

    ridership_csv = DATA_DIR / "average-ridership" / "12bb84ed-397e-435c-8d1b-8ce543108698.csv"
    ridership_df = pl.read_csv(ridership_csv, infer_schema_length=0)

    # Build normalized tables
    print("Building tables...")
    routes = build_routes_table(otp_df, routes_sys_df)
    otp = build_otp_table(otp_df)
    stops = build_stops_table(stops_df)
    route_stops = build_route_stops_table(stops_df)
    stop_ref = build_stop_reference_table(ref_df)
    ridership = build_ridership_table(ridership_df)

    # Write to SQLite
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.Connection(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)

    print("\nLoading tables into SQLite...")
    for name, df in [
        ("routes", routes),
        ("stops", stops),
        ("route_stops", route_stops),
        ("stop_reference", stop_ref),
        ("otp_monthly", otp),
        ("ridership_monthly", ridership),
    ]:
        count = insert_df(conn, name, df)
        print(f"  {name:20s} {count:>8,} rows")

    # Verification queries
    print("\n--- Verification ---")
    cur = conn.execute("SELECT COUNT(*) FROM routes")
    print(f"Total routes: {cur.fetchone()[0]}")

    cur = conn.execute("SELECT COUNT(*) FROM otp_monthly")
    print(f"Total OTP observations: {cur.fetchone()[0]}")

    cur = conn.execute("""
        SELECT r.route_id, r.route_name, r.mode, COUNT(o.month) as months,
               ROUND(AVG(o.otp), 4) as avg_otp
        FROM routes r
        LEFT JOIN otp_monthly o ON r.route_id = o.route_id
        GROUP BY r.route_id
        ORDER BY avg_otp DESC
        LIMIT 10
    """)
    print("\nTop 10 routes by average OTP:")
    print(f"  {'Route':<8} {'Name':<35} {'Mode':<12} {'Months':>6} {'Avg OTP':>8}")
    print(f"  {'-'*8} {'-'*35} {'-'*12} {'-'*6} {'-'*8}")
    for row in cur.fetchall():
        route_id, name, mode, months, avg_otp = row
        avg_str = f"{avg_otp:.1%}" if avg_otp else "N/A"
        print(f"  {route_id:<8} {(name or ''):<35} {mode:<12} {months:>6} {avg_str:>8}")

    cur = conn.execute("""
        SELECT r.route_id, r.route_name, COUNT(DISTINCT rs.stop_id) as stop_count
        FROM routes r
        JOIN route_stops rs ON r.route_id = rs.route_id
        GROUP BY r.route_id
        ORDER BY stop_count DESC
        LIMIT 5
    """)
    print("\nTop 5 routes by stop count:")
    for row in cur.fetchall():
        print(f"  {row[0]:<8} {row[1]:<35} {row[2]} stops")

    conn.close()
    print(f"\nDone. Database written to {DB_PATH}")


if __name__ == "__main__":
    main()
