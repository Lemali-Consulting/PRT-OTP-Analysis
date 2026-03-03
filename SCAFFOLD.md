# Scaffolding Guide: Analysis-Pipeline-Website Pattern

This document captures the full architecture of the REVERB PA project so it can be replicated for a new research project. It covers the three-layer pattern — **pipeline** (data ingestion), **analyses** (independent research units), and **website** (static documentation site) — plus all supporting infrastructure.

## Quick Start for a New ProjectDo

```bash
# 1. Scaffold the base project
uv run python scaffold.py scaffold /path/to/new-project \
  --name "my-research-project" \
  --package "my_research" \
  --description "Description of the project" \
  --db "data.db"

# 2. Initialize
cd /path/to/new-project
git init && uv sync
cp .env.example .env

# 3. Place your database at data/data.db, then add analyses
uv run python scaffold.py add first_analysis
```

The `scaffold.py scaffold` command generates ~20 files: `pyproject.toml`, `CLAUDE.md`, `CONTRIBUTING.md`, `FINDINGS.md`, `ruff.toml`, shared utilities, smoke tests, red-team protocol, and directory READMEs. From there you add pipeline steps manually and analyses via `scaffold.py add`.

---

## 1. Project Structure

```
project-root/
├── CLAUDE.md                  # AI coding conventions (canonical instructions)
├── CONTRIBUTING.md            # Analysis conventions and design principles
├── FINDINGS.md                # Aggregated results from all analyses
├── PLAN.md                    # Research plan and roadmap
├── README.md                  # Project overview and quick start
├── scaffold.py                # Scaffolding CLI tool
├── scaffold.toml              # Project configuration (name, package, DB, etc.)
├── pyproject.toml             # Python package config (uv/hatch)
├── ruff.toml                  # Linting config
├── .env.example               # Environment variable template
├── .gitignore
│
├── src/<package>/             # Shared Python package
│   ├── __init__.py
│   └── common.py              # DB access, paths, plotting helpers
│
├── data/                      # Source data
│   ├── SCHEMA.md              # Data dictionary
│   ├── data.db                # Unified SQLite database
│   ├── google-drive/          # Raw files synced from external sources
│   └── scraped/               # Datasets from public APIs
│
├── pipeline/                  # Data ingestion steps (run in order)
│   ├── README.md
│   ├── 01_data_ingestion/
│   ├── 02_census_acs/
│   ├── ...
│   └── NN_step_name/
│       ├── README.md
│       ├── METHODS.md
│       ├── FINDINGS.md
│       ├── SOURCES.yaml        # Data provenance manifest
│       ├── main.py
│       └── output/
│
├── analyses/                  # Independent research analyses
│   ├── README.md
│   ├── 01_first_analysis/
│   ├── 02_second_analysis/
│   ├── ...
│   └── NN_analysis_name/
│       ├── README.md           # 2-3 sentence summary
│       ├── METHODS.md          # Question, Approach, Data, Output
│       ├── FINDINGS.md         # Results (written after running)
│       ├── SOURCES.yaml        # Data provenance manifest
│       ├── main.py             # Sole entry point
│       └── output/             # Generated charts, CSVs
│           └── README.md
│
├── products/                  # Stakeholder delivery surfaces
│   ├── README.md
│   ├── website/               # Static documentation site
│   │   ├── main.py            # Site generator
│   │   ├── generate_manifests.py  # Auto-generates SOURCES.yaml
│   │   ├── glossary.yaml      # Domain glossary
│   │   ├── templates/         # Jinja2 HTML templates
│   │   └── output/            # Generated HTML site
│   ├── reports/               # Synthesis reports
│   └── dashboard/             # Interactive tools (Streamlit, etc.)
│
├── docs/
│   └── RED-TEAM.md            # Methodological review protocol
├── RED-TEAM-REPORTS/          # Timestamped review reports
└── tests/
    ├── conftest.py
    └── test_smoke.py          # Import smoke tests + structure validation
```

---

## 2. Configuration (`scaffold.toml`)

Central config consumed by `scaffold.py`:

