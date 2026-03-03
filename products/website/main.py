"""Generate a static documentation site from pipeline and analysis manifests."""

from __future__ import annotations

import sqlite3
import subprocess
import re
import shutil
from datetime import datetime, timezone
from html import escape
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jinja2 import Environment, FileSystemLoader

try:
    import mistune
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    mistune = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
GENERIC_SOURCE_DESCRIPTIONS = {
    "file": "Project data file consumed by one or more analyses or pipeline steps.",
    "api": "External API consumed by one or more pipeline steps.",
    "table": "Database table consumed by one or more analyses.",
    "dependency": "Python library dependency used by one or more analyses or pipeline steps.",
}
DEPENDENCY_DESCRIPTIONS = {
    "branca": "Utility library used by Folium for map templating, colormaps, and HTML components.",
    "numpy": "Numerical computing library for vectorized arrays and matrix operations.",
    "polars": "Dataframe library used for fast tabular data transformations and aggregation.",
    "scipy": "Scientific computing library used for statistical tests and numerical routines.",
    "statsmodels": "Statistical modeling library used for regression and time-series methods.",
    "matplotlib": "Plotting library used to generate static charts.",
    "folium": "Mapping library used to render interactive geospatial visualizations.",
    "xyzservices": "Catalog of map tile provider metadata used by mapping and geospatial visualization tools.",
    "requests": "HTTP client library used to fetch remote APIs and web resources.",
    "yaml": "YAML parsing library used to read and write manifest metadata.",
    "jinja2": "Templating library used to render static HTML pages.",
    "mistune": "Markdown parser used to convert findings and methods docs into HTML.",
}


@dataclass
class Page:
    kind: str
    title: str
    slug: str
    rel_dir: str
    group: str | None
    manifest: dict


def read_yaml(path: Path) -> dict:
    """Read YAML file into a dictionary."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def discover_pages() -> list[Page]:
    """Discover pipeline and analysis pages from SOURCES.yaml files."""
    pages: list[Page] = []
    for manifest_path in sorted((PROJECT_ROOT / "pipeline").glob("*/SOURCES.yaml")):
        manifest = read_yaml(manifest_path)
        step_dir = manifest_path.parent
        pages.append(
            Page(
                kind="pipeline",
                title=manifest.get("title", step_dir.name),
                slug=step_dir.name,
                rel_dir=f"pipeline/{step_dir.name}",
                group=manifest.get("group"),
                manifest=manifest,
            )
        )
    for manifest_path in sorted((PROJECT_ROOT / "analyses").glob("*/SOURCES.yaml")):
        manifest = read_yaml(manifest_path)
        analysis_dir = manifest_path.parent
        pages.append(
            Page(
                kind="analysis",
                title=manifest.get("title", analysis_dir.name),
                slug=analysis_dir.name,
                rel_dir=f"analyses/{analysis_dir.name}",
                group=manifest.get("group"),
                manifest=manifest,
            )
        )
    return pages


def build_table_lookup(pages: list[Page]) -> dict[str, Page]:
    """Map produced table names to their pipeline page."""
    lookup: dict[str, Page] = {}
    for page in pages:
        if page.kind != "pipeline":
            continue
        for table in page.manifest.get("tables_produced", []):
            name = table.get("name") if isinstance(table, dict) else str(table)
            lookup[name] = page
    return lookup


def build_table_descriptions(pages: list[Page]) -> dict[str, str]:
    """Map produced table names to one-sentence descriptions from pipeline manifests."""
    lookup: dict[str, str] = {}
    for page in pages:
        if page.kind != "pipeline":
            continue
        for table in page.manifest.get("tables_produced", []):
            if isinstance(table, dict):
                name = str(table.get("name", "")).strip()
                desc = str(table.get("description", "")).strip()
            else:
                name = str(table).strip()
                desc = ""
            if not name:
                continue
            lookup[name] = sentence(desc) or "Database table produced by a pipeline step."
    return lookup


def md_to_html(path: Path) -> str:
    """Render markdown file if present."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if mistune is not None:
        md = mistune.create_markdown(plugins=["table"])
        return md(text)
    return _md_fallback_to_html(text)


