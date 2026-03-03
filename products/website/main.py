"""Generate a static documentation site from pipeline and analysis manifests."""

from __future__ import annotations

import shutil
from html import escape
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

try:
    import mistune
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    mistune = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


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


def md_to_html(path: Path) -> str:
    """Render markdown file if present."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if mistune is not None:
        md = mistune.create_markdown()
        return md(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "".join(f"<p>{escape(p)}</p>" for p in paragraphs)


def page_sources(page: Page, table_lookup: dict[str, Page]) -> list[dict[str, str]]:
    """Build a normalized source list for one page."""
    out: list[dict[str, str]] = []
    for item in page.manifest.get("files", []):
        out.append(
            {
                "name": item.get("path", "file"),
                "kind": "file",
                "description": item.get("description", ""),
            }
        )
    for item in page.manifest.get("apis", []):
        out.append(
            {
                "name": item.get("name", item.get("url", "api")),
                "kind": "api",
                "description": item.get("description", ""),
            }
        )
    for table in page.manifest.get("tables", []):
        producer = table_lookup.get(table)
        desc = f"Consumed DB table. Produced by {producer.slug}." if producer else "Consumed DB table."
        out.append({"name": table, "kind": "table", "description": desc})
    return out


def build_mermaid_page(page: Page, table_lookup: dict[str, Page]) -> str:
    """Build a simple data-lineage diagram for one page."""
    lines = ["flowchart LR"]
    node_self = page.slug.replace("-", "_")
    lines.append(f"  {node_self}[\"{page.title}\"]")

    for idx, file_item in enumerate(page.manifest.get("files", []), start=1):
        node = f"f{idx}_{node_self}"
        label = file_item.get("path", "file")
        lines.append(f"  {node}[\"{label}\"] --> {node_self}")

    for idx, api_item in enumerate(page.manifest.get("apis", []), start=1):
        node = f"a{idx}_{node_self}"
        label = api_item.get("name", "API")
        lines.append(f"  {node}[\"{label}\"] --> {node_self}")

    for table in page.manifest.get("tables", []):
        producer = table_lookup.get(table)
        table_node = f"t_{table.replace('-', '_')}"
        lines.append(f"  {table_node}[\"{table}\"] --> {node_self}")
        if producer:
            prod_node = producer.slug.replace("-", "_")
            lines.append(f"  {prod_node}[\"{producer.title}\"] --> {table_node}")

    for table in page.manifest.get("tables_produced", []):
        table_name = table.get("name") if isinstance(table, dict) else str(table)
        table_node = f"tp_{table_name.replace('-', '_')}"
        lines.append(f"  {node_self} --> {table_node}[\"{table_name}\"]")

    return "\n".join(lines)


def collect_output_images(page: Page) -> list[dict[str, str]]:
    """Copy output images to website output and return render metadata."""
    src_dir = PROJECT_ROOT / page.rel_dir / "output"
    if not src_dir.exists():
        return []
    images = []
    kind_path = "analyses" if page.kind == "analysis" else page.kind
    dest_dir = OUTPUT_DIR / "assets" / kind_path / page.slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(src_dir.iterdir()):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg"}:
            continue
        target = dest_dir / path.name
        shutil.copy2(path, target)
        images.append(
            {
                "src": f"assets/{kind_path}/{page.slug}/{path.name}",
                "alt": path.stem,
                "label": path.name,
            }
        )
    return images


def write_css() -> None:
    """Write stylesheet for generated pages."""
    css = """
body { font-family: Georgia, 'Times New Roman', serif; margin: 0; background: #f7f3ea; color: #1e1e1e; }
.site-nav { display: flex; gap: 1rem; padding: 1rem; background: #12343b; color: #fff; flex-wrap: wrap; }
.site-nav a { color: #fff; text-decoration: none; }
.site-nav .brand { font-weight: 700; margin-right: 1rem; }
.container { max-width: 1000px; margin: 0 auto; padding: 1.5rem; }
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
img { max-width: 100%; height: auto; border: 1px solid #ddd; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
th, td { border: 1px solid #bbb; padding: 0.5rem; text-align: left; }
.markdown p { line-height: 1.6; }
pre.mermaid { overflow-x: auto; background: #fff; padding: 0.5rem; border: 1px solid #ddd; }
"""
    (OUTPUT_DIR / "style.css").write_text(css.strip() + "\n", encoding="utf-8")


def main() -> None:
    """Generate full static site output."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

    pages = discover_pages()
    table_lookup = build_table_lookup(pages)

    site_items = []
    source_index: dict[tuple[str, str], dict] = {}

    for page in pages:
        kind_path = "analyses" if page.kind == "analysis" else page.kind
        page_dir = OUTPUT_DIR / kind_path / page.slug
        page_dir.mkdir(parents=True, exist_ok=True)

        findings_html = md_to_html(PROJECT_ROOT / page.rel_dir / "FINDINGS.md")
        methods_html = md_to_html(PROJECT_ROOT / page.rel_dir / "METHODS.md")
        output_images = collect_output_images(page)
        sources = page_sources(page, table_lookup)
        mermaid = build_mermaid_page(page, table_lookup)

        html = env.get_template("page.html").render(
            root="../../",
            page=page,
            findings_html=findings_html,
            methods_html=methods_html,
            output_images=output_images,
            page_sources=sources,
            mermaid_diagram=mermaid,
        )
        (page_dir / "index.html").write_text(html, encoding="utf-8")

        rel_path = f"{kind_path}/{page.slug}/index.html"
        site_items.append({"title": page.title, "path": rel_path, "group": page.group})

        for src in sources:
            key = (src["kind"], src["name"])
            entry = source_index.setdefault(
                key,
                {
                    "kind": src["kind"],
                    "name": src["name"],
                    "description": src["description"],
                    "consumers": [],
                },
            )
            entry["consumers"].append({"title": page.title, "path": rel_path})

    pipeline_items = sorted([i for i in site_items if i["path"].startswith("pipeline/")], key=lambda x: x["path"])
    analysis_items = sorted([i for i in site_items if i["path"].startswith("analyses/")], key=lambda x: x["path"])

    index_html = env.get_template("index.html").render(root="", pipeline=pipeline_items, analyses=analysis_items)
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
        )
        (OUTPUT_DIR / source["path"]).write_text(html, encoding="utf-8")

    sources_html = env.get_template("sources.html").render(root="", sources=source_list)
    (OUTPUT_DIR / "sources.html").write_text(sources_html, encoding="utf-8")

    glossary_data = read_yaml(Path(__file__).resolve().parent / "glossary.yaml")
    glossary_html = env.get_template("glossary.html").render(
        root="",
        categories=glossary_data.get("categories", []),
    )
    (OUTPUT_DIR / "glossary.html").write_text(glossary_html, encoding="utf-8")

    write_css()
    print(f"Generated website output at {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
