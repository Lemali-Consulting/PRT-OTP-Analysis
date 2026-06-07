"""Unit tests for the PRT stop-signal classification ETL pure functions."""

import pytest

from prt_otp_analysis.stop_signals import classify_signal, has_signal


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("BUS (NO SIGNAL)", "none"),
        ("BUS (SIGNAL-NEARSIDE)", "nearside"),
        ("BUS (SIGNAL-FARSIDE)", "farside"),
        ("BUSWAY/BRT", "busway"),
        # Whitespace / case robustness for hand-maintained source data.
        ("  bus (signal-nearside)  ", "nearside"),
    ],
)
def test_classify_signal(mode, expected):
    """Each PRT mode string maps to its canonical signal class."""
    assert classify_signal(mode) == expected


def test_classify_signal_unknown_raises():
    """An unrecognized mode is a data-quality error, not silently bucketed."""
    with pytest.raises(ValueError):
        classify_signal("BUS (SOMETHING NEW)")


@pytest.mark.parametrize(
    "signal_class,expected",
    [
        ("nearside", True),
        ("farside", True),
        ("none", False),
        ("busway", False),
    ],
)
def test_has_signal(signal_class, expected):
    """has_signal is true only for stops at a (non-busway) traffic signal."""
    assert has_signal(signal_class) is expected