```toml
[project]
name = "my-research-project"
package = "my_research"
description = "Description of the project"
python_requires = ">=3.14"
db_filename = "data.db"
dependencies = [
    "polars>=1.38.1",
    "matplotlib>=3.10",
    "scipy>=1.14",
]

[env]
DB_PATH = "Optional override for the database path"
LOG_LEVEL = "DEBUG, INFO, WARNING, ERROR (default: INFO)"

[red_team]
categories = [
    "A. Unit of Analysis",
    "B. Stratification",
    "C. Statistical Testing",
    "D. Regression to the Mean",
    "E. Composition and Panel Balance",
    "F. Code-Documentation Consistency",
    "G. Joins and Filters",
    "H. Numerical and Implementation Correctness",
]
```

---

## 3. Shared Utilities (`src/<package>/common.py`)

Every analysis imports from this module. It provides:

```python
"""Shared utilities for analysis scripts: DB access, paths, and constants."""

import sqlite3
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DRIVE_DATA_DIR = DATA_DIR / "google-drive"
SCRAPED_DATA_DIR = DATA_DIR / "scraped"
DB_PATH = DATA_DIR / "data.db"


def get_db() -> sqlite3.Connection:
    """Return a read-only connection to the project database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Place your database in data/ or run the build script first."
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
    """Execute a SQL query and return results as a polars DataFrame."""
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
```

Key design decisions:
- **Read-only DB connection** — analyses never write to the database; only pipeline steps do.
- **`output_dir()` auto-creates** — no boilerplate `mkdir` in every analysis.
- **`setup_plotting()` returns `plt`** — ensures consistent chart styling project-wide and uses the `Agg` backend for headless rendering.

---

## 4. Pipeline Layer

Pipeline steps live in `pipeline/` and are numbered to indicate execution order. Unlike analyses, **pipeline steps write to the database** and `data/scraped/`.

### Pipeline step structure

```
pipeline/NN_step_name/
├── README.md
├── METHODS.md          # Same 4 sections: Question, Approach, Data, Output
├── FINDINGS.md         # What was fetched, row counts, data quality notes
├── SOURCES.yaml        # Manifest for the website
├── main.py             # Entry point (uses writable DB connection)
└── output/             # Supplementary artifacts (quality checks, catalogs)
```

### Pipeline SOURCES.yaml format

Pipeline manifests declare what they consume (APIs, files) and what they produce (DB tables):

```yaml
kind: pipeline
title: "Public Indicators"
files: []
apis:
  - name: "County Health Rankings"
    url: "https://www.countyhealthrankings.org/..."
    description: Annual county-level health outcome measures.
  - name: "BLS LAUS"
    url: "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    description: Bureau of Labor Statistics unemployment data.
tables: []
tables_produced:
  - name: health_rankings
    description: County Health Rankings measures for target counties.
  - name: bls_unemployment
    description: BLS local area unemployment estimates by county.
```

### Running pipeline

```bash
# Run steps in order
uv run python pipeline/01_data_ingestion/main.py
uv run python pipeline/02_census_acs/main.py
# ... etc.

# Or run everything:
uv run python scaffold.py run-all  # runs pipeline/* then analyses/*
```

---

## 5. Analysis Layer

Analyses are independent research units. Each answers a specific question using data from the pipeline.

### Analysis structure

```
analyses/NN_analysis_name/
├── README.md           # 2-3 sentence summary
├── METHODS.md          # Write BEFORE code
├── FINDINGS.md         # Write AFTER running
├── SOURCES.yaml        # Data provenance manifest
├── main.py             # Sole entry point
└── output/             # Charts (.png), summaries (.csv)
    └── README.md
```

### METHODS.md template (4 required sections)

```markdown
# Methods: Analysis Title

## Question
What question is this analysis trying to answer?

## Approach
1. Step-by-step description of the analytical approach.
2. Statistical methods, groupings, and transformations used.

## Data
- `table_name` (columns used)
- Any filters or inclusion criteria.

## Output
- `output/artifact.csv` -- description
- `output/chart.png` -- description
```

### Analysis SOURCES.yaml format

