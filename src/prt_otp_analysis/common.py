"""Shared utilities for analysis scripts: DB access, paths, and constants."""

import sqlite3
from pathlib import Path

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
