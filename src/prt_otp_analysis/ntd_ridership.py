"""Load NTD Monthly Ridership data from Excel into prt.db (ntd_agency + ntd_ridership tables)."""

import re
import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
NTD_DIR = DATA_DIR / "ntd-monthly-ridership"

XLSX_FILE = NTD_DIR / (
    "December 2025 Complete Monthly Ridership "
    "(with adjustments and estimates)_260202.xlsx"
)

MONTH_RE = re.compile(r"^\d{1,2}/\d{4}$")  # e.g. "1/2002", "12/2025"


def _convert_month(col_name: str) -> str:
    """Convert NTD month format '1/2002' to 'YYYY-MM'."""
    m, y = col_name.split("/")
    return f"{y}-{int(m):02d}"


def load_master() -> pl.DataFrame:
    """Read Master sheet and return agency dimension data."""
    import fastexcel

    wb = fastexcel.read_excel(str(XLSX_FILE))
    df = wb.load_sheet_by_name("Master").to_polars()

    # Filter out rows with null NTD ID
    df = df.filter(pl.col("NTD ID").is_not_null())

    # Select and rename columns
    agency = df.select(
        ntd_id=pl.col("NTD ID").cast(pl.Int64),
        agency_name=pl.col("Agency"),
        mode=pl.col("Mode"),
        tos=pl.col("TOS"),
        hq_city=pl.col("HQ City"),
        hq_state=pl.col("HQ State"),
        uza_name=pl.col("UZA Name"),
    )

    return agency


def _load_metric_sheet(sheet_name: str, metric_col: str, dtype: pl.DataType) -> pl.DataFrame:
    """Read one wide monthly sheet (UPT/VRH/VRM) and unpivot to long format."""
    import fastexcel

    wb = fastexcel.read_excel(str(XLSX_FILE))
    df = wb.load_sheet_by_name(sheet_name).to_polars()

    # Filter out rows with null NTD ID (footer/summary rows)
    df = df.filter(pl.col("NTD ID").is_not_null())

    # Identify month columns by regex
    month_cols = [c for c in df.columns if MONTH_RE.match(str(c))]
    id_cols = ["NTD ID", "Mode", "TOS"]

    # Unpivot wide to long
    long = df.select(id_cols + month_cols).unpivot(
        on=month_cols,
        index=id_cols,
        variable_name="month_raw",
        value_name=metric_col,
    )

    # Convert month format and types
    month_map = {m: _convert_month(m) for m in month_cols}
    long = long.with_columns(
        ntd_id=pl.col("NTD ID").cast(pl.Int64),
        month=pl.col("month_raw").replace(month_map),
    ).with_columns(pl.col(metric_col).cast(dtype, strict=False))

    return long.select(
        "ntd_id", pl.col("Mode").alias("mode"), pl.col("TOS").alias("tos"), "month", metric_col
    )


def load_ridership() -> pl.DataFrame:
    """Load monthly UPT, VRH, and VRM by agency/mode/TOS, joined to one frame.

    VRH (vehicle revenue hours) and VRM (vehicle revenue miles) come from
    sibling sheets in the same workbook and share the UPT grain, so productivity
    (UPT / VRH) can be computed per mode without a separate table.
    """
    upt = _load_metric_sheet("UPT", "upt", pl.Int64)
    vrh = _load_metric_sheet("VRH", "vrh", pl.Float64)
    vrm = _load_metric_sheet("VRM", "vrm", pl.Float64)

    keys = ["ntd_id", "mode", "tos", "month"]
    return upt.join(vrh, on=keys, how="left").join(vrm, on=keys, how="left")


