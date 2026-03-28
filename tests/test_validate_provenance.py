"""Tests for the provenance validation tool."""

import sys
import textwrap
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.validate_provenance import validate_analysis, validate_pipeline, ValidationResult


@pytest.fixture
def tmp_analysis(tmp_path):
    """Create a minimal valid analysis directory."""
    d = tmp_path / "01_example"
    d.mkdir()
    out = d / "output"
    out.mkdir()
    # Create actual output files
    (out / "chart.png").write_text("fake")
    (out / "results.csv").write_text("fake")

    (d / "main.py").write_text(
        textwrap.dedent("""\
        \"\"\"Example analysis.\"\"\"
        import polars

        SQL = \"\"\"SELECT * FROM otp_monthly\"\"\"
        """)
    )
    (d / "README.md").write_text("# Example\\nDoes a thing.")
    (d / "SOURCES.yaml").write_text(
        yaml.safe_dump(
            {
                "kind": "analysis",
                "title": "01 - Example",
                "description": "Does a thing.",
                "group": "Core OTP Patterns",
                "tables": ["otp_monthly"],
                "files": [],
                "dependencies": ["polars"],
                "analyses": [],
                "outputs": [
                    {"path": "chart.png", "kind": "image", "description": "A chart."},
                    {"path": "results.csv", "kind": "data", "description": "Results."},
                ],
            }
        )
    )
    return d


@pytest.fixture
def tmp_pipeline(tmp_path):
    """Create a minimal valid pipeline directory."""
    d = tmp_path / "01_ingest"
    d.mkdir()
    out = d / "output"
    out.mkdir()
    (d / "main.py").write_text('"""Ingest."""\n')
    (d / "README.md").write_text("# Ingest\\nIngests data.")
    (d / "SOURCES.yaml").write_text(
        yaml.safe_dump(
            {
                "kind": "pipeline",
                "title": "Data Ingestion",
                "description": "Ingests data.",
                "files": [{"path": "data/foo.csv", "description": "Input."}],
                "apis": [],
                "tables": [],
                "tables_produced": [
                    {"name": "otp_monthly", "description": "Monthly OTP."},
                ],
            }
        )
    )
    return d


class TestAnalysisValidation:
    def test_valid_analysis_has_no_errors(self, tmp_analysis):
        result = validate_analysis(tmp_analysis)
        assert result.errors == [], f"Unexpected errors: {result.errors}"

    def test_missing_required_field_kind(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["kind"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("kind" in e for e in result.errors)

    def test_missing_required_field_title(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["title"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("title" in e for e in result.errors)

    def test_missing_description(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["description"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("description" in e for e in result.errors)

    def test_missing_group(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["group"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("group" in e for e in result.errors)

    def test_missing_outputs_field(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["outputs"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("outputs" in e for e in result.errors)

    def test_output_missing_kind(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        del sources["outputs"][0]["kind"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("kind" in e for e in result.errors)

    def test_output_missing_description(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["outputs"][0]["description"] = ""
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("description" in e for e in result.errors)

    def test_undeclared_output_file(self, tmp_analysis):
        """A file exists in output/ but isn't declared in SOURCES.yaml."""
        (tmp_analysis / "output" / "surprise.png").write_text("fake")
        result = validate_analysis(tmp_analysis)
        assert any("surprise.png" in e for e in result.errors)

    def test_declared_output_file_missing(self, tmp_analysis):
        """SOURCES.yaml declares an output that doesn't exist on disk."""
        (tmp_analysis / "output" / "chart.png").unlink()
        result = validate_analysis(tmp_analysis)
        assert any("chart.png" in e for e in result.errors)

    def test_gitkeep_and_pycache_ignored(self, tmp_analysis):
        """__pycache__ and .gitkeep should not trigger undeclared warnings."""
        (tmp_analysis / "output" / ".gitkeep").write_text("")
        (tmp_analysis / "output" / "__pycache__").mkdir()
        result = validate_analysis(tmp_analysis)
        assert result.errors == []

    def test_cross_ref_must_be_dict(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["analyses"] = ["36_national_ridership_growth"]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("dict" in e.lower() or "mapping" in e.lower() for e in result.errors)

    def test_cross_ref_missing_relationship(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["analyses"] = [{"id": 2}]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("relationship" in e for e in result.errors)

    def test_cross_ref_missing_id(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["analyses"] = [{"relationship": "related"}]
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("id" in e for e in result.errors)

    def test_warnings_for_empty_tables(self, tmp_analysis):
        """An analysis with SQL but empty tables list should warn."""
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["tables"] = []
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("tables" in w for w in result.warnings)

    def test_no_false_sql_warning_from_python_keywords(self, tmp_analysis):
        """Polars .select() and 'from pathlib' should not trigger SQL warning."""
        (tmp_analysis / "main.py").write_text(
            '"""Example."""\nfrom pathlib import Path\nimport polars\ndf.select("col")\n'
        )
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["tables"] = []
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert not any("tables" in w for w in result.warnings)

    def test_warnings_for_empty_dependencies(self, tmp_analysis):
        sources = yaml.safe_load((tmp_analysis / "SOURCES.yaml").read_text())
        sources["dependencies"] = []
        (tmp_analysis / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_analysis(tmp_analysis)
        assert any("dependencies" in w for w in result.warnings)


class TestPipelineValidation:
    def test_valid_pipeline_has_no_errors(self, tmp_pipeline):
        result = validate_pipeline(tmp_pipeline)
        assert result.errors == [], f"Unexpected errors: {result.errors}"

    def test_missing_tables_produced(self, tmp_pipeline):
        sources = yaml.safe_load((tmp_pipeline / "SOURCES.yaml").read_text())
        del sources["tables_produced"]
        (tmp_pipeline / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_pipeline(tmp_pipeline)
        assert any("tables_produced" in e for e in result.errors)

    def test_tables_produced_entry_missing_description(self, tmp_pipeline):
        sources = yaml.safe_load((tmp_pipeline / "SOURCES.yaml").read_text())
        sources["tables_produced"] = [{"name": "foo"}]
        (tmp_pipeline / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_pipeline(tmp_pipeline)
        assert any("description" in e for e in result.errors)

    def test_tables_produced_string_entry(self, tmp_pipeline):
        sources = yaml.safe_load((tmp_pipeline / "SOURCES.yaml").read_text())
        sources["tables_produced"] = ["otp_monthly"]
        (tmp_pipeline / "SOURCES.yaml").write_text(yaml.safe_dump(sources))
        result = validate_pipeline(tmp_pipeline)
        assert any("dict" in e.lower() or "mapping" in e.lower() for e in result.errors)
