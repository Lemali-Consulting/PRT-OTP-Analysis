"""Research project scaffolding generator.

Documents and generates the analysis framework. Subcommands:
  scaffold <dir>           Create a new project with all framework elements
  add <name>               Add a new analysis directory (auto-numbers if no prefix)
  run-all                  Discover and run all analyses/*/main.py in order
  index                    Auto-generate an analysis index in FINDINGS.md
"""

__version__ = "2.0.0"

import argparse
import json
import re
import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path
from string import Template

# ===========================================================================
# DEFAULT CONFIGURATION — fallback when no scaffold.toml exists
# ===========================================================================

DEFAULT_CONFIG = {
    "name": "my-research-project",
    "package": "my_research_project",
    "description": "Description of your research project",
    "python_requires": ">=3.14",
    "db_filename": "data.db",
    "dependencies": ["polars>=1.38.1", "matplotlib>=3.10", "scipy>=1.14"],
    "env": {
        "DB_PATH": "Optional override for the database path",
        "LOG_LEVEL": "DEBUG, INFO, WARNING, ERROR (default: INFO)",
    },
    "red_team_categories": [
        "A. Unit of Analysis",
        "B. Stratification",
        "C. Statistical Testing",
        "D. Regression to the Mean",
        "E. Composition and Panel Balance",
        "F. Code-Documentation Consistency",
        "G. Joins and Filters",
        "H. Numerical and Implementation Correctness",
    ],
}


def load_config(path=None):
    """Read scaffold.toml and merge with defaults. Returns a flat config dict."""
    cfg = DEFAULT_CONFIG.copy()
    if path and path.exists():
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        # Flatten nested TOML tables into the flat config
        if "project" in raw:
            for k, v in raw["project"].items():
                cfg[k] = v
        if "env" in raw:
            cfg["env"] = raw["env"]
        if "red_team" in raw:
            if "categories" in raw["red_team"]:
                cfg["red_team_categories"] = raw["red_team"]["categories"]
    return cfg


# ===========================================================================
# TEMPLATE RENDER FUNCTIONS — each takes a config dict, returns a string
# ===========================================================================


def render_pyproject_toml(cfg):
    """Render pyproject.toml content."""
    return f"""\
[project]
name = "{cfg['name']}"
version = "0.1.0"
description = "{cfg['description']}"
requires-python = "{cfg['python_requires']}"
dependencies = {cfg['dependencies']!r}

[dependency-groups]
dev = [
    "ruff>=0.9",
    "pytest>=8.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{cfg['package']}"]
"""


def render_claude_md(cfg):
    """Render CLAUDE.md content."""
    return f"""\
- When creating a new directory, add a small README.md file, 2-3 sentences in length, describing the purpose of the directory.
- Add 1-2 sentence docstrings at the top of every python file, describing their purpose.

## Analysis conventions
- Each analysis lives in its own numbered directory under `analyses/` (e.g., `analyses/01_first_analysis/`).
- Every analysis directory must contain: `README.md`, `METHODS.md`, `FINDINGS.md`, `main.py`, and an `output/` subdirectory.
- Write `METHODS.md` before writing code. It must have four sections: Question, Approach, Data, Output.
- `main.py` is the sole entry point. It must be runnable standalone via `uv run python analyses/NN_name/main.py`.
- Use `{cfg['package']}.common.get_db()` for database access. Do not hardcode paths to the database.
- Generated artifacts (charts, CSVs) go in the analysis's `output/` directory, never in `data/`.
- Analyses must be independent -- never import from or depend on another analysis.
- See `CONTRIBUTING.md` for the full conventions.
- When updating an analysis, be sure to update the corresponding local FINDINGS.md and METHODS.md, if applicable.
    - If the local FINDINGS.md is modified, be sure to modify the root-level FINDINGS.md as well
"""


