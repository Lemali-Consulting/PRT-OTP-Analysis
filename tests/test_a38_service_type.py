"""Tests for A38 service type segmentation of downtown recovery analysis."""

import polars as pl
import pytest

from prt_otp_analysis.common import classify_bus_route


def _make_route_scores(route_ids: list[str]) -> pl.DataFrame:
    """Build a minimal route_scores DataFrame with fake downtown shares."""
    return pl.DataFrame(
        {
            "route_id": route_ids,
            "dt_share": [0.5] * len(route_ids),
            "total_boardings": [1000.0] * len(route_ids),
            "dt_boardings": [500.0] * len(route_ids),
            "n_stops": [20] * len(route_ids),
        }
    )


class TestServiceTypeClassification:
    """Verify classify_bus_route maps route IDs to expected service types."""

    @pytest.mark.parametrize(
        "route_id, expected",
        [
            ("1", "local"),
            ("61A", "local"),
            ("19L", "limited"),
            ("51L", "limited"),
            ("28X", "express"),
            ("P1", "busway"),
            ("P3", "busway"),
            ("G2", "busway"),
            ("P12", "flyer"),
            ("P76", "flyer"),
            ("O1", "flyer"),
            ("G31", "flyer"),
        ],
    )
    def test_classify_bus_route(self, route_id: str, expected: str) -> None:
        assert classify_bus_route(route_id) == expected


class TestServiceTypeGrouping:
    """Verify the commuter vs local grouping used in A38."""

    COMMUTER_TYPES = {"express", "flyer", "busway"}

    def test_commuter_group_contains_express_and_flyers(self) -> None:
        route_ids = ["1", "61A", "28X", "P12", "P76", "O1", "G2", "19L"]
        subtypes = [classify_bus_route(r) for r in route_ids]
        groups = [
            "commuter" if s in self.COMMUTER_TYPES else s for s in subtypes
        ]
        expected = [
            "local",
            "local",
            "commuter",
            "commuter",
            "commuter",
            "commuter",
            "commuter",
            "limited",
        ]
        assert groups == expected

    def test_add_service_type_column(self) -> None:
        """Simulates the column-addition logic that main.py should use."""
        route_ids = ["1", "P12", "28X", "51L"]
        route_scores_df = _make_route_scores(route_ids)

        # This is the pattern main.py should implement
        commuter_types = {"express", "flyer", "busway"}
        result_df = route_scores_df.with_columns(
            pl.col("route_id")
            .map_elements(classify_bus_route, return_dtype=pl.Utf8)
            .alias("subtype"),
        ).with_columns(
            pl.when(pl.col("subtype").is_in(commuter_types))
            .then(pl.lit("Commuter/Express"))
            .when(pl.col("subtype") == "limited")
            .then(pl.lit("Limited"))
            .otherwise(pl.lit("Local"))
            .alias("service_type"),
        )

        assert result_df["service_type"].to_list() == [
            "Local",
            "Commuter/Express",
            "Commuter/Express",
            "Limited",
        ]
        assert "service_type" in result_df.columns
        assert "subtype" in result_df.columns
