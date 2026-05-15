"""Website output surfacing and manifest coverage checks."""

from pathlib import Path
import importlib.util
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEBSITE_MAIN = PROJECT_ROOT / "products" / "website" / "main.py"

spec = importlib.util.spec_from_file_location("website_main", WEBSITE_MAIN)
assert spec is not None
assert spec.loader is not None
website_main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = website_main
spec.loader.exec_module(website_main)
Page = website_main.Page
collect_outputs = website_main.collect_outputs
discover_pages = website_main.discover_pages
build_table_lookup = website_main.build_table_lookup
build_table_upstream = website_main.build_table_upstream
build_table_descriptions = website_main.build_table_descriptions
build_mermaid_page = website_main.build_mermaid_page
page_sources = website_main.page_sources


def _analysis_source_paths() -> list[Path]:
    """Return all analysis SOURCES.yaml paths."""
    return sorted((PROJECT_ROOT / "analyses").glob("*/SOURCES.yaml"))


def test_all_analyses_declare_outputs():
    """Every analysis manifest should declare at least one output artifact."""
    for path in _analysis_source_paths():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        outputs = data.get("outputs", [])
        assert isinstance(outputs, list), f"{path} outputs must be a list"
        assert outputs, f"{path} must declare at least one output artifact"
        for item in outputs:
            assert isinstance(item, dict), f"{path} outputs entries must be maps"
            assert item.get("path"), f"{path} outputs entry missing path"
            assert item.get("kind"), f"{path} outputs entry missing kind"


def test_declared_outputs_exist_on_disk():
    """Each declared analysis output should exist under output/."""
    for path in _analysis_source_paths():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        output_dir = path.parent / "output"
        for item in data.get("outputs", []):
            rel = item["path"]
            artifact = output_dir / rel
            assert artifact.exists(), f"Missing declared output: {artifact}"
            assert artifact.is_file(), f"Declared output is not a file: {artifact}"


def test_website_collection_reports_no_analysis_output_errors():
    """Website collector should surface all declared analysis artifacts cleanly."""
    pages = [p for p in discover_pages() if p.kind == "analysis"]
    assert pages, "No analysis pages discovered"
    errors: list[str] = []
    for page in pages:
        artifacts, page_errors = collect_outputs(page)
        errors.extend(page_errors)
        assert artifacts, f"{page.rel_dir} should surface at least one artifact"
    assert not errors, "Output collection errors:\n" + "\n".join(errors)


def test_collect_outputs_flags_missing_declared_file(tmp_path: Path):
    """Collector should return an error when manifest declares a missing output file."""
    page = Page(
        kind="analysis",
        title="Test",
        slug="test_missing",
        rel_dir=str(tmp_path),
        group=None,
        manifest={"outputs": [{"path": "missing.png", "kind": "image"}]},
    )
    artifacts, errors = collect_outputs(page)
    assert not artifacts
    assert errors


# --- Home page table helper tests ---


def test_analysis_number_extracts_leading_digits():
    """analysis_number returns the integer prefix of an analysis slug."""
    assert website_main.analysis_number("01_system_trend") == 1
    assert website_main.analysis_number("48_service_productivity") == 48
    assert website_main.analysis_number("no_number_here") == 0


def test_strip_leading_number_removes_numbered_prefix():
    """strip_leading_number drops a 'NN -', 'NN:' or 'NN —' title prefix."""
    assert website_main.strip_leading_number("01 - System-Wide OTP Trend") == "System-Wide OTP Trend"
    assert website_main.strip_leading_number("06: Seasonal Patterns") == "Seasonal Patterns"
    assert (
        website_main.strip_leading_number("39 — National Service Cuts (2019 vs 2024)")
        == "National Service Cuts (2019 vs 2024)"
    )
    assert website_main.strip_leading_number("No Prefix Here") == "No Prefix Here"


def test_split_summary_separates_lead_sentence():
    """split_summary returns the first sentence and the remaining text."""
    lead, rest = website_main.split_summary("First sentence here. Second part follows. Third.")
    assert lead == "First sentence here."
    assert rest == "Second part follows. Third."
    lead, rest = website_main.split_summary("Only one sentence here.")
    assert (lead, rest) == ("Only one sentence here.", "")
    assert website_main.split_summary("") == ("", "")
    # A decimal point mid-sentence must not be treated as a sentence boundary.
    lead, rest = website_main.split_summary("Productivity fell to 18.5 riders per hour.")
    assert lead == "Productivity fell to 18.5 riders per hour."
    assert rest == ""


