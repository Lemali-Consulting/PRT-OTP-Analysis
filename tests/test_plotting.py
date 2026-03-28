"""Tests for shared plotting constants and utilities."""

import polars as pl

from prt_otp_analysis.common.plotting import (
    BUS_TYPE_COLORS,
    COLOR_GOOD,
    COLOR_GRAY,
    COLOR_NEGATIVE,
    COLOR_PRIMARY,
    COLOR_WARNING,
    MODE_COLORS,
    mode_scatter,
    setup_plotting,
)


class TestModeColors:
    def test_has_all_modes(self):
        assert set(MODE_COLORS.keys()) == {"BUS", "RAIL", "INCLINE", "UNKNOWN"}

    def test_values_are_hex(self):
        for color in MODE_COLORS.values():
            assert color.startswith("#") and len(color) == 7


class TestBusTypeColors:
    def test_has_all_bus_types(self):
        assert set(BUS_TYPE_COLORS.keys()) == {
            "local",
            "limited",
            "express",
            "busway",
            "flyer",
        }

    def test_values_are_hex(self):
        for color in BUS_TYPE_COLORS.values():
            assert color.startswith("#") and len(color) == 7


class TestSemanticColors:
    def test_all_are_hex_strings(self):
        for color in [COLOR_PRIMARY, COLOR_NEGATIVE, COLOR_GOOD, COLOR_WARNING, COLOR_GRAY]:
            assert isinstance(color, str)
            assert color.startswith("#") and len(color) == 7

    def test_distinct(self):
        colors = {COLOR_PRIMARY, COLOR_NEGATIVE, COLOR_GOOD, COLOR_WARNING, COLOR_GRAY}
        assert len(colors) == 5, "Semantic colors must be distinct"


class TestSetupPlotting:
    def test_returns_plt(self):
        plt = setup_plotting()
        assert hasattr(plt, "subplots")
        assert plt.rcParams["axes.spines.top"] is False
        assert plt.rcParams["axes.spines.right"] is False


def _sample_df(n_bus: int = 10, n_rail: int = 3) -> pl.DataFrame:
    """Build a small synthetic DataFrame with mode, x, and y columns."""
    import random
    random.seed(42)
    rows: list[dict] = []
    for i in range(n_bus):
        rows.append({"mode": "BUS", "x": float(i), "y": 0.5 + 0.02 * i + random.gauss(0, 0.05)})
    for i in range(n_rail):
        rows.append({"mode": "RAIL", "x": float(i), "y": 0.7 + random.gauss(0, 0.05)})
    return pl.DataFrame(rows)


class TestModeScatter:
    def test_draws_scatter_and_trendline(self):
        plt = setup_plotting()
        fig, ax = plt.subplots()
        df = _sample_df()
        result = mode_scatter(ax, df, "x", "y")
        plt.close(fig)

        # Should have scatter collections for BUS + RAIL, plus trendline line
        assert len(ax.collections) >= 2  # at least 2 scatter series
        assert len(ax.lines) >= 1  # trendline
        assert result is not None
        assert "r" in result and "p" in result

    def test_no_trend(self):
        plt = setup_plotting()
        fig, ax = plt.subplots()
        df = _sample_df()
        result = mode_scatter(ax, df, "x", "y", trend=False)
        plt.close(fig)

        assert result is None
        assert len(ax.lines) == 0  # no trendline

    def test_too_few_bus_points_returns_none(self):
        plt = setup_plotting()
        fig, ax = plt.subplots()
        df = _sample_df(n_bus=2, n_rail=3)
        result = mode_scatter(ax, df, "x", "y", min_n=3)
        plt.close(fig)

        assert result is None
        assert len(ax.lines) == 0

    def test_skips_empty_modes(self):
        plt = setup_plotting()
        fig, ax = plt.subplots()
        df = _sample_df(n_bus=5, n_rail=0)
        result = mode_scatter(ax, df, "x", "y")
        plt.close(fig)

        # Only BUS scatter, no RAIL
        assert len(ax.collections) == 1
        assert result is not None