def _md_fallback_to_html(text: str) -> str:
    """Fallback markdown renderer with table/list/heading support."""
    lines = text.strip().split("\n")
    html_parts: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        if re.match(r"^---+\s*$", line):
            html_parts.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            html_parts.append(f"<h{level}>{_inline_md(m.group(2))}</h{level}>")
            i += 1
            continue

        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            html_parts.append(_md_table_to_html(table_lines))
            continue

        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]))
                i += 1
            html_parts.append("<ul>" + "".join(f"<li>{_inline_md(it)}</li>" for it in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]))
                i += 1
            html_parts.append("<ol>" + "".join(f"<li>{_inline_md(it)}</li>" for it in items) + "</ol>")
            continue

        para_lines = []
        while i < len(lines) and lines[i].strip() and not _is_md_block_start(lines[i]):
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            html_parts.append(f"<p>{_inline_md(' '.join(para_lines))}</p>")

    return "\n".join(html_parts)


def _is_md_block_start(line: str) -> bool:
    """Return True if the line begins a block node."""
    return bool(
        re.match(r"^#{1,6}\s+", line)
        or line.strip().startswith("|")
        or re.match(r"^[-*]\s+", line)
        or re.match(r"^\d+\.\s+", line)
        or re.match(r"^---+\s*$", line)
    )


def _inline_md(text: str) -> str:
    """Render inline markdown with HTML escaping."""
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def _md_table_to_html(lines: list[str]) -> str:
    """Render GFM-style markdown table block to HTML."""
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    if len(rows) < 2:
        return f"<p>{_inline_md(' '.join(lines))}</p>"
    header = rows[0]
    data_rows = rows[2:]
    html = "<table><thead><tr>"
    for cell in header:
        html += f"<th>{_inline_md(cell)}</th>"
    html += "</tr></thead><tbody>"
    for row in data_rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{_inline_md(cell)}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


def sentence(text: str) -> str:
    """Normalize text into a concise one-sentence description."""
    value = text.strip()
    if not value:
        return ""
    if value[-1] not in ".!?":
        value += "."
    return value


def tables_produced_for_page(page: Page) -> list[dict[str, str]]:
    """Normalize pipeline tables_produced entries for page rendering."""
    out: list[dict[str, str]] = []
    for item in page.manifest.get("tables_produced", []):
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            desc = sentence(str(item.get("description", "")).strip())
        else:
            name = str(item).strip()
            desc = ""
        if not name:
            continue
        out.append(
            {
                "name": name,
                "description": desc or "Database table produced by this pipeline step.",
            }
        )
    return out


def validate_pipeline_manifests(pages: list[Page]) -> list[str]:
    """Validate pipeline manifests include descriptive tables_produced metadata."""
    errors: list[str] = []
    for page in pages:
        if page.kind != "pipeline":
            continue
        entries = page.manifest.get("tables_produced", [])
        if not entries:
            errors.append(f"{page.rel_dir}: missing tables_produced entries")
            continue
        for idx, item in enumerate(entries, start=1):
            if not isinstance(item, dict):
                errors.append(f"{page.rel_dir}: tables_produced[{idx}] must be a mapping with name/description")
                continue
            name = str(item.get("name", "")).strip()
            desc = str(item.get("description", "")).strip()
            if not name:
                errors.append(f"{page.rel_dir}: tables_produced[{idx}] missing non-empty name")
            if not desc:
                errors.append(f"{page.rel_dir}: tables_produced[{idx}] missing non-empty description")
    return errors


def dependency_description(name: str) -> str:
    """Return one-sentence description for a dependency name."""
    key = name.strip().lower()
    return DEPENDENCY_DESCRIPTIONS.get(
        key,
        "Python library dependency used by one or more analyses or pipeline steps.",
    )