def render_contributing_md(cfg):
    """Render CONTRIBUTING.md content."""
    return f"""\
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
├── 01_first_analysis/
│   ├── README.md          # 2-3 sentence summary
│   ├── METHODS.md         # What question, what approach, what data, what output
│   ├── FINDINGS.md        # What the analysis found (written after running)
│   ├── main.py            # Entry point (docstring at top)
│   └── output/            # Generated artifacts (charts, CSVs, tables)
│       └── README.md
├── 02_second_analysis/
│   └── ...
└── ...
```

## Adding a New Analysis

Use the scaffolding tool to create the boilerplate:
```bash
uv run python scaffold.py add short_name
```

Or manually create the directory with the standard layout:

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
   - **Data** -- which tables/columns from the database you'll use
   - **Output** -- what files `main.py` will produce in `output/`
4. **Write main.py.** Use `{cfg['package']}.common` for DB access:
   ```python
   from {cfg['package']}.common import get_db, output_dir
   ```
   The script should be runnable standalone:
   ```bash
   uv run python analyses/NN_short_name/main.py
   ```
5. **Write FINDINGS.md after running the analysis.** Summarize the key results: what the data showed, notable numbers, and any caveats or limitations.
6. **Generated output goes in `output/`.** Charts (`.png`), summary data (`.csv`), printed tables -- all in the `output/` subdirectory. Never commit large binary files; `.gitignore` them if needed.

## Running Analyses

Run a single analysis:
```bash
uv run python analyses/NN_short_name/main.py
```

Run all analyses in order:
```bash
uv run python scaffold.py run-all
```

## Numbering

Numbers indicate suggested reading order, not dependency. Analysis `03` does not depend on `01` having been run. The numbering simply communicates: "if you're new here, read them in this order to build up context."

## Shared Utilities

Common code lives in `src/{cfg['package']}/common.py`:
- `get_db()` -- returns a read-only SQLite connection to the database
- `output_dir(path)` -- returns the `output/` directory for an analysis, creating it if needed
- `query_to_polars(sql)` -- run a SQL query and get a polars DataFrame
- `setup_plotting()` -- configure matplotlib defaults and return plt
- `DB_PATH`, `DATA_DIR`, `PROJECT_ROOT` -- path constants

If you find yourself writing the same helper in multiple analyses, move it to `common.py`.

## File Conventions

- Every `.py` file gets a 1-2 sentence docstring at the top.
- Every new directory gets a 2-3 sentence `README.md`.
- See `CLAUDE.md` for the full set of project conventions.
"""


def render_common_py(cfg):
    """Render common.py content using string.Template to avoid brace conflicts."""
    return Template("""\
\"\"\"Shared utilities for analysis scripts: DB access, paths, and constants.\"\"\"

import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "$db_filename"


def get_db() -> sqlite3.Connection:
    \"\"\"Return a read-only connection to the project database.\"\"\"
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Place your database in data/ or run the build script first."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def output_dir(analysis_dir: str | Path) -> Path:
    \"\"\"Return the output/ directory for a given analysis, creating it if needed.\"\"\"
    out = Path(analysis_dir) / "output"
    out.mkdir(parents=True, exist_ok=True)
    return out


def query_to_polars(sql: str, params: tuple = ()) -> pl.DataFrame:
    \"\"\"Execute a SQL query and return results as a polars DataFrame.\"\"\"
    conn = get_db()
    try:
        rows = conn.execute(sql, params).fetchall()
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame([dict(row) for row in rows])
    finally:
        conn.close()


def setup_plotting():
    \"\"\"Configure matplotlib defaults for consistent chart styling and return plt.\"\"\"
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
""").substitute(db_filename=cfg["db_filename"])


def render_common_init(cfg):
    """Render __init__.py for the package."""
    return f'"""{cfg["package"]} — shared utilities for analysis scripts."""\n'


def render_root_findings(cfg):
    """Render root-level FINDINGS.md."""
    return """\
# Findings

Summary of results from all analyses.

*(Update this file whenever an individual analysis's FINDINGS.md changes.)*
*(Run `uv run python scaffold.py index` to auto-generate the analysis index below.)*

## Analysis Index

*(No analyses yet. Run `uv run python scaffold.py add first_analysis` to get started.)*
"""


def render_gitignore(cfg):
    """Render .gitignore."""
    return """\
.venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.env
analyses/*/output/*.csv
analyses/*/output/*.png
analyses/*/output/*.html
"""


def render_env_example(cfg):
    """Render .env.example from config."""
    lines = ["# Environment variables for this project.", "# Copy to .env and fill in values.\n"]
    for key, comment in cfg["env"].items():
        lines.append(f"# {key}=  # {comment}")
    lines.append("")
    return "\n".join(lines)


def render_ruff_toml(cfg):
    """Render ruff.toml."""
    return f"""\
line-length = 100

[lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[lint.isort]
known-first-party = ["{cfg['package']}"]
"""


def render_schema_md(cfg):
    """Render data/SCHEMA.md."""
    return f"""\
# Data Schema

Documents the tables and columns in `{cfg['db_filename']}`.

## Tables

### example_table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | ... |
| value | REAL | ... |

## Relationships

- Describe foreign key relationships and join patterns here.

## Notes

- Document any sentinel values (e.g., `"0"` meaning NULL).
- Note any known data quality issues.
- Record the data source and how/when it was loaded.
"""


