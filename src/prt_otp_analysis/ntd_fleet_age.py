"""Load NTD fleet age distribution data from the Socrata API into prt.db."""

import json
import sqlite3
from pathlib import Path
from urllib.request import urlopen

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
FLEET_DIR = DATA_DIR / "ntd-fleet-age"

# Socrata dataset: "2022-2024 NTD Annual Data - Vehicles (Age Distribution)"
DATASET_ID = "6abt-uhgq"
BASE_URL = f"https://data.transportation.gov/resource/{DATASET_ID}.json"

# Socrata stores NTD IDs as zero-padded strings; our DB uses integers.
# We fetch broadly and filter after converting.
YEARS = [2022, 2023, 2024]


def _fetch_year(year: int) -> list[dict]:
    """Fetch all rows for a given report year from the Socrata API."""
    limit = 5000
    offset = 0
    all_rows: list[dict] = []
    while True:
        url = f"{BASE_URL}?$where=report_year='{year}'&$limit={limit}&$offset={offset}"
        with urlopen(url) as resp:
            rows = json.loads(resp.read())
        if not rows:
            break
        all_rows.extend(rows)
        offset += limit
    return all_rows


def fetch_all() -> list[dict]:
    """Fetch fleet age data for all years."""
    all_rows: list[dict] = []
    for year in YEARS:
        print(f"  Fetching {year}...")
        rows = _fetch_year(year)
        print(f"    {len(rows)} rows")
        all_rows.extend(rows)
    return all_rows


def to_dataframe(raw: list[dict]) -> pl.DataFrame:
    """Convert raw Socrata JSON to a clean DataFrame."""
    records = []
    for r in raw:
        ntd_id_str = r.get("ntd_id", "").strip()
        if not ntd_id_str:
            continue
        try:
            ntd_id = int(ntd_id_str)
        except ValueError:
            continue
        vtype = r.get("vehicle_type", "")
        if not vtype:
            continue
        total = r.get("total_vehicles")
        avg_age = r.get("average_age_of_fleet_in_years")
        avg_miles = r.get("average_lifetime_miles_per")
        records.append({
            "ntd_id": ntd_id,
            "year": int(r.get("report_year", 0)),
            "vehicle_type": vtype,
            "total_vehicles": int(total) if total else None,
            "avg_age": float(avg_age) if avg_age else None,
            "avg_miles": float(avg_miles) if avg_miles else None,
        })
    df = pl.DataFrame(records)
    # A few agencies report the same vehicle type twice (different TOS).
    # Aggregate: sum vehicles, weighted-average age and miles.
    df = df.with_columns(
        age_weight=(pl.col("avg_age") * pl.col("total_vehicles")),
        miles_weight=(pl.col("avg_miles") * pl.col("total_vehicles")),
    )
    df = (
        df.group_by("ntd_id", "year", "vehicle_type")
        .agg(
            total_vehicles=pl.col("total_vehicles").sum(),
            age_weight=pl.col("age_weight").sum(),
            miles_weight=pl.col("miles_weight").sum(),
        )
        .with_columns(
            avg_age=(pl.col("age_weight") / pl.col("total_vehicles")),
            avg_miles=(pl.col("miles_weight") / pl.col("total_vehicles")),
        )
        .drop("age_weight", "miles_weight")
    )
    return df


def write_to_db(df: pl.DataFrame) -> None:
    """Write ntd_fleet_age table to prt.db."""
    conn = sqlite3.connect(DB_PATH)

    conn.execute("DROP TABLE IF EXISTS ntd_fleet_age")
    conn.execute("""
        CREATE TABLE ntd_fleet_age (
            ntd_id         INTEGER NOT NULL,
            year           INTEGER NOT NULL,
            vehicle_type   TEXT NOT NULL,
            total_vehicles INTEGER,
            avg_age        REAL,
            avg_miles      REAL,
            PRIMARY KEY (ntd_id, year, vehicle_type)
        )
    """)
    conn.executemany(
        "INSERT INTO ntd_fleet_age "
        "(ntd_id, year, vehicle_type, total_vehicles, avg_age, avg_miles) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        df.select("ntd_id", "year", "vehicle_type",
                  "total_vehicles", "avg_age", "avg_miles").rows(),
    )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM ntd_fleet_age").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to ntd_fleet_age")


def main() -> None:
    """Entry point: fetch NTD fleet age data and write to prt.db."""
    print("=" * 60)
    print("NTD Fleet Age ETL")
    print("=" * 60)

    print("\n1. Fetching data from Socrata API...")
    raw = fetch_all()
    print(f"  {len(raw)} total rows fetched")

    # Save raw data for provenance
    FLEET_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = FLEET_DIR / "fleet_age_raw.json"
    with open(raw_path, "w") as f:
        json.dump(raw, f)
    print(f"  Raw data saved to {raw_path}")

    print("\n2. Converting to DataFrame...")
    df = to_dataframe(raw)
    print(f"  {len(df)} rows after cleaning")

    print("\n3. Writing to database...")
    write_to_db(df)

    # Verification
    print("\n4. Verification...")
    from prt_otp_analysis.common import PEERS
    peer_df = df.filter(
        pl.col("ntd_id").is_in(list(PEERS.keys()))
        & (pl.col("year") == 2024)
        & (pl.col("vehicle_type") == "Bus")
    ).sort("avg_age", descending=True)
    print("\n  Peer city bus fleet age (2024):")
    for row in peer_df.iter_rows(named=True):
        city = PEERS.get(row["ntd_id"], str(row["ntd_id"]))
        age = f"{row['avg_age']:.1f}" if row["avg_age"] else "N/A"
        print(f"    {city:<15s} {row['total_vehicles']:>5d} buses, avg age {age} yrs")

    print("\nDone.")


if __name__ == "__main__":
    main()