```yaml
kind: analysis
title: GCM Priority Go-Zone Analysis
group: GCM Analysis          # Used for TOC grouping on website
tables:                       # DB tables consumed (read-only)
  - gcm_statements
  - gcm_ratings
files:                        # Direct file inputs
  - path: data/google-drive/Concept Mapping/Data/file.xlsx
    description: Cluster ratings export
analyses:                     # Cross-analysis references (rare)
  - 03_gcm_clustering
```

### Analysis main.py template

```python
"""Analysis NN: Title."""

from pathlib import Path

from <package>.common import get_db, output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def main():
    # Load data
    df = query_to_polars("SELECT * FROM my_table")

    # Analysis logic...

    # Save CSV output
    df.write_csv(OUT / "results.csv")

    # Save chart
    plt = setup_plotting()
    fig, ax = plt.subplots()
    # ... plotting code ...
    fig.savefig(OUT / "chart.png")
    plt.close(fig)

    print("Analysis NN complete.")


if __name__ == "__main__":
    main()
```

### Key analysis conventions

- **Independence** — never import from another analysis. Use DB tables as the interface.
- **Standalone** — `uv run python analyses/NN_name/main.py` must work.
- **Document first** — write METHODS.md before code.
- **Numbers = reading order**, not dependency.
- **Output images** are auto-discovered by the website generator and displayed on analysis pages.

---

## 6. SOURCES.yaml Auto-Generation

`products/website/generate_manifests.py` can auto-generate SOURCES.yaml by parsing `main.py`:

```bash
uv run python products/website/generate_manifests.py
```

It detects:
- **DB tables** — by finding `query_to_polars("SELECT ... FROM table_name")` and `conn.execute()` patterns.
- **Drive files** — by finding `DRIVE_DATA_DIR / "filename"` references.
- **Cross-analysis refs** — by finding `analyses/NN_name/output/` path patterns.

The generator also assigns **TOC groups** via a `GROUP_MAP` dict that maps analysis numbers to category names. Edit this map when adding new analyses.

---

## 7. Website Layer

The website is a static HTML site generated by `products/website/main.py`. It renders every pipeline step and analysis as its own page with:
- **Data provenance diagram** (Mermaid flowchart showing data lineage)
- **Findings** (rendered from FINDINGS.md)
- **Output images** (auto-discovered from `output/` directories)
- **Methods** (rendered from METHODS.md)
- **Sources table** (listing all upstream data dependencies)

Plus cross-cutting pages:
- **Index** — grouped TOC of all pipeline steps and analyses
- **Sources inventory** — all APIs, files, and DB tables across the project
- **Source detail pages** — per-source lineage showing source -> pipeline -> tables -> analyses
- **Glossary** — domain-specific terms from `glossary.yaml`

### Website dependencies

```
jinja2>=3.1
mistune>=3.0
pyyaml>=6.0
```

Plus the Mermaid JS library loaded via CDN in `base.html`.

### Templates (Jinja2)

Six templates in `products/website/templates/`:

| Template | Purpose |
|----------|---------|
| `base.html` | Shared layout: nav bar, Mermaid init, footer |
| `index.html` | Home page with pipeline + analysis TOC |
| `page.html` | Pipeline step or analysis detail page |
| `sources.html` | Source inventory (APIs, files, DB tables) |
| `source_detail.html` | Per-source lineage and consumer list |
| `glossary.html` | Domain glossary organized by category |

#### `base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Project Research{% endblock %}</title>
  <link rel="stylesheet" href="{{ root }}style.css">
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad: true, theme: 'neutral'});</script>
</head>
<body>
  <nav class="site-nav">
    <a href="{{ root }}index.html" class="nav-brand">Project Research</a>
    <span class="nav-sep">|</span>
    <a href="{{ root }}index.html#pipeline">Pipeline</a>
    <a href="{{ root }}index.html#analyses">Analyses</a>
    <a href="{{ root }}sources.html">Sources</a>
    <a href="{{ root }}glossary.html">Glossary</a>
  </nav>
  <main class="container">
    {% block content %}{% endblock %}
  </main>
  <footer class="site-footer">
    <p>Generated from project documentation.</p>
  </footer>
