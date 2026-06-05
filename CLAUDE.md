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

## Interpreting results
- **Surprising findings are a data quality signal first, a discovery second.** When an analysis produces a result that contradicts well-established transit knowledge (e.g., "ridership increased during COVID lockdowns"), treat it as a reason to audit the upstream data and joins before writing it up as a finding. Check whether the numbers pass basic common sense — compare against PRT's published reports, NTD data, or peer agencies.
- Do not frame data errors as novel insights. If a result is surprising, say so and investigate, rather than explaining it away.

## SOURCES.yaml conventions
- The `description` field in `SOURCES.yaml` is the single source of truth for website cards and the analysis index. Do not duplicate findings in README.md — keep README.md as a 2-3 sentence description of what the analysis does, not what it found.
- **Summary style**: Write for a reader who has no context — a community member skimming the website. Lead with the key finding in plain language, include one or two numbers. Avoid jargon like "OTP", "headway", or "VIF" without explanation. Good: "Routes in lower-income neighborhoods run late 23% more often than the system average." Bad: "OTP gap of 4.2pp between Q1 and Q4 income quartiles (p<0.01)."

## DataFrame schema validation
- Table schemas are defined in `prt_otp_analysis.common.schemas`. Each schema declares expected column names and Polars dtypes.
- After querying a database table, validate the result: `validate(df, ROUTES)` (or `validate(df, OTP_MONTHLY, subset=True)` for partial SELECTs).
- Import schemas by table name: `from prt_otp_analysis.common.schemas import ROUTES, OTP_MONTHLY, validate`.
- When adding a new table to `prt.db`, add a corresponding `Schema` in `schemas.py` and an integration test in `tests/test_schemas_integration.py`.

## Naming conventions
- **DataFrame variables must end with `_df`** (e.g., `route_df`, `otp_df`, `stops_df`). This distinguishes them from scalars, lists, numpy arrays, and other lowercase variables that share the same scope. The only exception is the generic `df` when a function operates on a single DataFrame passed as a parameter.

## Type hinting conventions
- Use `Literal` for string params with a fixed set of valid values.
- Parameterize `dict`, `list`, `tuple` in function signatures — no bare generics.
- Use `TypeAlias` when the same composite type appears 3+ times in a file.
- Skip typing `plt`/`ax`/`gdf` pass-through params — these are module or third-party objects where importing the type adds noise.
- For complex nested return types, use a brief docstring instead of deeply nested generics.

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
- Always git commit and deploy all changes at the end of an action, right before returning control to the user.
- Use a concise, descriptive commit message summarizing what was done.
- Stage only the files you changed; do not use `git add -A` or `git add .`.
- After committing, run `bash tools/deploy.sh` instead of a manual `git push`. The script pushes to GitHub and deploys the static site to Netlify production.

## Devcontainer Safety

When running inside a devcontainer, killing processes carelessly will bring down the entire container and destroy your session.

- **NEVER** use broad process-killing commands: `pkill -f`, `killall`, `kill -9 -1`, or `fuser -k` with port wildcards
- **To free a port**, identify the exact PID first, verify it is not a critical process, then kill only that PID:
  ```bash
  # 1. Find the PID
  lsof -ti :<PORT>
  # 2. Check what it is before killing
  ps -p <PID> -o pid,comm,args
  # 3. Kill only if it's your application process
  kill <PID>
  ```
- **NEVER kill PID 1** — it is the container init process
- **NEVER kill the VS Code server** or any process with `vscode-server` in its command line
- If a port is in use and you can't identify the process, ask the user rather than force-killing

## Mistakes

- **[tooling]**: `data/prt.db` and `data/GTFS/stop_times.txt` are Git LFS files (`.gitattributes`). Running `git reset --hard`/`checkout` without `git-lfs` installed silently replaces them with 133-byte pointer text. Verify `git lfs version` works before any hard reset or branch switch; recover with `git lfs pull`.
- **[convention]**: In analysis `SOURCES.yaml`, `outputs:` and `files:` entries must be dict-format (`- path: x.png` / `kind:` / `description:`), not bare strings. Bare strings pass `yaml` but crash the website build (`products/website/main.py`, `item.get` on a str) and fail `tests/test_website_outputs.py`. The scaffold tool emits dict format; hand-edits sometimes don't. Run `uv run python products/website/main.py` before deploy — it is the deploy gate and `tools/deploy.sh` only pushes the pre-built `output/`.
- **[tooling]**: `scaffold.py index` regenerates the FINDINGS.md analysis-index table row from the scaffold/README summary, overwriting any hand-edited row text. Edit the index row *after* running `index`, not before.