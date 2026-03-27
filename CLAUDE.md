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

## Analysis validation checklist
Before writing FINDINGS.md or reporting results, complete every applicable item. Document what was checked in a `## Validation` section at the bottom of FINDINGS.md.

### Data inputs
1. **Data source verified.** Every table or CSV used was checked against `data/SCHEMA.md` or the pipeline step that produces it. No column mapping was written from memory.
2. **Geographic/temporal scope matches.** All datasets in the analysis are filtered to the same time range and route set. If scopes differ, the mismatch is documented and justified.
3. **Null/missing handling.** Confirm that null or zero values are treated appropriately — not silently dropped or counted as real observations.

### Results plausibility
4. **Aggregates sanity-checked.** Key totals and rates were compared against known baselines (e.g., PRT's published OTP targets, NTD ridership reports). Any value outside the expected range was investigated before being written up.
5. **Surprising results investigated.** Any result that contradicts known transit patterns was treated as a data quality signal first. The investigation is documented — either the result was confirmed with an explanation, or the upstream error was identified and fixed.
6. **Direction of effects checked.** Known relationships were verified (e.g., higher frequency routes tend toward lower OTP, ridership dropped during COVID). A reversal is a red flag, not a finding.

### Statistical diagnostics (encode in analysis code)
7. **Multicollinearity checked.** Regression analyses compute and report VIF. Flag any predictor with VIF > 5.
8. **Small-sample routes flagged.** When computing route-level metrics, filter or flag routes below a minimum observation count. Report the threshold used.
9. **Ecological framing in FINDINGS.md.** Route-level or neighborhood-level results are described as area-level associations, never as individual-level claims.

## Error reporting
- When you discover a bug in code, an error in analysis, or make a mistake, report it immediately:
  `uv run python tools/error_report.py add <class> "short title"`
- The tool prints the full path to the created file. Open it and add a description of what went wrong, how it was discovered, and what was done to fix it.
- Before adding a report, run `uv run python tools/error_report.py list` to see existing error classes. Reuse an existing class when appropriate rather than creating a new one.

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

## Commit discipline
- Always git commit and push all changes at the end of an action, right before returning control to the user.
- Use a concise, descriptive commit message summarizing what was done.
- Stage only the files you changed; do not use `git add -A` or `git add .`.
- After committing, push to the remote.