def write_to_db(agency: pl.DataFrame, ridership: pl.DataFrame) -> None:
    """Write ntd_agency and ntd_ridership tables to prt.db."""
    conn = sqlite3.connect(DB_PATH)

    # ntd_agency
    conn.execute("DROP TABLE IF EXISTS ntd_ridership")
    conn.execute("DROP TABLE IF EXISTS ntd_agency")
    conn.execute("""
        CREATE TABLE ntd_agency (
            ntd_id         INTEGER NOT NULL,
            agency_name    TEXT NOT NULL,
            mode           TEXT NOT NULL,
            tos            TEXT NOT NULL,
            hq_city        TEXT,
            hq_state       TEXT,
            uza_name       TEXT,
            PRIMARY KEY (ntd_id, mode, tos)
        )
    """)
    conn.executemany(
        "INSERT INTO ntd_agency (ntd_id, agency_name, mode, tos, hq_city, hq_state, uza_name) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        agency.rows(),
    )

    # ntd_ridership
    conn.execute("""
        CREATE TABLE ntd_ridership (
            ntd_id  INTEGER NOT NULL,
            mode    TEXT NOT NULL,
            tos     TEXT NOT NULL,
            month   TEXT NOT NULL,
            upt     INTEGER,
            vrh     REAL,
            vrm     REAL,
            PRIMARY KEY (ntd_id, mode, tos, month),
            FOREIGN KEY (ntd_id, mode, tos) REFERENCES ntd_agency(ntd_id, mode, tos)
        )
    """)
    conn.executemany(
        "INSERT INTO ntd_ridership (ntd_id, mode, tos, month, upt, vrh, vrm) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ridership.select("ntd_id", "mode", "tos", "month", "upt", "vrh", "vrm").rows(),
    )

    conn.commit()

    agency_count = conn.execute("SELECT COUNT(*) FROM ntd_agency").fetchone()[0]
    ridership_count = conn.execute("SELECT COUNT(*) FROM ntd_ridership").fetchone()[0]
    conn.close()
    print(f"  Wrote {agency_count} rows to ntd_agency")
    print(f"  Wrote {ridership_count} rows to ntd_ridership")


def main() -> None:
    """Entry point: load NTD Excel data and write to prt.db."""
    print("=" * 60)
    print("NTD Monthly Ridership ETL")
    print("=" * 60)

    # Step 1: Load Master sheet
    print("\n1. Loading Master sheet (agency data)...")
    agency = load_master()
    print(f"  {len(agency)} agency-mode-TOS rows")
    print(f"  Unique agencies: {agency['ntd_id'].n_unique()}")

    # Step 2: Load UPT, VRH, VRM sheets
    print("\n2. Loading UPT/VRH/VRM sheets (ridership + service data)...")
    ridership = load_ridership()
    print(f"  {len(ridership)} ridership rows (long format)")
    non_null = ridership.filter(pl.col("upt").is_not_null())
    print(f"  {len(non_null)} rows with non-null UPT")
    vrh_non_null = ridership.filter(pl.col("vrh").is_not_null())
    print(f"  {len(vrh_non_null)} rows with non-null VRH")
    print(f"  Month range: {ridership['month'].min()} to {ridership['month'].max()}")

    # Step 3: Write to DB
    print("\n3. Writing to database...")
    write_to_db(agency, ridership)

    # Step 4: Verification
    print("\n4. Verification...")

    # PRT data
    prt = ridership.filter(pl.col("ntd_id") == 30022)
    print("\n  PRT (NTD ID 30022):")
    print(f"    Rows: {len(prt)}")
    print(f"    Modes: {prt['mode'].unique().sort().to_list()}")
    prt_2024 = prt.filter(pl.col("month").str.starts_with("2024"))
    prt_2024_total = prt_2024["upt"].sum()
    print(f"    2024 total UPT: {prt_2024_total:,.0f}")

    # Top 10 agencies by 2024 UPT
    year_2024 = ridership.filter(pl.col("month").str.starts_with("2024"))
    top10 = (
        year_2024.group_by("ntd_id")
        .agg(total_upt=pl.col("upt").sum())
        .sort("total_upt", descending=True)
        .head(10)
    )
    # Join agency names
    names = agency.select("ntd_id", "agency_name").unique(subset=["ntd_id"])
    top10 = top10.join(names, on="ntd_id", how="left")
    print("\n  Top 10 agencies by 2024 UPT:")
    for row in top10.iter_rows(named=True):
        print(f"    {row['agency_name']:<45s} {row['total_upt']:>15,.0f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
