"""Tests for shared plotting constants and utilities."""

from prt_otp_analysis.common.plotting import (
    BUS_TYPE_COLORS,
    COLOR_GOOD,
    COLOR_GRAY,
    COLOR_NEGATIVE,
    COLOR_PRIMARY,
    COLOR_WARNING,
    MODE_COLORS,
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
