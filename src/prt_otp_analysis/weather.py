"""Fetch NOAA daily weather data for Pittsburgh and aggregate to monthly for the weather_monthly table."""

import sqlite3
import urllib.request
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
CACHE_DIR = DATA_DIR / "noaa-weather"
CACHE_FILE = CACHE_DIR / "daily_raw.csv"

STATION = "USW00094823"  # Pittsburgh International Airport
START_DATE = "2019-01-01"
END_DATE = "2025-12-31"

API_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1"
    f"?dataset=daily-summaries"
    f"&stations={STATION}"
    f"&startDate={START_DATE}"
    f"&endDate={END_DATE}"
    f"&dataTypes=PRCP,SNOW,SNWD,TMAX,TMIN,AWND"
    f"&format=csv"
    f"&units=metric"
)


def fetch_daily() -> pl.DataFrame:
    """Fetch daily weather data from NCEI API or load from cache."""
    if CACHE_FILE.exists():
        print(f"  Loading cached data from {CACHE_FILE}")
        df = pl.read_csv(CACHE_FILE)
        print(f"  {len(df)} cached daily records")
        return df

    print("  Fetching from NCEI API...")
    print(f"  URL: {API_URL}")
    req = urllib.request.Request(API_URL, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as e:
        print(f"\n  ERROR: Failed to fetch data from NCEI API: {e}")
        print(f"  Try downloading manually from:")
        print(f"  {API_URL}")
        print(f"  Save the CSV to: {CACHE_FILE}")
        raise

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(raw)
    print(f"  Cached raw CSV to {CACHE_FILE}")

    df = pl.read_csv(CACHE_FILE)
    print(f"  {len(df)} daily records fetched")
    return df


def aggregate_monthly(daily: pl.DataFrame) -> pl.DataFrame:
    """Aggregate daily weather observations to monthly summaries."""
    # Extract year-month from DATE column
    df = daily.with_columns(
        month=pl.col("DATE").str.slice(0, 7),
    )

    monthly = df.group_by("month").agg(
        total_precip_mm=pl.col("PRCP").sum(),
        snow_days=pl.col("SNOW").filter(pl.col("SNOW") > 0).count(),
        total_snow_mm=pl.col("SNOW").sum(),
        mean_tmax_c=pl.col("TMAX").mean(),
        mean_tmin_c=pl.col("TMIN").mean(),
        freeze_days=pl.col("TMIN").filter(pl.col("TMIN") < 0).count(),
        hot_days=pl.col("TMAX").filter(pl.col("TMAX") >= 32).count(),
        mean_wind_ms=pl.col("AWND").mean(),
        heavy_precip_days=pl.col("PRCP").filter(pl.col("PRCP") >= 25.0).count(),
        n_obs=pl.col("DATE").count(),
    ).sort("month")

    return monthly


def write_to_db(monthly: pl.DataFrame) -> None:
    """Write weather_monthly table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS weather_monthly")
    conn.execute("""
        CREATE TABLE weather_monthly (
            month              TEXT PRIMARY KEY,
            total_precip_mm    REAL,
            snow_days          INTEGER,
            total_snow_mm      REAL,
            mean_tmax_c        REAL,
            mean_tmin_c        REAL,
            freeze_days        INTEGER,
            hot_days           INTEGER,
            mean_wind_ms       REAL,
            heavy_precip_days  INTEGER,
            n_obs              INTEGER NOT NULL
        )
    """)

    rows = monthly.rows()
    conn.executemany(
        """INSERT INTO weather_monthly
           (month, total_precip_mm, snow_days, total_snow_mm, mean_tmax_c,
            mean_tmin_c, freeze_days, hot_days, mean_wind_ms,
            heavy_precip_days, n_obs)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM weather_monthly").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to weather_monthly table in {DB_PATH}")


def main() -> None:
    """Entry point: fetch NOAA data, aggregate monthly, write to DB."""
    print("=" * 60)
    print("NOAA Weather Data ETL")
    print("=" * 60)

    # Step 1: Fetch daily data
    print("\n1. Fetching daily weather data...")
    daily = fetch_daily()

    # Verification
    date_range = daily["DATE"].sort()
    print(f"  Date range: {date_range[0]} to {date_range[-1]}")
    print(f"  Columns: {daily.columns}")

    # Check for missing values
    for col in ["PRCP", "SNOW", "TMAX", "TMIN", "AWND"]:
        if col in daily.columns:
            null_count = daily[col].null_count()
            print(f"  {col}: {null_count} nulls out of {len(daily)} ({null_count/len(daily)*100:.1f}%)")

    # Step 2: Aggregate to monthly
    print("\n2. Aggregating to monthly...")
    monthly = aggregate_monthly(daily)
    print(f"  {len(monthly)} monthly records")

    # Print summary statistics
    print("\n  Monthly summary (first 6 months):")
    print(f"  {'Month':<10s} {'Precip':>8s} {'Snow d':>7s} {'Snow mm':>8s} {'Tmax':>6s} {'Tmin':>6s} {'Freeze':>7s} {'Hot':>5s} {'Wind':>6s} {'N':>4s}")
    for row in monthly.head(6).iter_rows(named=True):
        print(f"  {row['month']:<10s} {row['total_precip_mm']:>8.1f} {row['snow_days']:>7d} {row['total_snow_mm']:>8.1f} "
              f"{row['mean_tmax_c']:>6.1f} {row['mean_tmin_c']:>6.1f} {row['freeze_days']:>7d} {row['hot_days']:>5d} "
              f"{row['mean_wind_ms']:>6.1f} {row['n_obs']:>4d}")

    # Sanity checks
    winter = monthly.filter(pl.col("month").str.slice(5, 2).is_in(["12", "01", "02"]))
    summer = monthly.filter(pl.col("month").str.slice(5, 2).is_in(["06", "07", "08"]))
    print(f"\n  Winter avg snow_days: {winter['snow_days'].mean():.1f}")
    print(f"  Summer avg snow_days: {summer['snow_days'].mean():.1f}")
    print(f"  Winter avg freeze_days: {winter['freeze_days'].mean():.1f}")
    print(f"  Summer avg hot_days: {summer['hot_days'].mean():.1f}")

    # Step 3: Write to DB
    print("\n3. Writing to database...")
    write_to_db(monthly)

    # Verify month format alignment with otp_monthly
    conn = sqlite3.connect(DB_PATH)
    otp_months = [r[0] for r in conn.execute("SELECT DISTINCT month FROM otp_monthly ORDER BY month").fetchall()]
    weather_months = [r[0] for r in conn.execute("SELECT DISTINCT month FROM weather_monthly ORDER BY month").fetchall()]
    conn.close()

    overlap = set(otp_months) & set(weather_months)
    otp_only = set(otp_months) - set(weather_months)
    weather_only = set(weather_months) - set(otp_months)
    print(f"\n  Month key alignment:")
    print(f"  OTP months: {len(otp_months)}, Weather months: {len(weather_months)}")
    print(f"  Overlap: {len(overlap)}, OTP-only: {len(otp_only)}, Weather-only: {len(weather_only)}")
    if otp_only:
        print(f"  OTP months without weather: {sorted(otp_only)[:5]}...")
    if weather_only:
        print(f"  Weather months without OTP: {sorted(weather_only)[:5]}...")

    print("\nDone.")


if __name__ == "__main__":
    main()