def render_root_readme(cfg):
    """Render root README.md."""
    return f"""\
# {cfg['name']}

{cfg['description']}

## Quick Start

```bash
uv sync
uv run python analyses/01_first_analysis/main.py
```

## Project Structure

```
├── CLAUDE.md               # AI coding conventions
├── CONTRIBUTING.md          # Analysis conventions and design principles
├── scaffold.py              # Scaffolding tool (add analyses, run-all, index)
├── scaffold.toml            # Project configuration
├── FINDINGS.md              # Aggregated results from all analyses
├── ruff.toml                # Linting and formatting config
├── analyses/                # Independent, numbered analyses
│   └── NN_name/
│       ├── README.md
│       ├── METHODS.md
│       ├── FINDINGS.md
│       ├── main.py
│       └── output/
├── data/                    # Source data (database, raw files)
│   └── SCHEMA.md            # Data dictionary
├── docs/
│   └── RED-TEAM.md          # Methodological review protocol
├── RED-TEAM-REPORTS/         # Timestamped review reports
├── src/{cfg['package']}/
│   └── common.py            # Shared utilities
└── tests/                   # Smoke tests and validation
    └── test_smoke.py
```

## Commands

```bash
# Scaffold a new project
uv run python scaffold.py scaffold <target-directory>

# Add a new analysis (auto-numbers)
uv run python scaffold.py add new_topic

# Add with explicit number
uv run python scaffold.py add 07_new_topic

# Run all analyses in order
uv run python scaffold.py run-all

# Regenerate the analysis index in FINDINGS.md
uv run python scaffold.py index

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Conventions

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details. The short version:

- Each analysis is **independent** and runnable via `uv run python analyses/NN_name/main.py`
- Write **METHODS.md before code**, FINDINGS.md after running
- Red-team reviews follow `docs/RED-TEAM.md` — report only, no code changes until human approval
"""


def render_analysis_readme(number, title, summary):
    """Render an analysis README.md."""
    return f"""\
# {number} - {title}

{summary}
"""


def render_analysis_methods(title):
    """Render an analysis METHODS.md."""
    return f"""\
# Methods: {title}

## Question
What question is this analysis trying to answer?

## Approach
- Step-by-step description of the analytical approach.
- Statistical methods, groupings, and transformations used.

## Data
- Which tables/columns from the database are used.
- Any filters or inclusion criteria.

## Output
- `output/artifact_name.csv` -- description
- `output/artifact_name.png` -- description
"""


def render_analysis_findings(title):
    """Render an analysis FINDINGS.md."""
    return f"""\
# Findings: {title}

## Summary
Brief summary of results.

## Key Numbers
- Headline statistics here.

## Observations
- Detailed observations from the analysis.

## Caveats
- Limitations and caveats of this analysis.
"""


def render_analysis_main(number, title, package):
    """Render an analysis main.py with correct output_dir usage."""
    return Template("""\
\"\"\"Analysis $number: $title.\"\"\"

from pathlib import Path

from $package.common import get_db, output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def main():
    # TODO: implement analysis
    pass


if __name__ == "__main__":
    main()
""").substitute(number=number, title=title, package=package)


def render_analysis_output_readme():
    """Render an analysis output/README.md."""
    return """\
# Output

Generated artifacts for this analysis. Contents are gitignored; rerun main.py to regenerate.
"""


def render_test_smoke(cfg):
    """Render tests/test_smoke.py using string.Template."""
    return Template("""\
\"\"\"Smoke tests: verify each analysis imports without error and shared utilities work.\"\"\"

import importlib
import importlib.util
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"


def _find_analyses() -> list[Path]:
    \"\"\"Discover all analysis main.py files.\"\"\"
    return sorted(ANALYSES_DIR.glob("*/main.py"))


class TestCommon:
    \"\"\"Tests for shared utilities in $package.common.\"\"\"

    def test_import_common(self):
        \"\"\"common.py should import without error.\"\"\"
        mod = importlib.import_module("$package.common")
        assert hasattr(mod, "get_db")
        assert hasattr(mod, "output_dir")
        assert hasattr(mod, "query_to_polars")
        assert hasattr(mod, "setup_plotting")

    def test_project_root_exists(self):
        \"\"\"PROJECT_ROOT should point to a real directory.\"\"\"
        from $package.common import PROJECT_ROOT
        assert PROJECT_ROOT.is_dir()

    def test_output_dir_creates(self, tmp_path):
        \"\"\"output_dir should create the directory if it doesn't exist.\"\"\"
        from $package.common import output_dir
        out = output_dir(tmp_path / "fake_analysis")
        assert out.is_dir()
        assert out.name == "output"


class TestAnalysesImport:
    \"\"\"Verify each analysis's main.py can be imported without side effects.\"\"\"

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_analysis_imports(self, main_py: Path):
        \"\"\"Each analysis main.py should import without crashing.\"\"\"
        spec = importlib.util.spec_from_file_location(
            f"analysis_{main_py.parent.name}", main_py
        )
        assert spec is not None, f"Could not load spec for {main_py}"
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            pytest.fail(f"{main_py.parent.name}/main.py failed to import: {exc}")


class TestAnalysesStructure:
    \"\"\"Verify each analysis directory has all required files.\"\"\"

    REQUIRED_FILES = ["README.md", "METHODS.md", "FINDINGS.md", "main.py"]

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_required_files_exist(self, main_py: Path):
        \"\"\"Each analysis must have README.md, METHODS.md, FINDINGS.md, main.py.\"\"\"
        analysis_dir = main_py.parent
        for filename in self.REQUIRED_FILES:
            assert (analysis_dir / filename).exists(), (
                f"{analysis_dir.name} missing {filename}"
            )

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_output_dir_exists(self, main_py: Path):
        \"\"\"Each analysis must have an output/ subdirectory.\"\"\"
        assert (main_py.parent / "output").is_dir(), (
            f"{main_py.parent.name} missing output/ directory"
        )

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_methods_has_four_sections(self, main_py: Path):
        \"\"\"METHODS.md must have Question, Approach, Data, Output sections.\"\"\"
        methods = (main_py.parent / "METHODS.md").read_text(encoding="utf-8")
        for section in ["## Question", "## Approach", "## Data", "## Output"]:
            assert section in methods, (
                f"{main_py.parent.name}/METHODS.md missing '{section}'"
            )
""").substitute(package=cfg["package"])


