"""Classify OTP null values as not_operating, unreported, or no_coverage using schedule and ridership cross-references."""

import sqlite3
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "prt.db"


def classify_otp_nulls(
    otp_routes: list[str],
    otp_months: list[str],
    otp_pairs: set[tuple[str, str]],
    schedule_pairs: set[tuple[str, str]],
    ridership_pairs: set[tuple[str, str]],
    schedule_range: tuple[str, str],
    ridership_range: tuple[str, str],
) -> pl.DataFrame:
    """Classify each missing OTP route-month.

    For every (route, month) in the full grid that lacks an OTP value,
    assigns a reason:
      - unreported:     evidence the route was operating (schedule or ridership)
      - not_operating:  within coverage of at least one source, but no evidence
      - no_coverage:    month falls outside both schedule and ridership ranges

    And an evidence field: schedule, ridership, both, or none.
    """
    sched_min, sched_max = schedule_range
    rider_min, rider_max = ridership_range

    full_grid = {(r, m) for r in otp_routes for m in otp_months}
    missing = full_grid - otp_pairs

    rows: list[dict[str, str]] = []
    for route, month in sorted(missing):
        in_sched_range = sched_min <= month <= sched_max
        in_rider_range = rider_min <= month <= rider_max

        has_schedule = (route, month) in schedule_pairs
        has_ridership = (route, month) in ridership_pairs

        # Determine evidence
        if has_schedule and has_ridership:
            evidence = "both"
        elif has_schedule:
            evidence = "schedule"
        elif has_ridership:
            evidence = "ridership"
        else:
            evidence = "none"

        # Determine reason
        if has_schedule or has_ridership:
            reason = "unreported"
        elif in_sched_range or in_rider_range:
            reason = "not_operating"
        else:
            reason = "no_coverage"

        rows.append({
            "route_id": route,
            "month": month,
            "reason": reason,
            "evidence": evidence,
        })

    return pl.DataFrame(
        rows,
        schema={"route_id": pl.Utf8, "month": pl.Utf8, "reason": pl.Utf8, "evidence": pl.Utf8},
    )


def build_from_db(db_path: Path | None = None) -> pl.DataFrame:
    """Extract inputs from prt.db, classify nulls, and return the result DataFrame."""
    db = db_path or DB_PATH
    conn = sqlite3.connect(db)

    otp_routes = [r[0] for r in conn.execute("SELECT DISTINCT route_id FROM routes").fetchall()]
    otp_months = [r[0] for r in conn.execute("SELECT DISTINCT month FROM otp_monthly").fetchall()]
    otp_pairs = {
        (r[0], r[1]) for r in conn.execute("SELECT route_id, month FROM otp_monthly").fetchall()
    }

    # Schedule data
    try:
        schedule_pairs = {
            (r[0], r[1])
            for r in conn.execute(
                "SELECT DISTINCT route_id, month FROM scheduled_trips_monthly"
            ).fetchall()
        }
        sched_range_row = conn.execute(
            "SELECT MIN(month), MAX(month) FROM scheduled_trips_monthly"
        ).fetchone()
        schedule_range = (sched_range_row[0], sched_range_row[1])
    except sqlite3.OperationalError:
        schedule_pairs = set()
        schedule_range = ("9999-01", "0000-01")  # empty range

    # Ridership data
    try:
        ridership_pairs = {
            (r[0], r[1])
            for r in conn.execute(
                "SELECT DISTINCT route_id, month FROM ridership_monthly"
            ).fetchall()
        }
        rider_range_row = conn.execute(
            "SELECT MIN(month), MAX(month) FROM ridership_monthly"
        ).fetchone()
        ridership_range = (rider_range_row[0], rider_range_row[1])
    except sqlite3.OperationalError:
        ridership_pairs = set()
        ridership_range = ("9999-01", "0000-01")

    conn.close()

    return classify_otp_nulls(
        otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs,
        schedule_range, ridership_range,
    )


def write_to_db(result_df: pl.DataFrame, db_path: Path | None = None) -> None:
    """Write the otp_null_classification table to prt.db."""
    db = db_path or DB_PATH
    conn = sqlite3.connect(db)

    conn.execute("DROP TABLE IF EXISTS otp_null_classification")
    conn.execute("""
        CREATE TABLE otp_null_classification (
            route_id TEXT NOT NULL,
            month    TEXT NOT NULL,
            reason   TEXT NOT NULL,
            evidence TEXT NOT NULL,
            PRIMARY KEY (route_id, month)
        )
    """)
    conn.executemany(
        "INSERT INTO otp_null_classification (route_id, month, reason, evidence) VALUES (?, ?, ?, ?)",
        result_df.rows(),
    )
    conn.commit()
    conn.close()


def main() -> None:
    """Build and write the OTP null classification table."""
    print("Classifying OTP null values...")
    result_df = build_from_db()

    # Summary
    reason_counts = result_df.group_by("reason").len().sort("reason")
    print("\nClassification summary:")
    for row in reason_counts.iter_rows():
        print(f"  {row[0]:<15} {row[1]:>5} route-months")
    print(f"  {'TOTAL':<15} {len(result_df):>5} route-months")

    # Top unreported routes
    unreported_df = result_df.filter(pl.col("reason") == "unreported")
    if len(unreported_df) > 0:
        by_route = (
            unreported_df.group_by("route_id")
            .len()
            .sort("len", descending=True)
            .head(10)
        )
        print("\nTop unreported routes:")
        for row in by_route.iter_rows():
            print(f"  {row[0]:<10} {row[1]:>3} months")

    write_to_db(result_df)
    print(f"\nWrote {len(result_df)} rows to otp_null_classification table")


if __name__ == "__main__":
    main()
