"""Polars DataFrame schemas for PRT database tables and validation helper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import polars as pl


@dataclass(frozen=True)
class Schema:
    """Expected column names and Polars dtypes for a database table."""

    name: str
    columns: dict[str, Any]  # values are polars dtype classes (e.g. pl.Utf8)
    nullable: frozenset[str] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# Table schemas — one per database table in prt.db
# ---------------------------------------------------------------------------

ROUTES = Schema(
    name="routes",
    columns={
        "route_id": pl.Utf8,
        "route_name": pl.Utf8,
        "mode": pl.Utf8,
    },
)

STOPS = Schema(
    name="stops",
    columns={
        "stop_id": pl.Utf8,
        "stop_code": pl.Int64,
        "stop_name": pl.Utf8,
        "lat": pl.Float64,
        "lon": pl.Float64,
        "county": pl.Utf8,
        "muni": pl.Utf8,
        "hood": pl.Utf8,
    },
    nullable=frozenset({"hood"}),
)

ROUTE_STOPS = Schema(
    name="route_stops",
    columns={
        "route_id": pl.Utf8,
        "stop_id": pl.Utf8,
        "direction": pl.Utf8,
        "trips_wd": pl.Int64,
        "trips_sa": pl.Int64,
        "trips_su": pl.Int64,
        "trips_7d": pl.Int64,
        "svc_days": pl.Utf8,
    },
)

STOP_REFERENCE = Schema(
    name="stop_reference",
    columns={
        "stop_id": pl.Utf8,
        "stop_code": pl.Int64,
        "stop_name": pl.Utf8,
        "stop_source": pl.Utf8,
        "public_stop": pl.Utf8,
        "lat": pl.Float64,
        "lon": pl.Float64,
        "mode": pl.Utf8,
        "first_served": pl.Utf8,
        "last_served": pl.Utf8,
        "county": pl.Utf8,
        "muni": pl.Utf8,
        "hood": pl.Utf8,
    },
    nullable=frozenset({"hood"}),
)

OTP_MONTHLY = Schema(
    name="otp_monthly",
    columns={
        "route_id": pl.Utf8,
        "month": pl.Utf8,
        "otp": pl.Float64,
    },
)

NTD_AGENCY = Schema(
    name="ntd_agency",
    columns={
        "ntd_id": pl.Int64,
        "agency_name": pl.Utf8,
        "mode": pl.Utf8,
        "tos": pl.Utf8,
        "hq_city": pl.Utf8,
        "hq_state": pl.Utf8,
        "uza_name": pl.Utf8,
    },
)

NTD_RIDERSHIP = Schema(
    name="ntd_ridership",
    columns={
        "ntd_id": pl.Int64,
        "mode": pl.Utf8,
        "tos": pl.Utf8,
        "month": pl.Utf8,
        "upt": pl.Int64,
        "vrh": pl.Float64,
        "vrm": pl.Float64,
    },
    nullable=frozenset({"upt", "vrh", "vrm"}),
)

NTD_ANNUAL_SERVICE = Schema(
    name="ntd_annual_service",
    columns={
        "ntd_id": pl.Int64,
        "agency_name": pl.Utf8,
        "city": pl.Utf8,
        "state": pl.Utf8,
        "uza_name": pl.Utf8,
        "year": pl.Int64,
        "vrh": pl.Float64,
        "vrm": pl.Float64,
        "upt": pl.Float64,
        "voms": pl.Float64,
        "fares": pl.Float64,
        "opexp": pl.Float64,
        "opexp_vo": pl.Float64,
        "opexp_vm": pl.Float64,
        "opexp_nvm": pl.Float64,
        "opexp_ga": pl.Float64,
    },
    nullable=frozenset({"vrh", "vrm", "upt", "voms", "fares", "opexp",
                         "opexp_vo", "opexp_vm", "opexp_nvm", "opexp_ga"}),
)


ALLEGHENY_GO_WEEKLY = Schema(
    name="allegheny_go_weekly",
    columns={
        "week_start": pl.Utf8,
        "rides": pl.Int64,
        "riders": pl.Int64,
    },
)


NTD_FLEET_AGE = Schema(
    name="ntd_fleet_age",
    columns={
        "ntd_id": pl.Int64,
        "year": pl.Int64,
        "vehicle_type": pl.Utf8,
        "total_vehicles": pl.Int64,
        "avg_age": pl.Float64,
        "avg_miles": pl.Float64,
    },
    nullable=frozenset({"total_vehicles", "avg_age", "avg_miles"}),
)


OTP_NULL_CLASSIFICATION = Schema(
    name="otp_null_classification",
    columns={
        "route_id": pl.Utf8,
        "month": pl.Utf8,
        "reason": pl.Utf8,
        "evidence": pl.Utf8,
    },
)


CENSUS_TRACTS = Schema(
    name="census_tracts",
    columns={
        "geoid": pl.Utf8,
        "state_fips": pl.Utf8,
        "county_fips": pl.Utf8,
        "tract_code": pl.Utf8,
        "population": pl.Int64,
        "median_household_income": pl.Int64,
        "households_total": pl.Int64,
        "households_zero_vehicle": pl.Int64,
        "pop_white_nh": pl.Int64,
        "pop_black_nh": pl.Int64,
        "pop_asian_nh": pl.Int64,
        "pop_hispanic": pl.Int64,
        "land_area_m2": pl.Float64,
        "intpt_lat": pl.Float64,
        "intpt_lon": pl.Float64,
        "geometry_wkt": pl.Utf8,
    },
    nullable=frozenset({
        "population", "median_household_income",
        "households_total", "households_zero_vehicle",
        "pop_white_nh", "pop_black_nh", "pop_asian_nh", "pop_hispanic",
    }),
)


ROUTE_SIGNALS = Schema(
    name="route_signals",
    columns={
        "route_id": pl.Utf8,
        "n_signals": pl.Int64,
        "length_km": pl.Float64,
        "signal_density": pl.Float64,
        "n_route_points": pl.Int64,
        "match_rate": pl.Float64,
    },
    nullable=frozenset({"signal_density"}),
)

ROUTE_ROAD_CLASS = Schema(
    name="route_road_class",
    columns={
        "route_id": pl.Utf8,
        "n_segments": pl.Int64,
        "total_length_ft": pl.Float64,
        "weighted_lanes": pl.Float64,
        "weighted_func_cls": pl.Float64,
        "weighted_speed": pl.Float64,
        "arterial_share": pl.Float64,
        "divided_share": pl.Float64,
        "n_route_points": pl.Int64,
        "match_rate": pl.Float64,
    },
    nullable=frozenset({
        "weighted_lanes", "weighted_func_cls", "weighted_speed",
        "arterial_share", "divided_share",
    }),
)


def validate(
    df: pl.DataFrame,
    schema: Schema,
    *,
    subset: bool = False,
) -> pl.DataFrame:
    """Validate a DataFrame against an expected schema.

    When *subset* is True, only columns present in *df* are checked (useful for
    queries that SELECT a subset of the table). When False (default), all schema
    columns must be present.

    Returns the DataFrame unchanged if valid; raises ValueError or TypeError otherwise.
    """
    label = schema.name

    if not subset:
        missing = set(schema.columns) - set(df.columns)
        if missing:
            raise ValueError(f"{label}: missing columns {sorted(missing)}")

    for col in df.columns:
        if col not in schema.columns:
            continue
        expected = schema.columns[col]
        actual = df.schema[col]
        # All-null columns infer as pl.Null; accept if the column is nullable.
        if actual == pl.Null and col in schema.nullable:
            continue
        if actual != expected:
            raise TypeError(
                f"{label}: column '{col}' expected {expected}, got {actual}"
            )

    return df