def render_conftest(cfg):
    """Render tests/conftest.py using string.Template."""
    return Template("""\
\"\"\"Shared pytest configuration.\"\"\"

import sys
from pathlib import Path

# Ensure the source package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
""").substitute()


def render_scaffold_toml(cfg):
    """Render scaffold.toml content from the config dict."""
    deps = "\n".join(f'    "{d}",' for d in cfg["dependencies"])
    cats = "\n".join(f'    "{c}",' for c in cfg["red_team_categories"])
    env_lines = "\n".join(f'{k} = "{v}"' for k, v in cfg["env"].items())
    return f"""\
[project]
name = "{cfg['name']}"
package = "{cfg['package']}"
description = "{cfg['description']}"
python_requires = "{cfg['python_requires']}"
db_filename = "{cfg['db_filename']}"
dependencies = [
{deps}
]

[env]
{env_lines}

[red_team]
categories = [
{cats}
]
"""


# ---------------------------------------------------------------------------
# Red-team protocol rendering
# ---------------------------------------------------------------------------

# Default checklist items per category
_RED_TEAM_ITEMS = {
    "A. Unit of Analysis": [
        "Is the unit of observation in the code consistent with what METHODS.md describes?",
        "Are correlations or regressions computed at the correct unit?",
        "Are observations independent at the stated unit, or is there clustering/nesting that is unaccounted for?",
    ],
    "B. Stratification": [
        "Are distinct subgroups pooled together? If so, is there a stratified check to rule out Simpson's paradox?",
        "If pooled results are the headline, is there justification for pooling?",
    ],
    "C. Statistical Testing": [
        "Do claims of group differences have a formal test (t-test, Kruskal-Wallis, etc.)?",
        "Do correlations report p-values or confidence intervals?",
        "Are multiple comparisons accounted for when many tests are run?",
    ],
    "D. Regression to the Mean": [
        "Do before/after or baseline-vs-change comparisons test for RTM?",
    ],
    "E. Composition and Panel Balance": [
        "Does the set of entities change across time periods? If so, is the analysis restricted to a balanced panel or does it document the impact?",
        "Are time periods balanced (same number of observations per group)?",
        "Are there minimum-observation filters?",
    ],
    "F. Code-Documentation Consistency": [
        "Does the code implement what METHODS.md says?",
        "Do chart labels, titles, and legends match what the code actually computed?",
        "Does FINDINGS.md accurately reflect the current output?",
    ],
    "G. Joins and Filters": [
        "Do SQL JOINs match the intended relationships?",
        "Are NULL, zero, or sentinel values in filter columns handled?",
        "Are WHERE/HAVING clauses consistent with the stated inclusion criteria?",
    ],
    "H. Numerical and Implementation Correctness": [
        "Are there division-by-zero, NaN propagation, or empty-group edge cases?",
        "Are rolling windows, lags, or shifts correctly parameterized?",
        "For matrix operations, are numerically stable methods used?",
    ],
}


def _build_red_team_checklist(categories):
    """Build the checklist section from category list."""
    lines = []
    for cat in categories:
        lines.append(f"### {cat}\n")
        items = _RED_TEAM_ITEMS.get(cat, ["TODO: Add checklist items for this category."])
        for item in items:
            lines.append(f"- [ ] {item}")
        lines.append("")
    return "\n".join(lines)


