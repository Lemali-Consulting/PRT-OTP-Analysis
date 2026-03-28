"""Unit tests for prt_otp_analysis.common.stats utilities."""

import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest


class TestWeightedMean:
    """Tests for the weighted_mean Polars expression builder."""

    def test_basic_weighted_mean(self):
        from prt_otp_analysis.common import weighted_mean

        df = pl.DataFrame({"val": [80.0, 90.0], "wt": [3.0, 1.0]})
        result = df.select(weighted_mean("val", "wt").alias("wm"))
        # (80*3 + 90*1) / (3+1) = 330/4 = 82.5
        assert result["wm"][0] == pytest.approx(82.5)

    def test_equal_weights_equals_mean(self):
        from prt_otp_analysis.common import weighted_mean

        df = pl.DataFrame({"val": [10.0, 20.0, 30.0], "wt": [1.0, 1.0, 1.0]})
        result = df.select(weighted_mean("val", "wt").alias("wm"))
        assert result["wm"][0] == pytest.approx(20.0)

    def test_safe_mode_zero_weights_falls_back_to_mean(self):
        from prt_otp_analysis.common import weighted_mean

        df = pl.DataFrame({"val": [10.0, 20.0, 30.0], "wt": [0.0, 0.0, 0.0]})
        result = df.select(weighted_mean("val", "wt", safe=True).alias("wm"))
        assert result["wm"][0] == pytest.approx(20.0)

    def test_unsafe_mode_zero_weights_returns_nan_or_inf(self):
        from prt_otp_analysis.common import weighted_mean

        df = pl.DataFrame({"val": [10.0, 20.0], "wt": [0.0, 0.0]})
        result = df.select(weighted_mean("val", "wt", safe=False).alias("wm"))
        # Division by zero → NaN or inf
        assert result["wm"][0] is None or not math.isfinite(result["wm"][0])

    def test_works_inside_group_by(self):
        from prt_otp_analysis.common import weighted_mean

        df = pl.DataFrame({
            "grp": ["a", "a", "b", "b"],
            "val": [100.0, 200.0, 50.0, 50.0],
            "wt": [1.0, 3.0, 1.0, 1.0],
        })
        result = (
            df.group_by("grp")
            .agg(weighted_mean("val", "wt").alias("wm"))
            .sort("grp")
        )
        # a: (100*1 + 200*3) / 4 = 175
        # b: (50*1 + 50*1) / 2 = 50
        assert result["wm"][0] == pytest.approx(175.0)
        assert result["wm"][1] == pytest.approx(50.0)


class TestCorrelate:
    """Tests for the correlate and correlate_by_mode functions."""

    def test_perfect_positive_correlation(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0], "y": [2.0, 4.0, 6.0, 8.0, 10.0]})
        result = correlate(df, "x", "y")
        assert result["pearson_r"] == pytest.approx(1.0)
        assert result["spearman_r"] == pytest.approx(1.0)
        assert result["n"] == 5

    def test_negative_correlation(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [10.0, 8.0, 6.0, 4.0]})
        result = correlate(df, "x", "y")
        assert result["pearson_r"] == pytest.approx(-1.0)

    def test_min_n_guard_returns_nan(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        result = correlate(df, "x", "y", min_n=3)
        assert math.isnan(result["pearson_r"])
        assert math.isnan(result["spearman_r"])
        assert result["n"] == 2

    def test_nulls_are_dropped(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({
            "x": [1.0, 2.0, None, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],
        })
        result = correlate(df, "x", "y")
        assert result["n"] == 4
        assert result["pearson_r"] == pytest.approx(1.0)

    def test_prefix_flattens_keys(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({"x": [1.0, 2.0, 3.0], "y": [2.0, 4.0, 6.0]})
        result = correlate(df, "x", "y", prefix="bus_span")
        assert "bus_span_pearson_r" in result
        assert "bus_span_pearson_p" in result
        assert "bus_span_spearman_r" in result
        assert "bus_span_spearman_p" in result
        assert "bus_span_n" in result
        assert result["bus_span_pearson_r"] == pytest.approx(1.0)
        # Original keys should not be present
        assert "pearson_r" not in result

    def test_prefix_min_n_guard(self):
        from prt_otp_analysis.common import correlate

        df = pl.DataFrame({"x": [1.0, 2.0], "y": [3.0, 4.0]})
        result = correlate(df, "x", "y", prefix="foo", min_n=3)
        assert math.isnan(result["foo_pearson_r"])
        assert result["foo_n"] == 2

    def test_correlate_by_mode_returns_flat(self):
        from prt_otp_analysis.common import correlate_by_mode

        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0],
            "mode": ["BUS", "BUS", "BUS", "BUS", "RAIL", "RAIL"],
        })
        result = correlate_by_mode(df, "x", "y")
        assert result["all_n"] == 6
        assert result["bus_n"] == 4
        assert result["all_pearson_r"] == pytest.approx(1.0)
        assert result["bus_pearson_r"] == pytest.approx(1.0)
        assert result["bus_spearman_r"] == pytest.approx(1.0)


class TestGini:
    """Tests for the Gini coefficient function."""

    def test_perfect_equality(self):
        from prt_otp_analysis.common import gini

        # All equal values → Gini = 0
        assert gini([10.0, 10.0, 10.0, 10.0]) == pytest.approx(0.0)

    def test_maximum_inequality(self):
        from prt_otp_analysis.common import gini

        # One person has everything → Gini approaches (n-1)/n
        result = gini([0.0, 0.0, 0.0, 100.0])
        assert result == pytest.approx(0.75, abs=0.01)

    def test_known_value(self):
        from prt_otp_analysis.common import gini

        # [1, 2, 3, 4, 5] → known Gini ≈ 0.2667
        result = gini([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result == pytest.approx(0.2667, abs=0.001)

    def test_nan_values_ignored(self):
        from prt_otp_analysis.common import gini

        assert gini([10.0, float("nan"), 10.0, 10.0]) == pytest.approx(0.0)

    def test_too_few_values_returns_nan(self):
        from prt_otp_analysis.common import gini

        assert math.isnan(gini([5.0]))
        assert math.isnan(gini([]))

    def test_all_zeros_returns_nan(self):
        from prt_otp_analysis.common import gini

        assert math.isnan(gini([0.0, 0.0, 0.0]))


class TestSaveCsv:
    """Tests for the save_csv output helper."""

    def test_writes_csv_file(self, tmp_path):
        from prt_otp_analysis.common import save_csv

        df = pl.DataFrame({"a": [1, 2], "b": [3, 4]})
        out = save_csv(df, tmp_path / "test.csv", quiet=True)
        assert out.exists()
        loaded_df = pl.read_csv(out)
        assert loaded_df.shape == (2, 2)
        assert loaded_df["a"].to_list() == [1, 2]

    def test_returns_path(self, tmp_path):
        from prt_otp_analysis.common import save_csv

        df = pl.DataFrame({"x": [1]})
        result = save_csv(df, tmp_path / "out.csv", quiet=True)
        assert isinstance(result, Path)
        assert result == tmp_path / "out.csv"

    def test_prints_logging(self, tmp_path, capsys):
        from prt_otp_analysis.common import save_csv

        df = pl.DataFrame({"x": [1]})
        save_csv(df, tmp_path / "logged.csv")
        captured = capsys.readouterr()
        assert "logged.csv" in captured.out
