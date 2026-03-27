"""Load NTD TS2.2 annual service data (VRH, VRM, UPT, VOMS) into prt.db."""

import re
import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
NTD_DIR = DATA_DIR / "ntd-annual-service"

XLSX_FILE = NTD_DIR / "2023_TS2.2_Service_Data.xlsx"

# Sheets to load and their target column names
METRIC_SHEETS = {
    "VRH": "vrh",
    "VRM": "vrm",
    "UPT": "upt",
    "VOMS": "voms",
}

# Agency identifier columns to keep
ID_COLS = {
    "NTD ID": "ntd_id",
    "Agency Name": "agency_name",
    "City": "city",
    "State": "state",
    "Primary UZA Name": "uza_name",
}

YEAR_RE = re.compile(r"^\d{4}$")


def _read_sheet(sheet_name: str, metric_col: str) -> pl.DataFrame:
    """Read one TS2.2 sheet and unpivot year columns to long format."""
    import fastexcel

    wb = fastexcel.read_excel(str(XLSX_FILE))
    df = wb.load_sheet_by_name(sheet_name).to_polars()

    # Filter out rows with null NTD ID
    df = df.filter(pl.col("NTD ID").is_not_null())

    # Identify year columns (could be string or int headers — all are strings here)
    year_cols = [c for c in df.columns if YEAR_RE.match(str(c))]

    # Unpivot year columns to long format
    long = df.select(list(ID_COLS.keys()) + year_cols).unpivot(
        on=year_cols,
        index=list(ID_COLS.keys()),
        variable_name="year_str",
        value_name=metric_col,
    )

    # Cast types
    long = long.with_columns(
        pl.col("NTD ID").cast(pl.Int64).alias("ntd_id"),
        pl.col("year_str").cast(pl.Int64).alias("year"),
        pl.col(metric_col).cast(pl.Float64, strict=False),
    )

    return long.select("ntd_id", "year", metric_col)


def _read_agency_info() -> pl.DataFrame:
    """Read agency identifier columns from the VRH sheet."""
    import fastexcel

    wb = fastexcel.read_excel(str(XLSX_FILE))
    df = wb.load_sheet_by_name("VRH").to_polars()
    df = df.filter(pl.col("NTD ID").is_not_null())

    agency = df.select(
        ntd_id=pl.col("NTD ID").cast(pl.Int64),
        agency_name=pl.col("Agency Name"),
        city=pl.col("City"),
        state=pl.col("State"),
        uza_name=pl.col("Primary UZA Name"),
    ).unique(subset=["ntd_id"])

    return agency


def write_to_db(data: pl.DataFrame) -> None:
    """Write ntd_annual_service table to prt.db."""
    conn = sqlite3.connect(DB_PATH)

    conn.execute("DROP TABLE IF EXISTS ntd_annual_service")
    conn.execute("""
        CREATE TABLE ntd_annual_service (
            ntd_id       INTEGER NOT NULL,
            agency_name  TEXT,
            city         TEXT,
            state        TEXT,
            uza_name     TEXT,
            year         INTEGER NOT NULL,
            vrh          REAL,
            vrm          REAL,
            upt          REAL,
            voms         REAL,
            PRIMARY KEY (ntd_id, year)
        )
    """)
    conn.executemany(
        "INSERT INTO ntd_annual_service "
        "(ntd_id, agency_name, city, state, uza_name, year, vrh, vrm, upt, voms) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        data.select(
            "ntd_id", "agency_name", "city", "state", "uza_name",
            "year", "vrh", "vrm", "upt", "voms",
        ).rows(),
    )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM ntd_annual_service").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to ntd_annual_service")


def main() -> None:
    """Entry point: load NTD TS2.2 annual service data and write to prt.db."""
    print("=" * 60)
    print("NTD Annual Service ETL (TS2.2)")
    print("=" * 60)

    # Step 1: Read each metric sheet
    metrics = {}
    for sheet_name, col_name in METRIC_SHEETS.items():
        print(f"\n1. Loading {sheet_name} sheet...")
        df = _read_sheet(sheet_name, col_name)
        print(f"  {len(df)} rows (long format)")
        non_null = df.filter(pl.col(col_name).is_not_null())
        print(f"  {len(non_null)} rows with non-null {col_name}")
        metrics[col_name] = df

    # Step 2: Join all metrics on (ntd_id, year)
    print("\n2. Joining metrics...")
    joined = metrics["vrh"]
    for col_name in ["vrm", "upt", "voms"]:
        joined = joined.join(metrics[col_name], on=["ntd_id", "year"], how="left")

    print(f"  {len(joined)} rows after join")

    # Step 3: Attach agency identifiers
    print("\n3. Attaching agency identifiers...")
    agency = _read_agency_info()
    print(f"  {len(agency)} unique agencies")
    joined = joined.join(agency, on="ntd_id", how="left")

    # Step 4: Write to DB
    print("\n4. Writing to database...")
    write_to_db(joined)

    # Step 5: Verification
    print("\n5. Verification...")
    prt = joined.filter(pl.col("ntd_id") == 30022)
    prt_recent = prt.filter(pl.col("year").is_in([2019, 2023])).sort("year")
    print("\n  PRT (NTD ID 30022):")
    for row in prt_recent.iter_rows(named=True):
        print(f"    {row['year']}: VRH={row['vrh']:,.0f}  VRM={row['vrm']:,.0f}  "
              f"UPT={row['upt']:,.0f}  VOMS={row['voms']:,.0f}")

    # Top 10 by 2023 VRH
    top10 = (
        joined.filter((pl.col("year") == 2023) & pl.col("vrh").is_not_null())
        .sort("vrh", descending=True)
        .head(10)
    )
    print("\n  Top 10 agencies by 2023 VRH:")
    for row in top10.iter_rows(named=True):
        print(f"    {row['agency_name']:<50s} {row['vrh']:>12,.0f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
