"""Shared utilities for analysis scripts: DB access, paths, and constants."""

import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"


def get_db() -> sqlite3.Connection:
    """Return a read-only connection to the PRT database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Run `uv run python src/prt_otp_analysis/build_db.py` first."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def output_dir(analysis_dir: str | Path) -> Path:
    """Return the output/ directory for a given analysis, creating it if needed."""
    out = Path(analysis_dir) / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def query_to_polars(sql: str, params: tuple = ()) -> pl.DataFrame:
    """Execute a SQL query against prt.db and return results as a polars DataFrame."""
    conn = get_db()
    try:
        rows = conn.execute(sql, params).fetchall()
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame([dict(row) for row in rows])
    finally:
        conn.close()


def setup_plotting():
    """Configure matplotlib defaults for consistent chart styling and return plt."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
    })
    return plt


def classify_bus_route(route_id: str) -> str:
    """Classify a bus route_id as local, limited, express, busway, or flyer."""
    if route_id.endswith("L"):
        return "limited"
    if route_id.endswith("X"):
        return "express"
    if route_id.startswith(("P", "G")):
        return "busway"
    if route_id.startswith("O"):
        return "flyer"
    return "local"