def _prefer_description(current: str, candidate: str, kind: str) -> str:
    """Keep the more specific source description when merging inventory entries."""
    current_s = sentence(current)
    candidate_s = sentence(candidate)
    generic = GENERIC_SOURCE_DESCRIPTIONS.get(kind, "")
    if not current_s:
        return candidate_s or generic
    if not candidate_s:
        return current_s
    if current_s == generic and candidate_s != generic:
        return candidate_s
    if len(candidate_s) > len(current_s) and candidate_s != generic:
        return candidate_s
    return current_s


def page_sources(
    page: Page, table_lookup: dict[str, Page], table_descriptions: dict[str, str]
) -> list[dict[str, str]]:
    """Build a normalized source list for one page."""
    out: list[dict[str, str]] = []
    for item in page.manifest.get("files", []):
        name = item.get("path", "file")
        desc = sentence(item.get("description", ""))
        out.append(
            {
                "name": name,
                "kind": "file",
                "description": desc or GENERIC_SOURCE_DESCRIPTIONS["file"],
                "owner": sentence(item.get("owner", "")) or "Local project data owner not specified.",
                "freshness": sentence(item.get("freshness", "")) or "Snapshot file; refresh by rerunning its pipeline step.",
                "caveat": sentence(item.get("caveat", "")) or "May lag upstream source updates.",
                "relevance": desc or "Input file directly consumed by this page.",
            }
        )
    for item in page.manifest.get("apis", []):
        name = item.get("name", item.get("url", "api"))
        desc = sentence(item.get("description", ""))
        host = urlparse(item.get("url", "")).netloc
        out.append(
            {
                "name": name,
                "kind": "api",
                "description": desc or GENERIC_SOURCE_DESCRIPTIONS["api"],
                "owner": sentence(item.get("owner", "")) or (f"Hosted by {host}." if host else "External API owner not specified."),
                "freshness": sentence(item.get("freshness", "")) or "Queried during pipeline execution; freshness depends on upstream updates.",
                "caveat": sentence(item.get("caveat", "")) or "Availability and schema can change without notice.",
                "relevance": desc or "API endpoint provides upstream inputs for this page.",
            }
        )
    for table in page.manifest.get("tables", []):
        producer = table_lookup.get(table)
        table_desc = table_descriptions.get(table, "")
        if producer and table_desc:
            desc = f"{table_desc} Produced by {producer.title}."
        elif table_desc:
            desc = table_desc
        elif producer:
            desc = f"Database table consumed by this page and produced by {producer.title}."
        else:
            desc = GENERIC_SOURCE_DESCRIPTIONS["table"]
        out.append(
            {
                "name": table,
                "kind": "table",
                "description": desc,
                "owner": f"Produced by {producer.title}." if producer else "Project pipeline owner not linked.",
                "freshness": "Updated when the producing pipeline step is rerun." if producer else "Refresh cadence unknown.",
                "caveat": "Coverage depends on upstream source availability and ETL assumptions.",
                "relevance": "Primary analytical table used in this page's computations.",
            }
        )
    for dep in page.manifest.get("dependencies", []):
        out.append(
            {
                "name": dep,
                "kind": "dependency",
                "description": dependency_description(dep),
                "owner": "Open-source Python ecosystem maintainers.",
                "freshness": "Version pinned by project environment until dependency updates are applied.",
                "caveat": "Library updates may change behavior or defaults.",
                "relevance": "Runtime dependency required for this page's pipeline or analysis code.",
            }
        )
    return out


