"""Validation tests for pipeline manifest table metadata."""

from pathlib import Path
import importlib.util
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
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