def render_red_team_md(cfg):
    """Render docs/RED-TEAM.md."""
    checklist = _build_red_team_checklist(cfg["red_team_categories"])
    return f"""\
# Red-Team Protocol

## Scope

Review the specified analysis (or analyses) against the checklist below. **Report only — do not modify any code or files.** Output a structured report of findings for human review.

## Rules

1. **Only flag issues that fall into a checklist category below.** Do not invent novel methodological objections outside these categories.
2. **Every finding must cite the specific file, line(s), and code or query** that exhibits the issue. If you cannot point to concrete evidence, do not report it.
3. **Classify severity honestly:**
   - **Significant** — could change the direction or statistical significance of a finding.
   - **Moderate** — affects magnitude, precision, or reproducibility but not direction.
   - **Low** — cosmetic, documentation-only, or inherent to the data with no available fix.
4. **Do not fix anything.** The report is the deliverable. Fixes happen only after human review and approval.
5. **Do not re-check issues already documented** in existing RED-TEAM-REPORTS/ files for the same analysis.

## Checklist

{checklist}\

## Report Format

Post results in `RED-TEAM-REPORTS/`, named `YYYY-MM-DD-analysis-NN-short-name.md`, using this structure:

```markdown
# Red-Team Report: Analysis NN — Name

**Date:** YYYY-MM-DD
**Reviewer:** [human or model]
**Status:** Report only — no code changes made

## Findings

| # | Category | Severity | File:Line | Issue | Evidence | Suggested Fix |
|---|----------|----------|-----------|-------|----------|---------------|
| 1 | A | Significant | main.py:45 | ... | ... | ... |

## No Issues Found

List checklist categories that were checked and passed cleanly.

## Out of Scope

Note anything suspicious that does not fit a checklist category.
These are suggestions only and should not be acted on without human review.
```

## After Fixes Are Applied

Once a human has reviewed the report and approved fixes:

1. Apply the approved fixes and rerun the analysis.
2. Update the analysis's `FINDINGS.md` and `METHODS.md` if findings or methodology changed.
3. If `FINDINGS.md` changed, update the root-level `FINDINGS.md` as well.
4. Add a `## Review History` entry at the bottom of the analysis's `FINDINGS.md`:
   ```markdown
   ## Review History

   - YYYY-MM-DD: [RED-TEAM-REPORTS/filename.md](../../RED-TEAM-REPORTS/filename.md) — N issues (M significant). Brief summary of changes.
   ```
"""


# Static templates that don't depend on config
ANALYSES_README = """\
# Analyses

Independent, numbered analyses. Each is self-contained and runnable standalone. \
Numbers indicate suggested reading order, not dependency.
"""

DATA_README_TEMPLATE = """\
# Data

Source data for analyses. Place your database and raw data files here. \
See [SCHEMA.md](SCHEMA.md) for the data dictionary. \
Generated artifacts belong in each analysis's `output/` directory, not here.
"""

DOCS_README = """\
# Docs

Project documentation, protocols, and reference materials.
"""

RED_TEAM_REPORTS_README = """\
# Red-Team Reports

Timestamped reports from methodological reviews. Each report documents issues found, \
severity classifications, and suggested fixes for human review.
"""

TESTS_README = """\
# Tests

Smoke tests and validation for shared utilities and analyses. Run with `uv run pytest`.
"""

TESTS_INIT = """\
\"\"\"Test suite for the project.\"\"\"
"""


# ===========================================================================
# HELPERS
# ===========================================================================


