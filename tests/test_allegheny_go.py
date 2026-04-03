"""Tests for the Allegheny Go Tableau extraction module."""

import json

import polars as pl
import pytest

from prt_otp_analysis.allegheny_go import (
    _decode_alias,
    parse_bootstrap_response,
)


# --- Fixtures: realistic VizQL bootstrap response fragments ---


def _make_bootstrap_payload(
    datetimes: list[str],
    integers: list[int],
    ride_alias_indices: list[int],
    rider_alias_indices: list[int],
) -> str:
    """Build a minimal Tableau bootstrapSession multipart response.

    The real response is length-prefixed: <len>;<json><len>;<json>
    Part 0 = session metadata, Part 1 = secondaryInfo with data.
    """
    date_value_indices = list(range(len(datetimes)))

    part0 = {
        "sheetName": "Ridership",
        "layoutId": "123",
        "newSessionId": "TEST-SESSION",
        "worldUpdate": {},
    }

    part1 = {
        "secondaryInfo": {
            "presModelMap": {
                "dataDictionary": {
                    "presModelHolder": {
                        "genDataDictionaryPresModel": {
                            "dataSegments": {
                                "0": {
                                    "dataColumns": [
                                        {
                                            "dataType": "integer",
                                            "dataValues": integers,
                                        },
                                        {
                                            "dataType": "datetime",
                                            "dataValues": datetimes,
                                        },
                                    ],
                                },
                            },
                        },
                    },
                },
                "vizData": {
                    "presModelHolder": {
                        "genPresModelMapPresModel": {
                            "presModelMap": {
                                "Ridership Total Rides over Time (2)": {
                                    "presModelHolder": {
                                        "genVizDataPresModel": {
                                            "paneColumnsData": {
                                                "paneColumnsList": [
                                                    {
                                                        "vizPaneColumns": [
                                                            {"tupleIds": list(range(1, len(datetimes) + 1))},
                                                            {"valueIndices": date_value_indices, "aliasIndices": date_value_indices},
                                                            {"valueIndices": [], "aliasIndices": ride_alias_indices},
                                                        ],
                                                    },
                                                    {
                                                        "vizPaneColumns": [
                                                            {"tupleIds": list(range(100, 100 + len(datetimes)))},
                                                            {"valueIndices": [], "aliasIndices": []},
                                                            {"valueIndices": [], "aliasIndices": rider_alias_indices},
                                                        ],
                                                    },
                                                ],
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    }

    s0 = json.dumps(part0)
    s1 = json.dumps(part1)
    return f"{len(s0)};{s0}{len(s1)};{s1}"


# Sample data: 3 weeks
SAMPLE_DATETIMES = [
    "2024-05-12 00:00:00",
    "2024-05-19 00:00:00",
    "2024-05-26 00:00:00",
]
SAMPLE_INTEGERS = [262, 745, 1068, 23, 70, 134]  # rides[0:3] + riders[3:6]
# Rides use negative alias: -3 → integers[0], -4 → integers[1], -5 → integers[2]
SAMPLE_RIDE_ALIASES = [-3, -4, -5]
# Riders use positive indices: 3 → integers[3], 4 → integers[4], 5 → integers[5]
SAMPLE_RIDER_ALIASES = [3, 4, 5]


class TestDecodeAlias:
    """Tests for the alias index decoding helper."""

    def test_positive_index(self) -> None:
        assert _decode_alias(2, [10, 20, 30]) == 30

    def test_negative_index(self) -> None:
        # -3 → data[0], -4 → data[1]
        assert _decode_alias(-3, [100, 200]) == 100
        assert _decode_alias(-4, [100, 200]) == 200

    def test_out_of_range_returns_none(self) -> None:
        assert _decode_alias(5, [1, 2]) is None
        assert _decode_alias(-10, [1, 2]) is None


class TestParseBootstrapResponse:
    """Tests for parsing the full bootstrap multipart response."""

    def test_extracts_weekly_ridership(self) -> None:
        raw = _make_bootstrap_payload(
            SAMPLE_DATETIMES, SAMPLE_INTEGERS,
            SAMPLE_RIDE_ALIASES, SAMPLE_RIDER_ALIASES,
        )
        result_df = parse_bootstrap_response(raw)

        assert isinstance(result_df, pl.DataFrame)
        assert len(result_df) == 3
        assert set(result_df.columns) == {"week_start", "rides", "riders"}

    def test_correct_values(self) -> None:
        raw = _make_bootstrap_payload(
            SAMPLE_DATETIMES, SAMPLE_INTEGERS,
            SAMPLE_RIDE_ALIASES, SAMPLE_RIDER_ALIASES,
        )
        result_df = parse_bootstrap_response(raw)

        assert result_df["week_start"].to_list() == [
            "2024-05-12", "2024-05-19", "2024-05-26",
        ]
        assert result_df["rides"].to_list() == [262, 745, 1068]
        assert result_df["riders"].to_list() == [23, 70, 134]

    def test_no_datetimes_raises(self) -> None:
        raw = _make_bootstrap_payload([], SAMPLE_INTEGERS, [], [])
        with pytest.raises(ValueError, match="No datetime column"):
            parse_bootstrap_response(raw)

    def test_mismatched_pane_lengths_raises(self) -> None:
        raw = _make_bootstrap_payload(
            SAMPLE_DATETIMES, SAMPLE_INTEGERS,
            SAMPLE_RIDE_ALIASES[:2],  # only 2 ride indices for 3 dates
            SAMPLE_RIDER_ALIASES,
        )
        with pytest.raises(ValueError, match="Mismatched array lengths"):
            parse_bootstrap_response(raw)

    def test_missing_worksheet_raises(self) -> None:
        """When the expected worksheet is renamed, raise with available names."""
        part0 = json.dumps({"sheetName": "X", "worldUpdate": {}})
        part1_data = {
            "secondaryInfo": {
                "presModelMap": {
                    "dataDictionary": {
                        "presModelHolder": {
                            "genDataDictionaryPresModel": {
                                "dataSegments": {
                                    "0": {
                                        "dataColumns": [
                                            {"dataType": "datetime", "dataValues": ["2024-01-01"]},
                                            {"dataType": "integer", "dataValues": [1]},
                                        ],
                                    },
                                },
                            },
                        },
                    },
                    "vizData": {
                        "presModelHolder": {
                            "genPresModelMapPresModel": {
                                "presModelMap": {
                                    "Some Other Sheet": {},
                                },
                            },
                        },
                    },
                },
            },
        }
        part1 = json.dumps(part1_data)
        raw = f"{len(part0)};{part0}{len(part1)};{part1}"

        with pytest.raises(ValueError, match="not found"):
            parse_bootstrap_response(raw)