def group_output_artifacts(artifacts: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group output artifacts by presentation bucket."""
    return {
        "charts": [a for a in artifacts if a.get("kind") == "image"],
        "interactive": [a for a in artifacts if a.get("kind") == "html"],
        "data": [a for a in artifacts if a.get("kind") not in {"image", "html"}],
    }


def get_git_revision() -> str:
    """Return short git commit hash if available."""
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=PROJECT_ROOT,
                text=True,
            )
            .strip()
        )
    except Exception:
        return "unknown"


def get_table_month_coverage() -> dict[str, tuple[str, str]]:
    """Return min/max month coverage for database tables that include month keys."""
    db_path = PROJECT_ROOT / "data" / "prt.db"
    if not db_path.exists():
        return {}
    coverage: dict[str, tuple[str, str]] = {}
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for table in tables:
            cols = {
                row[1]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            month_col = "month" if "month" in cols else None
            if table == "schedule_periods" and {"start_date", "end_date"} <= cols:
                row = conn.execute(
                    "SELECT MIN(SUBSTR(start_date,1,7)), MAX(SUBSTR(end_date,1,7)) FROM schedule_periods"
                ).fetchone()
                if row and row[0] and row[1]:
                    coverage[table] = (row[0], row[1])
                continue
            if not month_col:
                continue
            row = conn.execute(
                f"SELECT MIN({month_col}), MAX({month_col}) FROM {table} WHERE {month_col} IS NOT NULL"
            ).fetchone()
            if row and row[0] and row[1]:
                coverage[table] = (str(row[0]), str(row[1]))
    finally:
        conn.close()
    return coverage


def coverage_text_for_page(page: Page, table_coverage: dict[str, tuple[str, str]]) -> str:
    """Build concise coverage-window text for a page from referenced tables."""
    table_names: list[str] = list(page.manifest.get("tables", []))
    for item in page.manifest.get("tables_produced", []):
        if isinstance(item, dict):
            t = str(item.get("name", "")).strip()
        else:
            t = str(item).strip()
        if t:
            table_names.append(t)
    windows = [(t, table_coverage[t]) for t in table_names if t in table_coverage]
    if not windows:
        return "Coverage window unavailable for this page."
    starts = sorted(w[1][0] for w in windows)
    ends = sorted(w[1][1] for w in windows)
    tables = ", ".join(sorted({w[0] for w in windows})[:4])
    suffix = "" if len(windows) <= 4 else ", ..."
    return f"{starts[0]} to {ends[-1]} (from {tables}{suffix})."


def build_mermaid_page(page: Page, table_lookup: dict[str, Page]) -> str:
    """Build a simple data-lineage diagram for one page."""
    lines = ["flowchart LR"]
    node_self = page.slug.replace("-", "_")
    lines.append(f"  {node_self}[\"{page.title}\"]")
    file_nodes: list[str] = []
    api_nodes: list[str] = []
    table_nodes: list[str] = []
    dep_nodes: list[str] = []
    pipeline_nodes: list[str] = []

    for idx, file_item in enumerate(page.manifest.get("files", []), start=1):
        node = f"f{idx}_{node_self}"
        label = file_item.get("path", "file")
        lines.append(f"  {node}[\"{label}\"] --> {node_self}")
        file_nodes.append(node)

    for idx, api_item in enumerate(page.manifest.get("apis", []), start=1):
        node = f"a{idx}_{node_self}"
        label = api_item.get("name", "API")
        lines.append(f"  {node}[\"{label}\"] --> {node_self}")
        api_nodes.append(node)

    for table in page.manifest.get("tables", []):
        producer = table_lookup.get(table)
        table_node = f"t_{table.replace('-', '_')}"
        lines.append(f"  {table_node}[\"{table}\"] --> {node_self}")
        table_nodes.append(table_node)
        if producer:
            prod_node = producer.slug.replace("-", "_")
            lines.append(f"  {prod_node}[\"{producer.title}\"] --> {table_node}")
            pipeline_nodes.append(prod_node)

    for idx, dep in enumerate(page.manifest.get("dependencies", []), start=1):
        node = f"d{idx}_{node_self}"
        lines.append(f"  {node}[\"{dep} (lib)\"] --> {node_self}")
        dep_nodes.append(node)

    for table in page.manifest.get("tables_produced", []):
        table_name = table.get("name") if isinstance(table, dict) else str(table)
        table_node = f"tp_{table_name.replace('-', '_')}"
        lines.append(f"  {node_self} --> {table_node}[\"{table_name}\"]")
        table_nodes.append(table_node)

    lines.append("  classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;")
    lines.append("  classDef table fill:#ecfeff,stroke:#0e7490,color:#164e63;")
    lines.append("  classDef dep fill:#fff7ed,stroke:#c2410c,color:#7c2d12,stroke-dasharray: 4 2;")
    lines.append("  classDef file fill:#eef2ff,stroke:#6366f1,color:#3730a3;")
    lines.append("  classDef api fill:#f0fdf4,stroke:#16a34a,color:#14532d;")
    lines.append("  classDef pipeline fill:#f5f3ff,stroke:#7c3aed,color:#4c1d95;")

    lines.append(f"  class {node_self} page;")
    if table_nodes:
        lines.append(f"  class {','.join(sorted(set(table_nodes)))} table;")
    if dep_nodes:
        lines.append(f"  class {','.join(sorted(set(dep_nodes)))} dep;")
    if file_nodes:
        lines.append(f"  class {','.join(sorted(set(file_nodes)))} file;")
    if api_nodes:
        lines.append(f"  class {','.join(sorted(set(api_nodes)))} api;")
    if pipeline_nodes:
        lines.append(f"  class {','.join(sorted(set(pipeline_nodes)))} pipeline;")

    return "\n".join(lines)


def collect_outputs(page: Page) -> tuple[list[dict[str, str]], list[str]]:
    """Copy declared output artifacts to website output and return metadata/errors."""
    src_dir = PROJECT_ROOT / page.rel_dir / "output"
    declared = page.manifest.get("outputs", [])
    if not src_dir.exists():
        if not declared:
            return [], []
        return [], [f"{page.rel_dir}: output directory missing but outputs are declared"]

    artifacts: list[dict[str, str]] = []
    errors: list[str] = []
    kind_path = "analyses" if page.kind == "analysis" else page.kind
    dest_dir = OUTPUT_DIR / "assets" / kind_path / page.slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Backward compatibility for manifests that do not declare outputs yet.
    if not declared:
        for path in sorted(src_dir.iterdir()):
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg"}:
                continue
            target = dest_dir / path.name
            shutil.copy2(path, target)
            artifacts.append(
                {
                    "src": f"assets/{kind_path}/{page.slug}/{path.name}",
                    "alt": path.stem,
                    "label": path.name,
                    "kind": "image",
                    "description": "Generated chart image produced by this page.",
                }
            )
        return artifacts, errors

    for item in declared:
        rel_path = str(item.get("path", "")).strip()
        kind = str(item.get("kind", "file")).strip().lower() or "file"
        description = sentence(str(item.get("description", "")).strip())
        if not rel_path:
            errors.append(f"{page.rel_dir}: outputs entry missing 'path'")
            continue

        path = src_dir / rel_path
        if not path.exists():
            errors.append(f"{page.rel_dir}: declared output missing: output/{rel_path}")
            continue
        if not path.is_file():
            errors.append(f"{page.rel_dir}: declared output is not a file: output/{rel_path}")
            continue

        target = dest_dir / path.name
        shutil.copy2(path, target)
        artifacts.append(
            {
                "src": f"assets/{kind_path}/{page.slug}/{path.name}",
                "alt": path.stem,
                "label": path.name,
                "kind": kind,
                "description": description or "Generated artifact produced by this page.",
            }
        )

    return artifacts, errors


def write_css() -> None:
    """Write stylesheet for generated pages."""
    css = """
:root {
  --bg: #f7efe2;
  --ink: #172026;
  --ink-muted: #42515c;
  --panel: #fffdf9;
  --line: #c8b6a1;
  --accent: #a34f2f;
  --accent-soft: #f4dfce;
  --accent-alt: #1e6f66;
  --radius: 14px;
  --shadow: 0 14px 30px rgba(36, 20, 4, 0.08);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "IBM Plex Sans", "Trebuchet MS", sans-serif;
  color: var(--ink);
  background: radial-gradient(1200px 600px at 12% -5%, #ffe4cc 0%, transparent 55%),
              radial-gradient(900px 500px at 100% 12%, #dcefe9 0%, transparent 52%),
              var(--bg);
  line-height: 1.55;
}
.bg-layer { position: fixed; inset: 0; pointer-events: none; z-index: -1; }
.bg-layer-one { background: linear-gradient(135deg, rgba(163,79,47,0.06), transparent 40%); }
.bg-layer-two { background: linear-gradient(310deg, rgba(30,111,102,0.08), transparent 45%); }
.site-header {
  position: sticky;
  top: 0;
  z-index: 30;
  backdrop-filter: blur(8px);
  background: rgba(247, 239, 226, 0.88);
  border-bottom: 1px solid rgba(163, 79, 47, 0.18);
}
.site-nav {
  max-width: 1160px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.95rem 1.25rem;
}
.site-nav a { color: var(--ink); text-decoration: none; }
.site-nav a:hover { color: var(--accent); }
.brand {
  font-family: "Fraunces", "Georgia", serif;
  font-weight: 700;
  font-size: 1.18rem;
  letter-spacing: 0.01em;
}
.nav-links { display: flex; gap: 1rem; flex-wrap: wrap; font-weight: 500; }
.container { max-width: 1160px; margin: 0 auto; padding: 1.25rem; }
.shell { display: grid; gap: 1.2rem; }
.hero {
  background: linear-gradient(150deg, #1f403d 0%, #285552 35%, #a34f2f 100%);
  color: #fff;
  border-radius: var(--radius);
  padding: 2rem 1.5rem;
  box-shadow: var(--shadow);
}
.hero-compact { padding: 1.35rem 1.2rem; }
.hero h1 {
  font-family: "Fraunces", "Georgia", serif;
  margin: 0.15rem 0 0.45rem;
  line-height: 1.08;
  font-size: clamp(1.7rem, 2.8vw, 2.5rem);
}
.kicker {
  margin: 0;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.84;
  font-weight: 600;
}
.lede { margin: 0; color: rgba(255,255,255,0.9); max-width: 70ch; }
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1.05rem 1.1rem;
  box-shadow: var(--shadow);
}
.toc-panel { position: sticky; top: 74px; z-index: 5; }
.toc-links { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.toc-links a {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  text-decoration: none;
  background: #fffaf4;
}
.pager { display: flex; justify-content: space-between; gap: 0.75rem; }
.pager a { font-weight: 600; }
.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.8rem;
}
.filters label { display: grid; gap: 0.25rem; font-weight: 600; color: var(--ink-muted); }
.filters input, .filters select {
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.45rem 0.55rem;
  font: inherit;
  background: #fff;
}
h2, h3 {
  font-family: "Fraunces", "Georgia", serif;
  margin: 0.35rem 0 0.7rem;
  line-height: 1.2;
}
a { color: var(--accent-alt); text-decoration-thickness: 2px; text-underline-offset: 2px; }
a:hover { color: var(--accent); }
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.85rem;
}
.card {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.9rem;
  background: #fffaf4;
  display: grid;
  gap: 0.4rem;
}
.card h3 { margin: 0; font-size: 1.05rem; }
.card p { margin: 0; color: var(--ink-muted); font-size: 0.94rem; }
.tag {
  justify-self: start;
  display: inline-block;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
  border-radius: 999px;
  padding: 0.22rem 0.55rem;
  border: 1px solid #d8b79a;
  background: var(--accent-soft);
  color: #7a331d;
}
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.95rem;
}
.shot-card {
  margin: 0;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  overflow: hidden;
}
.artifact-frame {
  width: 100%;
  height: 320px;
  border: 0;
  background: #fff;
}
.artifact-body {
  padding: 0.65rem;
  display: grid;
  gap: 0.35rem;
}
.artifact-kind {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-muted);
  font-weight: 700;
}
.artifact-link {
  font-weight: 600;
  word-break: break-word;
}
.artifact-desc {
  margin: 0;
  color: var(--ink-muted);
  font-size: 0.9rem;
}
.tab-bar { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 0.7rem; }
.tab-btn {
  border: 1px solid var(--line);
  background: #fff;
  color: var(--ink);
  padding: 0.34rem 0.66rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
}
.tab-btn.active { background: var(--accent-soft); border-color: #d8b79a; }
.output-pane { display: none; }
.output-pane.active { display: block; }
.csv-preview { margin-top: 0.45rem; }
.csv-preview summary { cursor: pointer; font-weight: 600; }
.csv-preview-body { margin-top: 0.45rem; }
.fold > summary {
  list-style: none;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.fold > summary::-webkit-details-marker { display: none; }
img { max-width: 100%; height: auto; display: block; }
figcaption {
  padding: 0.55rem 0.65rem;
  font-size: 0.82rem;
  color: var(--ink-muted);
  border-top: 1px solid var(--line);
}
.source-table, table { width: 100%; border-collapse: collapse; }
th, td {
  border: 1px solid var(--line);
  padding: 0.52rem 0.6rem;
  text-align: left;
  vertical-align: top;
}
th { background: #f4e5d2; font-weight: 700; }
.markdown h1, .markdown h2, .markdown h3 { margin-top: 1rem; }
.markdown p { margin: 0.65rem 0; }
.markdown ul, .markdown ol { margin: 0.45rem 0 0.65rem 1.2rem; }
.markdown table { margin: 0.8rem 0; }
pre.mermaid {
  overflow-x: auto;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.6rem;
}
@media (max-width: 760px) {
  .site-nav { align-items: flex-start; flex-direction: column; }
  .nav-links { gap: 0.65rem; }
  .container { padding: 0.85rem; }
  .hero { padding: 1.2rem 0.95rem; }
  .toc-panel { position: static; }
  .pager { flex-direction: column; }
  .panel { padding: 0.85rem; }
  th, td { font-size: 0.9rem; }
}
"""
    (OUTPUT_DIR / "style.css").write_text(css.strip() + "\n", encoding="utf-8")


def main() -> None:
    """Generate full static site output."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    pages = discover_pages()
    pipeline_manifest_errors = validate_pipeline_manifests(pages)
    table_lookup = build_table_lookup(pages)
    table_descriptions = build_table_descriptions(pages)
    table_coverage = get_table_month_coverage()
    run_metadata = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "git_revision": get_git_revision(),
    }

    analysis_pages = [p for p in pages if p.kind == "analysis"]
    analysis_slugs = [p.slug for p in sorted(analysis_pages, key=lambda p: p.slug)]
    prev_next: dict[str, dict[str, Page | None]] = {}
    by_slug = {p.slug: p for p in analysis_pages}
    for idx, slug in enumerate(analysis_slugs):
        prev_page = by_slug[analysis_slugs[idx - 1]] if idx > 0 else None
        next_page = by_slug[analysis_slugs[idx + 1]] if idx + 1 < len(analysis_slugs) else None
        prev_next[slug] = {"prev": prev_page, "next": next_page}

    site_items = []
    source_index: dict[tuple[str, str], dict] = {}
    output_errors: list[str] = []

    for page in pages:
        kind_path = "analyses" if page.kind == "analysis" else page.kind
        page_dir = OUTPUT_DIR / kind_path / page.slug
        page_dir.mkdir(parents=True, exist_ok=True)

        findings_html = md_to_html(PROJECT_ROOT / page.rel_dir / "FINDINGS.md")
        methods_html = md_to_html(PROJECT_ROOT / page.rel_dir / "METHODS.md")
        output_artifacts, errors = collect_outputs(page)
        output_errors.extend(errors)
        output_groups = group_output_artifacts(output_artifacts)
        page_tables_produced = tables_produced_for_page(page)
        sources = page_sources(page, table_lookup, table_descriptions)
        mermaid = build_mermaid_page(page, table_lookup)
        coverage_text = coverage_text_for_page(page, table_coverage)
        neighbors = prev_next.get(page.slug, {"prev": None, "next": None})

        html = env.get_template("page.html").render(
            root="../../",
            page=page,
            run_metadata=run_metadata,
            coverage_text=coverage_text,
            findings_html=findings_html,
            methods_html=methods_html,
            output_artifacts=output_artifacts,
            output_groups=output_groups,
            page_tables_produced=page_tables_produced,
            page_sources=sources,
            mermaid_diagram=mermaid,
            prev_page=neighbors["prev"],
            next_page=neighbors["next"],
        )
        (page_dir / "index.html").write_text(html, encoding="utf-8")

        rel_path = f"{kind_path}/{page.slug}/index.html"
        site_items.append(
            {
                "title": page.title,
                "path": rel_path,
                "group": page.group,
                "description": page.manifest.get("description", ""),
                "kind": page.kind,
                "output_kinds": sorted({str(o.get("kind", "file")) for o in page.manifest.get("outputs", [])}),
            }
        )

        for src in sources:
            key = (src["kind"], src["name"])
            entry = source_index.setdefault(
                key,
                {
                    "kind": src["kind"],
                    "name": src["name"],
                    "description": src["description"],
                    "owner": src.get("owner", ""),
                    "freshness": src.get("freshness", ""),
                    "caveat": src.get("caveat", ""),
                    "relevance": src.get("relevance", ""),
                    "consumers": [],
                },
            )
            entry["description"] = _prefer_description(
                entry.get("description", ""), src.get("description", ""), src["kind"]
            )
            if not entry.get("owner"):
                entry["owner"] = src.get("owner", "")
            if not entry.get("freshness"):
                entry["freshness"] = src.get("freshness", "")
            if not entry.get("caveat"):
                entry["caveat"] = src.get("caveat", "")
            if not entry.get("relevance"):
                entry["relevance"] = src.get("relevance", "")
            entry["consumers"].append({"title": page.title, "path": rel_path})

    pipeline_items = sorted([i for i in site_items if i["path"].startswith("pipeline/")], key=lambda x: x["path"])
    analysis_items = sorted([i for i in site_items if i["path"].startswith("analyses/")], key=lambda x: x["path"])
    analysis_groups = sorted({i.get("group") for i in analysis_items if i.get("group")})
    output_kind_options = sorted({k for i in analysis_items for k in i.get("output_kinds", [])})

    index_html = env.get_template("index.html").render(
        root="",
        pipeline=pipeline_items,
        analyses=analysis_items,
        analysis_groups=analysis_groups,
        output_kind_options=output_kind_options,
        run_metadata=run_metadata,
    )
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    source_list = []
    for idx, source in enumerate(sorted(source_index.values(), key=lambda x: (x["kind"], x["name"]))):
        slug = f"source-{idx:03d}.html"
        source["path"] = f"sources/{slug}"
        source_list.append(source)

    sources_dir = OUTPUT_DIR / "sources"
    sources_dir.mkdir(exist_ok=True)
    for source in source_list:
        mermaid = "flowchart LR\n"
        source_node = "src"
        source_name = source["name"]
        mermaid += f'  {source_node}["{source_name}"]\n'
        for idx, consumer in enumerate(source["consumers"], start=1):
            node = f"c{idx}"
            consumer_title = consumer["title"]
            mermaid += f'  {source_node} --> {node}["{consumer_title}"]\n'
        html = env.get_template("source_detail.html").render(
            root="../",
            source=source,
            consumers=source["consumers"],
            mermaid_diagram=mermaid,
            run_metadata=run_metadata,
        )
        (OUTPUT_DIR / source["path"]).write_text(html, encoding="utf-8")

    sources_html = env.get_template("sources.html").render(
        root="",
        sources=source_list,
        run_metadata=run_metadata,
    )
    (OUTPUT_DIR / "sources.html").write_text(sources_html, encoding="utf-8")

    glossary_data = read_yaml(Path(__file__).resolve().parent / "glossary.yaml")
    glossary_html = env.get_template("glossary.html").render(
        root="",
        categories=glossary_data.get("categories", []),
        run_metadata=run_metadata,
    )
    (OUTPUT_DIR / "glossary.html").write_text(glossary_html, encoding="utf-8")

    all_errors = pipeline_manifest_errors + output_errors
    if all_errors:
        details = "\n".join(f"  - {msg}" for msg in all_errors)
        raise RuntimeError(f"Website generation failed due to manifest/output validation errors:\n{details}")

    write_css()
    print(f"Generated website output at {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
