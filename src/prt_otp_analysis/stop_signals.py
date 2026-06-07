"""Ingest PRT's authoritative bus-stop signal classification into the stop_signals table.

Reads the PRT-provided spreadsheet (bus stops tagged near-side / far-side / no-signal
at traffic signals), resolves each stop_code to its GTFS stop_id, and rebuilds the
stop_signals table in prt.db.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
SOURCE_XLSX = DATA_DIR / "prt-stop-signals" / "bus_stops_with_signals_2602.xlsx"

# PRT `mode` string -> canonical signal class stored in the table.
_MODE_TO_CLASS: dict[str, str] = {
    "BUS (NO SIGNAL)": "none",
    "BUS (SIGNAL-NEARSIDE)": "nearside",
    "BUS (SIGNAL-FARSIDE)": "farside",
    "BUSWAY/BRT": "busway",
}

# Classes that represent an actual at-signal stop (busway is dedicated ROW, not a signal).
_SIGNAL_CLASSES = frozenset({"nearside", "farside"})


def classify_signal(mode: str) -> str:
    """Map a PRT `mode` string to a canonical signal class.

    Returns one of: 'none', 'nearside', 'farside', 'busway'. Raises ValueError on an
    unrecognized value so new/typo'd source labels surface instead of being mis-bucketed.
    """
    key = " ".join(mode.strip().upper().split())
    try:
        return _MODE_TO_CLASS[key]
    except KeyError as exc:
        raise ValueError(f"Unrecognized PRT stop mode: {mode!r}") from exc


def has_signal(signal_class: str) -> bool:
    """Return True only for stops located at a (non-busway) traffic signal."""
    return signal_class in _SIGNAL_CLASSES


# ---------------------------------------------------------------------------
# ETL
# ---------------------------------------------------------------------------

def load_source() -> pl.DataFrame:
    """Read the PRT spreadsheet and derive signal_class / has_signal columns."""
    raw_df = pl.read_excel(SOURCE_XLSX)
    return raw_df.select(
        pl.col("stop_id").alias("prt_stop_id").cast(pl.Utf8),
        pl.col("stop_code").cast(pl.Int64),
        pl.col("stop_name").cast(pl.Utf8),
        pl.col("mode").alias("prt_mode").cast(pl.Utf8),
        pl.col("location").alias("prt_location").cast(pl.Utf8),
    ).with_columns(
        signal_class=pl.col("prt_mode").map_elements(classify_signal, return_dtype=pl.Utf8),
    ).with_columns(
        has_signal=pl.col("signal_class").is_in(_SIGNAL_CLASSES).cast(pl.Int64),
    )


def resolve_gtfs_stop_id(df: pl.DataFrame, conn: sqlite3.Connection) -> pl.DataFrame:
    """Attach the GTFS stop_id to each row via the shared stop_code key.

    The PRT `stop_id` is an internal identifier (e.g. 'E08092'); downstream tables
    (route_stops, stops) key on the GTFS stop_id, reachable only through stop_code.
    """
    rows = conn.execute("SELECT stop_id, stop_code FROM stops").fetchall()
    xref_df = pl.DataFrame(
        {"stop_id": [str(r[0]) for r in rows], "stop_code": [int(r[1]) for r in rows]},
        schema={"stop_id": pl.Utf8, "stop_code": pl.Int64},
    )
    return df.join(xref_df, on="stop_code", how="left")


def write_to_db(df: pl.DataFrame, conn: sqlite3.Connection) -> int:
    """Drop and rebuild the stop_signals table from the prepared DataFrame."""
    conn.execute("DROP TABLE IF EXISTS stop_signals")
    conn.execute(
        """
        CREATE TABLE stop_signals (
            stop_code     INTEGER PRIMARY KEY,
            stop_id       TEXT,
            prt_stop_id   TEXT NOT NULL,
            stop_name     TEXT,
            prt_mode      TEXT NOT NULL,
            signal_class  TEXT NOT NULL,
            has_signal    INTEGER NOT NULL,
            prt_location  TEXT
        )
        """
    )
    conn.executemany(
        """INSERT OR REPLACE INTO stop_signals
           (stop_code, stop_id, prt_stop_id, stop_name, prt_mode,
            signal_class, has_signal, prt_location)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        df.select(
            "stop_code", "stop_id", "prt_stop_id", "stop_name",
            "prt_mode", "signal_class", "has_signal", "prt_location",
        ).iter_rows(),
    )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM stop_signals").fetchone()[0]


def main() -> None:
    """Run the stop-signal ingestion ETL."""
    if not SOURCE_XLSX.exists():
        raise FileNotFoundError(f"Source spreadsheet not found at {SOURCE_XLSX}")
    df = load_source()
    conn = sqlite3.connect(DB_PATH)
    try:
        df = resolve_gtfs_stop_id(df, conn)
        n = write_to_db(df, conn)
    finally:
        conn.close()
    matched = df.filter(pl.col("stop_id").is_not_null()).height
    print(f"  Loaded {df.height} PRT stops; {matched} matched to a GTFS stop_id.")
    print(f"  Wrote {n} rows to stop_signals in {DB_PATH}")
    print("  signal_class counts:")
    for row in df.group_by("signal_class").len().sort("len", descending=True).iter_rows():
        print(f"    {row[1]:6d}  {row[0]}")


if __name__ == "__main__":
    main()
