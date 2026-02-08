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