</body>
</html>
```

#### `page.html` (pipeline step or analysis)

```html
{% extends "base.html" %}
{% block title %}{{ page.title }} - Project{% endblock %}
{% block content %}
<h1>{{ page.title }}</h1>
<span class="badge badge-{{ page.kind }}">{{ page.kind | title }}</span>
{% if page.group %}
<span class="badge badge-group">{{ page.group }}</span>
{% endif %}

{% if mermaid_diagram %}
<section class="provenance">
  <h2>Data Provenance</h2>
  <pre class="mermaid">{{ mermaid_diagram }}</pre>
</section>
{% endif %}

{% if findings_html %}
<section class="findings">
  <h2>Findings</h2>
  <div class="markdown-body">{{ findings_html }}</div>
</section>
{% endif %}

{% if output_images %}
<section class="output-gallery">
  <h2>Output</h2>
  {% for img in output_images %}
  <figure>
    <img src="{{ img.src }}" alt="{{ img.alt }}" loading="lazy">
    <figcaption>{{ img.label }}</figcaption>
  </figure>
  {% endfor %}
</section>
{% endif %}

{% if methods_html %}
<section class="methods">
  <h2>Methods</h2>
  <div class="markdown-body">{{ methods_html }}</div>
</section>
{% endif %}

{% if page_sources %}
<section class="sources">
  <h2>Sources</h2>
  <table class="source-table">
    <thead><tr><th>Source</th><th>Type</th><th>Description</th></tr></thead>
    <tbody>
    {% for src in page_sources %}
      <tr>
        <td>{{ src.name }}</td>
        <td><span class="badge badge-{{ src.kind }}">{{ src.kind }}</span></td>
        <td>{{ src.description }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
</section>
{% endif %}
{% endblock %}
```

### How the website generator works

`products/website/main.py` does the following:

1. **Discovers manifests** — walks `pipeline/*/SOURCES.yaml` and `analyses/*/SOURCES.yaml`.
2. **Builds a table lookup** — maps each DB table name to the pipeline that produces it.
3. **Generates Mermaid diagrams** — for each page, builds a `flowchart LR` showing the full data lineage (source files/APIs -> pipeline -> tables -> analysis).
4. **Collects output images** — finds `.png/.svg/.jpg` files in each analysis's `output/` dir, copies them to `output/analyses/img/<dirname>/`.
5. **Collects page sources** — traces upstream through the table lookup to list all APIs, files, and tables used.
6. **Renders pages** — uses Jinja2 templates with rendered Markdown (via mistune) for FINDINGS.md and METHODS.md.
7. **Writes CSS** — a single inline `write_css()` function generates `style.css`.

### Mermaid diagram generation

Three diagram builders:

- **`build_mermaid_pipeline(manifest)`** — `APIs/Files --> Pipeline --> Tables Produced`
- **`build_mermaid_analysis(manifest, table_lookup)`** — full lineage: `APIs/Files --> Pipeline --> Tables --> Analysis`, with dashed arrows for cross-analysis refs.
- **`build_mermaid_source(source, table_lookup)`** — `Source --> Pipelines --> Tables --> Downstream Analyses`

All use `%%{init: {'flowchart': {'useMaxWidth': false}}}%%` so diagrams can scroll horizontally.

### Building and deploying

```bash
# Generate the site
uv run python products/website/main.py

# Open locally
open products/website/output/index.html

# Deploy to Netlify
npx netlify-cli link --name <site-name>
npx netlify-cli deploy --prod --dir=products/website/output
```

---

## 8. Glossary (`glossary.yaml`)

Optional domain glossary rendered as a dedicated page:

```yaml
categories:
  - name: "Statistical Methods"
    terms:
      - term: "TF-IDF"
        abbreviation: "TF-IDF"
        definition: "Term Frequency-Inverse Document Frequency, a text analysis metric."
      - term: "Go-Zone"
        definition: "A bivariate plot quadrant..."
  - name: "Data Sources"
    terms:
      - term: "ACS"
        abbreviation: "ACS"
        definition: "American Community Survey..."
```

---

## 9. Scaffold CLI Reference

```bash
# Create a full new project
uv run python scaffold.py scaffold <target-dir> [--name NAME] [--package PKG] [--db FILE]

# Add a new analysis (auto-numbers from highest existing)
uv run python scaffold.py add <name> [--title "Title"] [--summary "Summary"]

# Run all pipeline steps then all analyses
uv run python scaffold.py run-all

# Regenerate the analysis index in FINDINGS.md
uv run python scaffold.py index

# All commands support --json (machine-readable) and --dry-run (preview)
```

---

## 10. Testing

`tests/test_smoke.py` auto-discovers all analyses and validates:
- Each `main.py` can be imported without error.
- Each analysis has all required files (`README.md`, `METHODS.md`, `FINDINGS.md`, `main.py`).
- Each analysis has an `output/` directory.
- Each `METHODS.md` has all 4 required sections (`## Question`, `## Approach`, `## Data`, `## Output`).

```bash
uv run pytest
```

---

## 11. Red-Team Protocol

`docs/RED-TEAM.md` defines a methodological review process. Reviews produce **report-only** outputs in `RED-TEAM-REPORTS/` (no code changes until human approval). Each report uses 8 checklist categories (unit of analysis, stratification, statistical testing, regression to the mean, composition, code-doc consistency, joins/filters, numerical correctness) with severity levels (Significant / Moderate / Low).

---

## 12. Replication Checklist

To set up this pattern for a new project:

1. [ ] Run `scaffold.py scaffold <dir>` with your project config
2. [ ] `git init && uv sync` in the new directory
3. [ ] Edit `scaffold.toml` with your project's name, package, and dependencies
4. [ ] Place your database at `data/data.db` and document it in `data/SCHEMA.md`
5. [ ] Create pipeline steps manually in `pipeline/01_*`, `02_*`, etc.
6. [ ] Add analyses via `scaffold.py add <name>`
7. [ ] Write METHODS.md before code for each analysis
8. [ ] Create `SOURCES.yaml` manifests (or auto-generate with `generate_manifests.py`)
9. [ ] Copy `products/website/` directory and customize templates (project name, nav links)
10. [ ] Add a `glossary.yaml` if your domain has specialized terminology
11. [ ] Run `uv run python products/website/main.py` to generate the site
12. [ ] Deploy with `npx netlify-cli deploy --prod --dir=products/website/output`

### What scaffold.py generates vs. what you add manually

| Generated by `scaffold.py scaffold` | Added manually |
|--------------------------------------|----------------|
| `pyproject.toml`, `CLAUDE.md`, `CONTRIBUTING.md` | Pipeline steps (`pipeline/NN_*/`) |
| `scaffold.toml`, `ruff.toml`, `.gitignore` | `products/website/` (templates, generator) |
| `src/<package>/common.py` | `products/website/generate_manifests.py` |
| `data/SCHEMA.md`, `data/README.md` | `glossary.yaml` |
| `docs/RED-TEAM.md`, `RED-TEAM-REPORTS/` | `SOURCES.yaml` per step (or auto-generate) |
| `tests/test_smoke.py`, `tests/conftest.py` | Raw data files in `data/` |
| `FINDINGS.md`, `README.md` | Netlify configuration |

### Website-specific files to copy

The website layer is not generated by `scaffold.py` — copy these from an existing project:

```
products/website/
├── main.py                    # ~850 lines: manifest discovery, Mermaid generation,
│                              #   image collection, HTML rendering, CSS
├── generate_manifests.py      # ~210 lines: parses main.py to auto-build SOURCES.yaml
├── glossary.yaml              # Domain-specific glossary (optional)
├── README.md
└── templates/
    ├── base.html
    ├── index.html
    ├── page.html
    ├── sources.html
    ├── source_detail.html
    └── glossary.html
```

Customize by:
- Replacing project name in `base.html` nav brand
- Updating `GROUP_ORDER` in `main.py` for your analysis categories
- Updating `GROUP_MAP` in `generate_manifests.py` for your analysis-to-group assignments
- Adding website dependencies to `pyproject.toml`: `jinja2`, `mistune`, `pyyaml`
