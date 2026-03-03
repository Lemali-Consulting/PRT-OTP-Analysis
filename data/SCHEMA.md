# Data Schema

Canonical schema documentation for the project database and source datasets.

The detailed dictionary currently lives in [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md).
Use this file as the scaffold-compatible entrypoint and keep both files aligned.

## Primary Database

- SQLite file: `data/prt.db`
- Build command: `uv run python pipeline/01_data_ingestion/main.py`

## Tables

See [`DATA_DICTIONARY.md`](DATA_DICTIONARY.md) for table-level columns, types, and caveats.
