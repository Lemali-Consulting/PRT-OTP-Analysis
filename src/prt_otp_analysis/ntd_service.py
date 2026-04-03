"""Load NTD TS2.2 annual service data (VRH, VRM, UPT, VOMS) into prt.db."""

import re
import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
NTD_DIR = DATA_DIR / "ntd-annual-service"

# Old file covers 1991-2023; new file covers 2015-2024.
# We load both and prefer the newer file for overlapping years.
XLSX_OLD = NTD_DIR / "2023_TS2.2_Service_Data.xlsx"
XLSX_NEW = NTD_DIR / "2024_TS2.2_Service_Data.xlsx"

# Sheets to load and their target column names
METRIC_SHEETS = {
    "VRH": "vrh",
    "VRM": "vrm",
    "UPT": "upt",
    "VOMS": "voms",
    "FARES": "fares",
    "OpExp Total": "opexp",
    "OpExp VO": "opexp_vo",
    "OpExp VM": "opexp_vm",
    "OpExp NVM": "opexp_nvm",
    "OpExp GA": "opexp_ga",
}

# Sheet names that differ between workbook releases (2023 vs 2024).
# Keys are canonical names used in METRIC_SHEETS; values are alternates to try.
_SHEET_ALIASES: dict[str, list[str]] = {
    "FARES": ["Fares"],
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


def _resolve_sheet_name(wb_sheets: list[str], canonical: str) -> str:
    """Return the actual sheet name in the workbook, handling aliases."""
    if canonical in wb_sheets:
        return canonical
    for alt in _SHEET_ALIASES.get(canonical, []):
        if alt in wb_sheets:
            return alt
    raise ValueError(f"Sheet '{canonical}' not found in workbook (available: {wb_sheets})")


def _read_sheet(xlsx_path: Path, sheet_name: str, metric_col: str) -> pl.DataFrame:
    """Read one TS2.2 sheet and unpivot year columns to long format."""
    import fastexcel

    wb = fastexcel.read_excel(str(xlsx_path))
    actual_name = _resolve_sheet_name(wb.sheet_names, sheet_name)
    df = wb.load_sheet_by_name(actual_name).to_polars()

    # Filter out rows with null NTD ID
    df = df.filter(pl.col("NTD ID").is_not_null())

    # Identify year columns (could be string or int headers — all are strings here)
    year_cols = [c for c in df.columns if YEAR_RE.match(str(c))]

    # Only select ID_COLS that exist in this file (schema varies across releases)
    available_id_cols = [c for c in ID_COLS if c in df.columns]

    # Unpivot year columns to long format
    long = df.select(available_id_cols + year_cols).unpivot(
        on=year_cols,
        index=available_id_cols,
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


def _read_agency_info(xlsx_path: Path) -> pl.DataFrame:
    """Read agency identifier columns from the VRH sheet."""
    import fastexcel

    wb = fastexcel.read_excel(str(xlsx_path))
    df = wb.load_sheet_by_name("VRH").to_polars()
    df = df.filter(pl.col("NTD ID").is_not_null())

    select_exprs = {"ntd_id": pl.col("NTD ID").cast(pl.Int64)}
    for orig, alias in ID_COLS.items():
        if orig != "NTD ID" and orig in df.columns:
            select_exprs[alias] = pl.col(orig)

    agency = df.select(**select_exprs).unique(subset=["ntd_id"])

    # Ensure all expected columns exist (fill missing with null)
    for alias in ID_COLS.values():
        if alias not in agency.columns:
            agency = agency.with_columns(pl.lit(None).alias(alias))

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
            fares        REAL,
            opexp        REAL,
            opexp_vo     REAL,
            opexp_vm     REAL,
            opexp_nvm    REAL,
            opexp_ga     REAL,
            PRIMARY KEY (ntd_id, year)
        )
    """)
    metric_cols = list(METRIC_SHEETS.values())
    id_cols = ["ntd_id", "agency_name", "city", "state", "uza_name", "year"]
    all_cols = id_cols + metric_cols
    placeholders = ", ".join(["?"] * len(all_cols))
    col_names = ", ".join(all_cols)
    conn.executemany(
        f"INSERT INTO ntd_annual_service ({col_names}) VALUES ({placeholders})",
        data.select(all_cols).rows(),
    )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM ntd_annual_service").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to ntd_annual_service")


def _load_file(xlsx_path: Path, label: str) -> pl.DataFrame:
    """Load all metric sheets from one TS2.2 file and join them."""
    metrics: dict[str, pl.DataFrame] = {}
    for sheet_name, col_name in METRIC_SHEETS.items():
        print(f"  Loading {label} {sheet_name}...")
        df = _read_sheet(xlsx_path, sheet_name, col_name)
        non_null = df.filter(pl.col(col_name).is_not_null())
        print(f"    {len(non_null)} non-null rows")
        metrics[col_name] = df

    col_names = list(METRIC_SHEETS.values())
    joined = metrics[col_names[0]]
    for col_name in col_names[1:]:
        joined = joined.join(metrics[col_name], on=["ntd_id", "year"], how="left")

    return joined


def main() -> None:
    """Entry point: load NTD TS2.2 annual service data and write to prt.db."""
    print("=" * 60)
    print("NTD Annual Service ETL (TS2.2)")
    print("=" * 60)

    # Step 1: Load old file (1991-2023)
    print("\n1. Loading old file (1991-2023)...")
    old_df = _load_file(XLSX_OLD, "old")
    print(f"  {len(old_df)} rows from old file")

    # Step 2: Load new file (2015-2024)
    print("\n2. Loading new file (2015-2024)...")
    new_df = _load_file(XLSX_NEW, "new")
    print(f"  {len(new_df)} rows from new file")

    # Step 3: Merge — keep old rows for years not in the new file, prefer new for overlap
    print("\n3. Merging files (new file takes precedence for overlapping years)...")
    new_keys = new_df.select("ntd_id", "year").unique()
    old_only = old_df.join(new_keys, on=["ntd_id", "year"], how="anti")
    joined = pl.concat([old_only, new_df])
    print(f"  {len(old_only)} rows from old file only (pre-2015)")
    print(f"  {len(new_df)} rows from new file")
    print(f"  {len(joined)} total rows after merge")

    # Step 4: Attach agency identifiers (prefer new file for up-to-date names)
    print("\n4. Attaching agency identifiers...")
    agency_new = _read_agency_info(XLSX_NEW)
    agency_old = _read_agency_info(XLSX_OLD)
    # New file takes precedence; fill gaps from old
    agency = pl.concat([agency_new, agency_old]).unique(subset=["ntd_id"], keep="first")
    print(f"  {len(agency)} unique agencies")
    joined = joined.join(agency, on="ntd_id", how="left")

    # Step 5: Write to DB
    print("\n5. Writing to database...")
    write_to_db(joined)

    # Step 6: Verification
    print("\n6. Verification...")
    years = sorted(joined["year"].unique().to_list())
    print(f"  Year range: {years[0]}-{years[-1]}")

    prt = joined.filter(pl.col("ntd_id") == 30022)
    prt_recent = prt.filter(pl.col("year").is_in([2019, 2023, 2024])).sort("year")
    print("\n  PRT (NTD ID 30022):")
    for row in prt_recent.iter_rows(named=True):
        vrh = f"{row['vrh']:,.0f}" if row["vrh"] else "N/A"
        vrm = f"{row['vrm']:,.0f}" if row["vrm"] else "N/A"
        upt = f"{row['upt']:,.0f}" if row["upt"] else "N/A"
        voms = f"{row['voms']:,.0f}" if row["voms"] else "N/A"
        print(f"    {row['year']}: VRH={vrh}  VRM={vrm}  UPT={upt}  VOMS={voms}")

    # Top 10 by 2024 VRH
    top10 = (
        joined.filter((pl.col("year") == 2024) & pl.col("vrh").is_not_null())
        .sort("vrh", descending=True)
        .head(10)
    )
    print(f"\n  Top 10 agencies by 2024 VRH:")
    for row in top10.iter_rows(named=True):
        print(f"    {row['agency_name']:<50s} {row['vrh']:>12,.0f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