def _write_file(path, content):
    """Write a file, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


def _next_analysis_number(analyses_dir):
    """Scan analyses/ for the highest NN_ prefix and return N+1, zero-padded."""
    existing = []
    if analyses_dir.is_dir():
        for d in analyses_dir.iterdir():
            m = re.match(r"^(\d{2,})_", d.name)
            if m:
                existing.append(int(m.group(1)))
    if existing:
        return max(existing) + 1
    return 1


def _emit(result, use_json):
    """Print result as JSON or human-readable text."""
    if use_json:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output is handled inline in each command
        pass


# ===========================================================================
# COMMANDS
# ===========================================================================


def cmd_scaffold(args):
    """Generate the full project scaffolding at the given root directory."""
    root = Path(args.target).resolve()
    use_json = getattr(args, "json", False)
    dry_run = getattr(args, "dry_run", False)

    if not dry_run and root.exists() and any(root.iterdir()):
        msg = f"ERROR: {root} already exists and is not empty. Aborting."
        if use_json:
            print(json.dumps({"command": "scaffold", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    # Build config: defaults → TOML → CLI args
    config_path = Path(args.config) if args.config else None
    cfg = load_config(config_path)
    if args.name:
        cfg["name"] = args.name
    if args.package:
        cfg["package"] = args.package
    if args.description:
        cfg["description"] = args.description
    if args.db:
        cfg["db_filename"] = args.db

    files_to_write = {
        "pyproject.toml": render_pyproject_toml(cfg),
        "CLAUDE.md": render_claude_md(cfg),
        "CONTRIBUTING.md": render_contributing_md(cfg),
        "FINDINGS.md": render_root_findings(cfg),
        ".gitignore": render_gitignore(cfg),
        ".env.example": render_env_example(cfg),
        "README.md": render_root_readme(cfg),
        "ruff.toml": render_ruff_toml(cfg),
        "scaffold.toml": render_scaffold_toml(cfg),
        "scaffold.py": Path(__file__).read_text(encoding="utf-8"),
        f"src/{cfg['package']}/__init__.py": render_common_init(cfg),
        f"src/{cfg['package']}/common.py": render_common_py(cfg),
        "data/README.md": DATA_README_TEMPLATE,
        "data/SCHEMA.md": render_schema_md(cfg),
        "docs/README.md": DOCS_README,
        "docs/RED-TEAM.md": render_red_team_md(cfg),
        "RED-TEAM-REPORTS/README.md": RED_TEAM_REPORTS_README,
        "analyses/README.md": ANALYSES_README,
        "tests/README.md": TESTS_README,
        "tests/__init__.py": TESTS_INIT,
        "tests/conftest.py": render_conftest(cfg),
        "tests/test_smoke.py": render_test_smoke(cfg),
    }

    if dry_run:
        result = {
            "command": "scaffold",
            "dry_run": True,
            "target": str(root),
            "files": sorted(files_to_write.keys()),
            "config": {k: v for k, v in cfg.items() if k != "env"},
        }
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Dry run: would scaffold project at {root}\n")
            print(f"Config: name={cfg['name']}, package={cfg['package']}, db={cfg['db_filename']}")
            print(f"\nWould create {len(files_to_write)} files:")
            for f in sorted(files_to_write.keys()):
                print(f"  {f}")
        return result

    root.mkdir(parents=True, exist_ok=True)
    created = []

    if not use_json:
        print(f"Scaffolding project at {root}...\n")

    for relpath, content in files_to_write.items():
        full_path = root / relpath
        _write_file(full_path, content)
        created.append(relpath)
        if not use_json:
            print(f"  created {relpath}")

    result = {
        "command": "scaffold",
        "target": str(root),
        "files_created": created,
        "config": {
            "name": cfg["name"],
            "package": cfg["package"],
            "db_filename": cfg["db_filename"],
        },
    }

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\nDone. Next steps:")
        print(f"  cd {root}")
        print(f"  git init && uv sync")
        print(f"  cp .env.example .env  # and fill in values")
        print(f"  # Place your database at data/{cfg['db_filename']}")
        print(f"  # Edit data/SCHEMA.md to document your tables")
        print(f"  uv run python scaffold.py add first_analysis")

    return result


def cmd_add(args):
    """Add a new analysis directory with all boilerplate files."""
    name = args.name
    use_json = getattr(args, "json", False)
    dry_run = getattr(args, "dry_run", False)

    # Determine project root (where analyses/ lives)
    root = Path.cwd()
    analyses_dir = root / "analyses"
    if not analyses_dir.is_dir():
        msg = f"ERROR: No analyses/ directory found in {root}. Run this command from the project root."
        if use_json:
            print(json.dumps({"command": "add", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    # Load config from scaffold.toml
    cfg = load_config(root / "scaffold.toml")

    # Auto-numbering: if name doesn't start with NN_, prepend the next number
    if re.match(r"^\d{2,}_\w+$", name):
        # Explicit number provided
        pass
    elif re.match(r"^\w+$", name):
        # Auto-number
        next_num = _next_analysis_number(analyses_dir)
        name = f"{next_num:02d}_{name}"
    else:
        msg = f"ERROR: Analysis name must be a valid identifier (e.g., my_topic or 07_my_topic). Got: {name}"
        if use_json:
            print(json.dumps({"command": "add", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    analysis_dir = analyses_dir / name
    if analysis_dir.exists():
        msg = f"ERROR: {analysis_dir} already exists."
        if use_json:
            print(json.dumps({"command": "add", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    # Extract number and title
    m = re.match(r"^(\d{2,})_(.*)", name)
    number = m.group(1)
    title_slug = m.group(2)
    title = getattr(args, "title", None) or title_slug.replace("_", " ").title()
    summary = getattr(args, "summary", None) or "TODO: describe this analysis."

    files_to_write = {
        "README.md": render_analysis_readme(number, title, summary),
        "METHODS.md": render_analysis_methods(title),
        "FINDINGS.md": render_analysis_findings(title),
        "main.py": render_analysis_main(number, title, cfg["package"]),
        "output/README.md": render_analysis_output_readme(),
    }

    if dry_run:
        result = {
            "command": "add",
            "dry_run": True,
            "name": name,
            "path": str(analysis_dir),
            "title": title,
            "summary": summary,
            "files": sorted(files_to_write.keys()),
        }
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Dry run: would create analysis {name}\n")
            print(f"  Title: {title}")
            print(f"  Summary: {summary}")
            print(f"\nWould create {len(files_to_write)} files in analyses/{name}/:")
            for f in sorted(files_to_write.keys()):
                print(f"  {f}")
        return result

    created = []
    if not use_json:
        print(f"Creating analysis {name}...\n")

    for relpath, content in files_to_write.items():
        full_path = analysis_dir / relpath
        _write_file(full_path, content)
        created.append(relpath)
        if not use_json:
            print(f"  created analyses/{name}/{relpath}")

    result = {
        "command": "add",
        "name": name,
        "path": str(analysis_dir),
        "title": title,
        "summary": summary,
        "files_created": created,
    }

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\nDone. Next steps:")
        print(f"  1. Edit analyses/{name}/METHODS.md (write this before code)")
        print(f"  2. Implement analyses/{name}/main.py")
        print(f"  3. Run: uv run python analyses/{name}/main.py")
        print(f"  4. Write analyses/{name}/FINDINGS.md with results")
        print(f"  5. Run: uv run python scaffold.py index  (to update the index)")

    return result


def cmd_run_all(args):
    """Discover and run all analyses/*/main.py in numerical order."""
    root = Path.cwd()
    analyses_dir = root / "analyses"
    use_json = getattr(args, "json", False)
    dry_run = getattr(args, "dry_run", False)

    if not analyses_dir.is_dir():
        msg = f"ERROR: No analyses/ directory found in {root}."
        if use_json:
            print(json.dumps({"command": "run-all", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    main_files = sorted(analyses_dir.glob("*/main.py"))
    if not main_files:
        result = {"command": "run-all", "results": [], "passed": 0, "total": 0}
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print("No analyses found.")
        return result

    if dry_run:
        names = [mf.parent.name for mf in main_files]
        result = {
            "command": "run-all",
            "dry_run": True,
            "analyses": names,
            "total": len(names),
        }
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Dry run: would run {len(names)} analyses:")
            for n in names:
                print(f"  {n}")
        return result

    if not use_json:
        print(f"Found {len(main_files)} analyses.\n")

    results = []
    for main_py in main_files:
        name = main_py.parent.name
        if not use_json:
            print(f"{'=' * 60}")
            print(f"Running {name}...")
            print(f"{'=' * 60}")

        try:
            kwargs = {"cwd": str(root), "timeout": 300}
            if use_json:
                kwargs["capture_output"] = True
                kwargs["text"] = True
            result = subprocess.run(
                [sys.executable, str(main_py)],
                **kwargs,
            )
            status = "PASS" if result.returncode == 0 else f"FAIL (exit {result.returncode})"
            entry = {"name": name, "status": status, "returncode": result.returncode}
            if use_json:
                entry["stdout"] = result.stdout
                entry["stderr"] = result.stderr
        except subprocess.TimeoutExpired:
            status = "FAIL (timeout)"
            entry = {"name": name, "status": status, "returncode": -1}
        except Exception as exc:
            status = f"FAIL ({exc})"
            entry = {"name": name, "status": status, "returncode": -1}

        results.append(entry)
        if not use_json:
            print()

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)

    output = {
        "command": "run-all",
        "results": results,
        "passed": passed,
        "total": total,
    }

    if use_json:
        print(json.dumps(output, indent=2))
    else:
        print(f"{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        for r in results:
            icon = "+" if r["status"] == "PASS" else "-"
            print(f"  [{icon}] {r['name']}: {r['status']}")
        print(f"\n{passed}/{total} passed.")

    if passed < total:
        sys.exit(1)

    return output


def cmd_index(args):
    """Auto-generate an analysis index from analyses/*/README.md."""
    root = Path.cwd()
    analyses_dir = root / "analyses"
    findings_path = root / "FINDINGS.md"
    use_json = getattr(args, "json", False)
    dry_run = getattr(args, "dry_run", False)

    if not analyses_dir.is_dir():
        msg = f"ERROR: No analyses/ directory found in {root}."
        if use_json:
            print(json.dumps({"command": "index", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    if not findings_path.exists():
        msg = f"ERROR: No FINDINGS.md found in {root}."
        if use_json:
            print(json.dumps({"command": "index", "error": msg}))
        else:
            print(msg)
        sys.exit(1)

    # Discover analyses (supports 2+ digit numbers)
    analysis_dirs = sorted(
        [d for d in analyses_dir.iterdir() if d.is_dir() and re.match(r"^\d{2,}_", d.name)]
    )

    if not analysis_dirs:
        result = {"command": "index", "analyses": [], "total": 0}
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print("No analyses found.")
        return result

    # Build index
    entries = []
    index_lines = ["## Analysis Index\n"]
    index_lines.append("| # | Name | Summary |")
    index_lines.append("|---|------|---------|")

    for d in analysis_dirs:
        m = re.match(r"^(\d{2,})_(.*)", d.name)
        number = m.group(1)
        title_slug = m.group(2)
        readme = d / "README.md"
        if readme.exists():
            text = readme.read_text(encoding="utf-8").strip()
            summary = ""
            for line in text.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    summary = line
                    break
        else:
            summary = "*(no README.md)*"

        title = title_slug.replace("_", " ").title()
        index_lines.append(f"| {number} | [{title}](analyses/{d.name}/) | {summary} |")
        entries.append({"number": number, "name": d.name, "title": title, "summary": summary})

    index_block = "\n".join(index_lines) + "\n"

    if dry_run:
        result = {
            "command": "index",
            "dry_run": True,
            "analyses": entries,
            "total": len(entries),
            "index_block": index_block,
        }
        if use_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Dry run: would update FINDINGS.md with {len(entries)} analyses:")
            for e in entries:
                print(f"  {e['number']}. {e['title']}: {e['summary']}")
        return result

    # Replace existing index block in FINDINGS.md
    content = findings_path.read_text(encoding="utf-8")
    pattern = r"## Analysis Index\n.*?(?=\n## (?!Analysis Index)|\Z)"
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, index_block.rstrip(), content, flags=re.DOTALL)
    else:
        new_content = content.rstrip() + "\n\n" + index_block

    findings_path.write_text(new_content, encoding="utf-8")

    result = {
        "command": "index",
        "analyses": entries,
        "total": len(entries),
        "updated": str(findings_path),
    }

    if use_json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Updated {findings_path} with {len(entries)} analyses.")

    return result


# ===========================================================================
# CLI
# ===========================================================================


def main():
    """Parse arguments and dispatch to the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Research project scaffolding and management tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s scaffold ../my-new-project   Create a new project
              %(prog)s add new_topic                 Add an analysis (auto-numbered)
              %(prog)s add 07_new_topic              Add with explicit number
              %(prog)s run-all                       Run all analyses in order
              %(prog)s index                         Regenerate the analysis index
              %(prog)s scaffold /tmp/test --json --dry-run   Preview as JSON
        """),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Shared flags added to each subparser so they can appear before or after subcommand
    _common = argparse.ArgumentParser(add_help=False)
    _common.add_argument(
        "--json", action="store_true", default=False,
        help="Output results as JSON instead of human-readable text",
    )
    _common.add_argument(
        "--dry-run", action="store_true", default=False,
        help="Show what would be done without writing any files or running anything",
    )

    # scaffold
    p_scaffold = subparsers.add_parser(
        "scaffold", parents=[_common], help="Create a new project with all framework elements"
    )
    p_scaffold.add_argument("target", help="Target directory for the new project")
    p_scaffold.add_argument("--config", default=None, help="Path to scaffold.toml config file")
    p_scaffold.add_argument("--name", default=None, help="Project name (overrides config)")
    p_scaffold.add_argument("--package", default=None, help="Python package name (overrides config)")
    p_scaffold.add_argument("--description", default=None, help="Project description (overrides config)")
    p_scaffold.add_argument("--db", default=None, help="Database filename (overrides config)")
    p_scaffold.set_defaults(func=cmd_scaffold)

    # add
    p_add = subparsers.add_parser(
        "add", parents=[_common], help="Add a new analysis directory with boilerplate"
    )
    p_add.add_argument(
        "name",
        help="Analysis name (e.g., my_topic for auto-numbering, or 07_my_topic for explicit)",
    )
    p_add.add_argument("--title", default=None, help="Custom title for the analysis README")
    p_add.add_argument("--summary", default=None, help="Summary for the analysis README (avoids TODO placeholder)")
    p_add.set_defaults(func=cmd_add)

    # run-all
    p_run = subparsers.add_parser(
        "run-all", parents=[_common], help="Run all analyses/*/main.py in numerical order"
    )
    p_run.set_defaults(func=cmd_run_all)

    # index
    p_index = subparsers.add_parser(
        "index", parents=[_common], help="Auto-generate the analysis index in FINDINGS.md"
    )
    p_index.set_defaults(func=cmd_index)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
