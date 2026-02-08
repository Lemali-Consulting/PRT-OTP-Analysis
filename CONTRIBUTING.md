# Contributing: Analysis Conventions

This document describes how analyses are organized in this project and the conventions for adding new ones.

## Design Principles

- **Each analysis is independent.** Any analysis can be run without running any other. This ensures replicability and makes each analysis reviewable on its own.
- **Plain Python over notebooks.** `.py` files are easier to diff, review, and run reproducibly. If interactivity is needed, import from `main.py` into a scratch notebook.
- **Document before you code.** Write `METHODS.md` first. If you can't explain the approach in plain language, the code will be harder to trust.

## Directory Structure

Analyses live under `analyses/`, each in a numbered subdirectory:

```
analyses/
├── README.md
├── 01_system_trend/
│   ├── README.md          # 2-3 sentence summary
│   ├── METHODS.md         # What question, what approach, what data, what output
│   ├── FINDINGS.md        # What the analysis found (written after running)
│   ├── main.py            # Entry point (docstring at top)
│   └── output/            # Generated artifacts (charts, CSVs, tables)
│       └── README.md
├── 02_mode_comparison/
│   └── ...
└── ...
```

## Adding a New Analysis

1. **Pick the next number.** Check the highest existing prefix and increment (e.g., after `05_`, use `06_`).
2. **Create the directory** with the standard layout:
   ```
   analyses/NN_short_name/
   ├── README.md
   ├── METHODS.md
   ├── FINDINGS.md
   ├── main.py
   └── output/
       └── README.md
   ```
3. **Write METHODS.md first.** It should have four sections:
   - **Question** -- what you're trying to answer
   - **Approach** -- how you'll answer it (steps, statistical methods, groupings)
   - **Data** -- which tables/columns from `data/prt.db` you'll use
   - **Output** -- what files `main.py` will produce in `output/`
4. **Write main.py.** Use `prt_otp_analysis.common` for DB access:
   ```python
   from prt_otp_analysis.common import get_db, output_dir
   ```
   The script should be runnable standalone:
   ```bash
   uv run python analyses/NN_short_name/main.py
   ```
5. **Write FINDINGS.md after running the analysis.** Summarize the key results: what the data showed, notable numbers, and any caveats or limitations.
6. **Generated output goes in `output/`.** Charts (`.png`), summary data (`.csv`), printed tables -- all in the `output/` subdirectory. Never commit large binary files; `.gitignore` them if needed.

## Numbering

Numbers indicate suggested reading order, not dependency. Analysis `03` does not depend on `01` having been run. The numbering simply communicates: "if you're new here, read them in this order to build up context."

## Shared Utilities

Common code lives in `src/prt_otp_analysis/common.py`:
- `get_db()` -- returns a read-only SQLite connection to `data/prt.db`
- `output_dir(path)` -- returns the `output/` directory for an analysis, creating it if needed
- `DB_PATH`, `DATA_DIR`, `PROJECT_ROOT` -- path constants

If you find yourself writing the same helper in multiple analyses, move it to `common.py`.

## File Conventions

- Every `.py` file gets a 1-2 sentence docstring at the top.
- Every new directory gets a 2-3 sentence `README.md`.
- See `CLAUDE.md` for the full set of project conventions.
