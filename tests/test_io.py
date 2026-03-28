"""Tests for prt_otp_analysis.common.io helpers."""

import io
import sys
from pathlib import Path
from unittest.mock import patch

from prt_otp_analysis.common.io import analysis_dir, phase, run_analysis


class TestAnalysisDir:
    """Tests for the analysis_dir() path helper."""

    def test_returns_output_subdir(self, tmp_path: Path) -> None:
        """Returns an 'output' subdirectory under the caller's file parent."""
        fake_file = tmp_path / "main.py"
        fake_file.touch()
        result = analysis_dir(str(fake_file))
        assert result == tmp_path / "output"

    def test_creates_output_dir(self, tmp_path: Path) -> None:
        """Creates the output directory if it doesn't exist."""
        fake_file = tmp_path / "main.py"
        fake_file.touch()
        result = analysis_dir(str(fake_file))
        assert result.is_dir()

    def test_returns_path_object(self, tmp_path: Path) -> None:
        """Return type is a Path."""
        fake_file = tmp_path / "main.py"
        fake_file.touch()
        result = analysis_dir(str(fake_file))
        assert isinstance(result, Path)


class TestRunAnalysis:
    """Tests for the run_analysis() decorator."""

    def test_prints_header_and_done(self) -> None:
        """Decorator prints header before and 'Done.' after the function."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):

            @run_analysis(7, "Test Analysis")
            def my_main() -> None:
                print("body")

            my_main()

        output = buf.getvalue()
        lines = output.strip().split("\n")
        # Header should be first
        assert "Analysis 7: Test Analysis" in output
        # Body should appear
        assert "body" in output
        # Done should be last
        assert lines[-1].strip() == "Done."

    def test_preserves_return_value(self) -> None:
        """Decorator passes through the wrapped function's return value."""

        @run_analysis(1, "Return Test")
        def my_main() -> int:
            return 42

        with patch("sys.stdout", io.StringIO()):
            result = my_main()
        assert result == 42

    def test_preserves_function_name(self) -> None:
        """Decorator preserves __name__ via functools.wraps."""

        @run_analysis(1, "Name Test")
        def my_main() -> None:
            pass

        assert my_main.__name__ == "my_main"


class TestPhase:
    """Tests for the phase() context manager."""

    def test_prints_label_with_ellipsis(self) -> None:
        """phase() prints a newline, the label, and '...' on entry."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with phase("Loading data"):
                pass
        assert buf.getvalue() == "\nLoading data...\n"

    def test_body_output_follows_label(self) -> None:
        """Output inside the phase block appears after the label."""
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            with phase("Analyzing"):
                print("  Pearson r = 0.42")
        output = buf.getvalue()
        assert output.index("Analyzing...") < output.index("Pearson r = 0.42")
