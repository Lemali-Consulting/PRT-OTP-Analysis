"""Tests for OTP null classification logic."""

import polars as pl
import pytest

from prt_otp_analysis.otp_null_classification import classify_otp_nulls


@pytest.fixture()
def otp_routes() -> list[str]:
    return ["1", "2", "Y1"]


@pytest.fixture()
def otp_months() -> list[str]:
    return ["2019-01", "2019-02", "2019-03", "2020-11"]


@pytest.fixture()
def otp_pairs() -> set[tuple[str, str]]:
    """Route-months where OTP was actually reported."""
    return {
        ("1", "2019-01"), ("1", "2019-02"), ("1", "2019-03"), ("1", "2020-11"),
        ("2", "2019-01"), ("2", "2019-02"), ("2", "2019-03"),
        # Route 2 missing 2020-11, Y1 missing everything
    }


@pytest.fixture()
def schedule_pairs() -> set[tuple[str, str]]:
    """Route-months where service was scheduled (from WPRDC)."""
    return {
        ("1", "2019-01"), ("1", "2019-02"), ("1", "2019-03"), ("1", "2020-11"),
        ("2", "2019-01"), ("2", "2019-02"), ("2", "2019-03"), ("2", "2020-11"),
        ("Y1", "2019-01"), ("Y1", "2019-02"), ("Y1", "2019-03"), ("Y1", "2020-11"),
    }


@pytest.fixture()
def ridership_pairs() -> set[tuple[str, str]]:
    """Route-months where ridership was recorded."""
    return {
        ("1", "2019-01"), ("1", "2019-02"), ("1", "2019-03"), ("1", "2020-11"),
        ("2", "2019-01"), ("2", "2019-02"), ("2", "2019-03"), ("2", "2020-11"),
        # Y1 has no ridership data
    }


@pytest.fixture()
def schedule_range() -> tuple[str, str]:
    return ("2019-01", "2020-11")


@pytest.fixture()
def ridership_range() -> tuple[str, str]:
    return ("2019-01", "2020-11")


class TestClassifyOtpNulls:
    """Tests for the classify_otp_nulls function."""

    def test_returns_only_missing_pairs(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        # Should only contain route-months NOT in otp_pairs
        result_keys = set(zip(
            result_df["route_id"].to_list(),
            result_df["month"].to_list(),
        ))
        assert result_keys.isdisjoint(otp_pairs)

    def test_all_missing_pairs_classified(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        full_grid = {(r, m) for r in otp_routes for m in otp_months}
        missing = full_grid - otp_pairs
        result_keys = set(zip(
            result_df["route_id"].to_list(),
            result_df["month"].to_list(),
        ))
        assert result_keys == missing

    def test_scheduled_but_no_otp_is_unreported(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        """Route 2 in 2020-11: scheduled + has ridership, but no OTP → unreported."""
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        row = result_df.filter(
            (pl.col("route_id") == "2") & (pl.col("month") == "2020-11")
        )
        assert len(row) == 1
        assert row["reason"][0] == "unreported"

    def test_scheduled_no_ridership_still_unreported(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        """Y1 in all months: scheduled but no OTP and no ridership → unreported (schedule is sufficient evidence)."""
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        y1_rows = result_df.filter(pl.col("route_id") == "Y1")
        assert len(y1_rows) == 4
        assert (y1_rows["reason"] == "unreported").all()

    def test_not_scheduled_no_ridership_is_not_operating(self):
        """Route with no evidence of operating → not_operating."""
        result_df = classify_otp_nulls(
            otp_routes=["GHOST"],
            otp_months=["2019-06"],
            otp_pairs=set(),
            schedule_pairs=set(),
            ridership_pairs=set(),
            schedule_range=("2019-01", "2020-11"),
            ridership_range=("2019-01", "2020-11"),
        )
        assert len(result_df) == 1
        assert result_df["reason"][0] == "not_operating"
        assert result_df["evidence"][0] == "none"

    def test_outside_both_ranges_is_no_coverage(self):
        """Month outside both schedule and ridership ranges → no_coverage."""
        result_df = classify_otp_nulls(
            otp_routes=["1"],
            otp_months=["2025-06"],
            otp_pairs=set(),
            schedule_pairs=set(),
            ridership_pairs=set(),
            schedule_range=("2019-01", "2021-03"),
            ridership_range=("2017-01", "2024-10"),
        )
        assert len(result_df) == 1
        assert result_df["reason"][0] == "no_coverage"

    def test_outside_schedule_but_in_ridership_range(self):
        """Month after schedule ends but within ridership range, ridership exists → unreported."""
        result_df = classify_otp_nulls(
            otp_routes=["1"],
            otp_months=["2022-06"],
            otp_pairs=set(),
            schedule_pairs=set(),
            ridership_pairs={("1", "2022-06")},
            schedule_range=("2019-01", "2021-03"),
            ridership_range=("2017-01", "2024-10"),
        )
        assert len(result_df) == 1
        assert result_df["reason"][0] == "unreported"
        assert result_df["evidence"][0] == "ridership"

    def test_outside_schedule_in_ridership_range_no_ridership(self):
        """Month after schedule ends, within ridership range, no ridership → not_operating."""
        result_df = classify_otp_nulls(
            otp_routes=["1"],
            otp_months=["2022-06"],
            otp_pairs=set(),
            schedule_pairs=set(),
            ridership_pairs=set(),
            schedule_range=("2019-01", "2021-03"),
            ridership_range=("2017-01", "2024-10"),
        )
        assert len(result_df) == 1
        assert result_df["reason"][0] == "not_operating"

    def test_evidence_field_reflects_sources(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        # Route 2, 2020-11: both schedule and ridership → "both"
        row = result_df.filter(
            (pl.col("route_id") == "2") & (pl.col("month") == "2020-11")
        )
        assert row["evidence"][0] == "both"

        # Y1: schedule only → "schedule"
        y1_rows = result_df.filter(pl.col("route_id") == "Y1")
        assert (y1_rows["evidence"] == "schedule").all()

    def test_output_schema(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        assert set(result_df.columns) == {"route_id", "month", "reason", "evidence"}
        assert result_df.schema["route_id"] == pl.Utf8
        assert result_df.schema["month"] == pl.Utf8
        assert result_df.schema["reason"] == pl.Utf8
        assert result_df.schema["evidence"] == pl.Utf8

    def test_valid_reason_values(
        self, otp_routes, otp_months, otp_pairs,
        schedule_pairs, ridership_pairs, schedule_range, ridership_range,
    ):
        result_df = classify_otp_nulls(
            otp_routes, otp_months, otp_pairs,
            schedule_pairs, ridership_pairs,
            schedule_range, ridership_range,
        )
        valid_reasons = {"unreported", "not_operating", "no_coverage"}
        actual_reasons = set(result_df["reason"].unique().to_list())
        assert actual_reasons <= valid_reasons
