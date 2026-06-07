"""Validation tests for pipeline manifest table metadata."""

from pathlib import Path
import importlib.util
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
ANALYSES_DIR = PROJECT_ROOT / "analyses"
WEBSITE_MAIN = PROJECT_ROOT / "products" / "website" / "main.py"

spec = importlib.util.spec_from_file_location("website_main_pipeline", WEBSITE_MAIN)
assert spec is not None
assert spec.loader is not None
website_main = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = website_main
spec.loader.exec_module(website_main)


def _pipeline_source_paths() -> list[Path]:
    """Return all pipeline SOURCES.yaml paths."""
    return sorted(PIPELINE_DIR.glob("*/SOURCES.yaml"))


def _consumed_tables_source_paths() -> list[Path]:
    """Return every SOURCES.yaml (pipeline + analysis) that may list consumed tables."""
    return sorted(PIPELINE_DIR.glob("*/SOURCES.yaml")) + sorted(
        ANALYSES_DIR.glob("*/SOURCES.yaml")
    )


def test_consumed_tables_are_bare_strings():
    """Consumed `tables:` entries must be bare strings, never dict-format.

    A dict in `tables:` crashes the website build (`page_sources` uses each entry
    as a dict key: "cannot use 'dict' as a dict key"). Only `tables_produced:`
    uses dict-format (name/description). This guards against that mismatch, which
    the website build catches only at deploy time.
    """
    for path in _consumed_tables_source_paths():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tables = data.get("tables", [])
        assert isinstance(tables, list), f"{path} tables must be a list"
        for idx, item in enumerate(tables, start=1):
            assert isinstance(item, str), (
                f"{path} tables[{idx}] must be a bare string (e.g. '- stops'), "
                f"not {type(item).__name__}; dict-format is only for tables_produced"
            )


def test_pipeline_tables_produced_have_name_and_description():
    """Every pipeline tables_produced entry must have name and description."""
    for path in _pipeline_source_paths():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        tables = data.get("tables_produced", [])
        assert isinstance(tables, list), f"{path} tables_produced must be a list"
        assert tables, f"{path} must define at least one tables_produced entry"
        for idx, item in enumerate(tables, start=1):
            assert isinstance(item, dict), f"{path} tables_produced[{idx}] must be a mapping"
            name = str(item.get("name", "")).strip()
            desc = str(item.get("description", "")).strip()
            assert name, f"{path} tables_produced[{idx}] missing name"
            assert desc, f"{path} tables_produced[{idx}] missing description"


def test_website_pipeline_manifest_validation_has_no_errors():
    """Website validation helper should accept current pipeline manifests."""
    pages = website_main.discover_pages()
    errors = website_main.validate_pipeline_manifests(pages)
    assert not errors, "Pipeline manifest validation errors:\n" + "\n".join(errors)
