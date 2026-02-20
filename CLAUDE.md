- When creating a new directory, add a small README.md file, 2-3 sentences in length, describing the purpose of the directory.
- Add 1-2 sentence docstrings at the top of every python file, describing their purpose.

## Analysis conventions
- Each analysis lives in its own numbered directory under `analyses/` (e.g., `analyses/01_system_trend/`).
- Every analysis directory must contain: `README.md`, `METHODS.md`, `FINDINGS.md`, `main.py`, and an `output/` subdirectory.
- Write `METHODS.md` before writing code. It must have four sections: Question, Approach, Data, Output.
- `main.py` is the sole entry point. It must be runnable standalone via `uv run python analyses/NN_name/main.py`.
- Use `prt_otp_analysis.common.get_db()` for database access. Do not hardcode paths to `prt.db`.
- Generated artifacts (charts, CSVs) go in the analysis's `output/` directory, never in `data/`.
- Analyses must be independent -- never import from or depend on another analysis.
- See `CONTRIBUTING.md` for the full conventions.
- When updating an analysis, be sure to update the corresponding local FINDINGS.md and METHODS.md, if applicable.
    - If the local FINDINGS.md is modified, be sure to modify the root-level FINDINGS.md as well

## Scaffolding tool (`scaffold.py`)
- Always use `--json` for machine-readable output. Parse the result to confirm file paths and names.
- Use `--dry-run` to preview what will be created before writing files.
- **New project:** `uv run python scaffold.py scaffold <target-dir> --name <name> --package <pkg> --db <db_filename> --json`
  - Creates the full project structure (pyproject.toml, src/, tests/, analyses/, docs/, etc.)
  - Config values can also be set via `--config path/to/scaffold.toml`
- **New analysis:** `uv run python scaffold.py add <name> --json`
  - Auto-numbers from the highest existing analysis (e.g., `add my_topic` → `19_my_topic`)
  - Use `--title "Custom Title"` and `--summary "Brief description"` to fill in README.md directly
- **Update index:** `uv run python scaffold.py index --json`
- **Run all analyses:** `uv run python scaffold.py run-all --json`