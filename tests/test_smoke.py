"""Smoke tests: validate project structure and analysis imports."""

import importlib
import importlib.util
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DIR = PROJECT_ROOT / "analyses"


def _find_analyses() -> list[Path]:
    """Discover all analysis main.py files."""
    return sorted(ANALYSES_DIR.glob("*/main.py"))


class TestCommon:
    """Tests for shared utilities in prt_otp_analysis.common."""

    def test_import_common(self):
        mod = importlib.import_module("prt_otp_analysis.common")
        assert hasattr(mod, "get_db")
        assert hasattr(mod, "output_dir")
        assert hasattr(mod, "query_to_polars")
        assert hasattr(mod, "setup_plotting")


class TestAnalysesStructure:
    """Verify each analysis directory has scaffold-required files."""

    REQUIRED_FILES = ["README.md", "METHODS.md", "FINDINGS.md", "main.py", "SOURCES.yaml"]

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_required_files_exist(self, main_py: Path):
        analysis_dir = main_py.parent
        for filename in self.REQUIRED_FILES:
            assert (analysis_dir / filename).exists(), (
                f"{analysis_dir.name} missing {filename}"
            )

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_output_dir_exists(self, main_py: Path):
        assert (main_py.parent / "output").is_dir(), (
            f"{main_py.parent.name} missing output/ directory"
        )

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_methods_has_four_sections(self, main_py: Path):
        methods = (main_py.parent / "METHODS.md").read_text(encoding="utf-8")
        for section in ["## Question", "## Approach", "## Data", "## Output"]:
            assert section in methods, (
                f"{main_py.parent.name}/METHODS.md missing '{section}'"
            )


class TestAnalysesImport:
    """Verify each analysis main.py imports without crashing."""

    @pytest.mark.parametrize("main_py", _find_analyses(), ids=lambda p: p.parent.name)
    def test_analysis_imports(self, main_py: Path):
        spec = importlib.util.spec_from_file_location(
            f"analysis_{main_py.parent.name}", main_py
        )
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
