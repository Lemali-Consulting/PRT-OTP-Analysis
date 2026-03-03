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