# --- Provenance chain tests ---


def _make_pipeline_page() -> Page:
    return Page(
        kind="pipeline",
        title="Data Ingestion",
        slug="01_data_ingestion",
        rel_dir="pipeline/01_data_ingestion",
        group=None,
        manifest={
            "files": [
                {"path": "data/routes.csv", "description": "Route CSV."},
                {"path": "data/stops.csv", "description": "Stop CSV."},
            ],
            "apis": [
                {"name": "WPRDC API", "url": "https://data.wprdc.org", "description": "Public dataset."},
            ],
            "tables_produced": [
                {"name": "routes", "description": "Route dimension table."},
                {"name": "otp_monthly", "description": "Monthly OTP values."},
            ],
        },
    )


def _make_analysis_page() -> Page:
    return Page(
        kind="analysis",
        title="System Trend",
        slug="01_system_trend",
        rel_dir="analyses/01_system_trend",
        group="Performance",
        manifest={
            "tables": ["routes", "otp_monthly"],
            "dependencies": ["polars"],
        },
    )


def test_build_table_upstream_maps_tables_to_raw_sources():
    """build_table_upstream returns files and APIs for each produced table."""
    pipeline = _make_pipeline_page()
    upstream = build_table_upstream([pipeline])
    assert "routes" in upstream
    assert "otp_monthly" in upstream
    names = [s["name"] for s in upstream["routes"]]
    assert "data/routes.csv" in names
    assert "data/stops.csv" in names
    assert "WPRDC API" in names
    kinds = {s["kind"] for s in upstream["routes"]}
    assert kinds == {"file", "api"}


def test_mermaid_includes_upstream_sources():
    """Mermaid diagram should show upstream files/APIs feeding into the pipeline node."""
    pipeline = _make_pipeline_page()
    analysis = _make_analysis_page()
    pages = [pipeline, analysis]
    table_lookup = build_table_lookup(pages)
    table_upstream = build_table_upstream(pages)
    mermaid = build_mermaid_page(analysis, table_lookup, table_upstream)
    assert "data/routes.csv" in mermaid
    assert "data/stops.csv" in mermaid
    assert "WPRDC API" in mermaid
    assert "Data Ingestion" in mermaid


def test_mermaid_without_upstream_still_works():
    """Mermaid diagram should work when table_upstream is None (backward compat)."""
    pipeline = _make_pipeline_page()
    analysis = _make_analysis_page()
    table_lookup = build_table_lookup([pipeline, analysis])
    mermaid = build_mermaid_page(analysis, table_lookup)
    assert "Data Ingestion" in mermaid
    assert "data/routes.csv" not in mermaid


def test_page_sources_includes_upstream_for_tables():
    """page_sources should attach upstream list to table source entries."""
    pipeline = _make_pipeline_page()
    analysis = _make_analysis_page()
    pages = [pipeline, analysis]
    table_lookup = build_table_lookup(pages)
    table_descriptions = build_table_descriptions(pages)
    table_upstream = build_table_upstream(pages)
    sources = page_sources(analysis, table_lookup, table_descriptions, table_upstream)
    table_entries = [s for s in sources if s["kind"] == "table"]
    assert len(table_entries) == 2
    for entry in table_entries:
        assert "upstream" in entry
        assert len(entry["upstream"]) == 3
        upstream_names = [u["name"] for u in entry["upstream"]]
        assert "data/routes.csv" in upstream_names


def test_page_sources_without_upstream_has_no_key():
    """page_sources without table_upstream should not add upstream key to non-table entries."""
    pipeline = _make_pipeline_page()
    analysis = _make_analysis_page()
    pages = [pipeline, analysis]
    table_lookup = build_table_lookup(pages)
    table_descriptions = build_table_descriptions(pages)
    sources = page_sources(analysis, table_lookup, table_descriptions)
    dep_entries = [s for s in sources if s["kind"] == "dependency"]
    assert dep_entries
    for entry in dep_entries:
        assert "upstream" not in entry
