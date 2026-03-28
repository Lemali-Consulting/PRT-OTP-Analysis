"""Unit tests for prt_otp_analysis.common.schemas validation."""

import polars as pl
import pytest

from prt_otp_analysis.common.schemas import (
    NTD_AGENCY,
    NTD_ANNUAL_SERVICE,
    NTD_RIDERSHIP,
    OTP_MONTHLY,
    OTP_NULL_CLASSIFICATION,
    ROUTE_STOPS,
    ROUTES,
    STOP_REFERENCE,
    STOPS,
    Schema,
    validate,
)


class TestSchema:
    """Tests for the Schema dataclass."""

    def test_schema_has_name_and_columns(self):
        assert ROUTES.name == "routes"
        assert "route_id" in ROUTES.columns

    def test_columns_map_to_polars_dtypes(self):
        for col, dtype in ROUTES.columns.items():
            assert isinstance(col, str)
            # Polars dtype classes (e.g. pl.Utf8) are DataTypeClass metaclass instances
            assert dtype in (pl.Utf8, pl.Int64, pl.Float64)

    def test_nullable_tracked(self):
        # hood is nullable in stops
        assert "hood" in STOPS.nullable


class TestValidate:
    """Tests for the validate() function."""

    def test_valid_dataframe_passes(self):
        df = pl.DataFrame({
            "route_id": ["1", "P1"],
            "route_name": ["Freeport", "East Busway"],
            "mode": ["BUS", "BUS"],
        })
        result = validate(df, ROUTES)
        assert result.shape == (2, 3)

    def test_missing_column_raises(self):
        df = pl.DataFrame({
            "route_id": ["1"],
            "mode": ["BUS"],
        })
        with pytest.raises(ValueError, match="missing columns.*route_name"):
            validate(df, ROUTES)

    def test_wrong_dtype_raises(self):
        df = pl.DataFrame({
            "route_id": [1, 2],  # Int64 instead of Utf8
            "route_name": ["a", "b"],
            "mode": ["BUS", "BUS"],
        })
        with pytest.raises(TypeError, match="route_id.*expected.*got"):
            validate(df, ROUTES)

    def test_extra_columns_allowed(self):
        """Queries often SELECT extra computed columns — these should not fail."""
        df = pl.DataFrame({
            "route_id": ["1"],
            "route_name": ["Freeport"],
            "mode": ["BUS"],
            "extra_col": [42],
        })
        result = validate(df, ROUTES)
        assert "extra_col" in result.columns

    def test_subset_validation(self):
        """When a query selects only some columns, validate only those."""
        df = pl.DataFrame({
            "route_id": ["1"],
            "otp": [0.75],
        })
        result = validate(df, OTP_MONTHLY, subset=True)
        assert result.shape == (1, 2)

    def test_subset_still_checks_dtypes(self):
        df = pl.DataFrame({
            "route_id": [1],  # wrong dtype
            "otp": [0.75],
        })
        with pytest.raises(TypeError, match="route_id"):
            validate(df, OTP_MONTHLY, subset=True)

    def test_subset_false_requires_all_columns(self):
        df = pl.DataFrame({
            "route_id": ["1"],
            "otp": [0.75],
        })
        with pytest.raises(ValueError, match="missing columns"):
            validate(df, OTP_MONTHLY, subset=False)

    def test_nullable_column_allows_nulls(self):
        df = pl.DataFrame({
            "stop_id": ["S1"],
            "stop_code": [100],
            "stop_name": ["Main St"],
            "lat": [40.0],
            "lon": [-80.0],
            "county": ["Allegheny"],
            "muni": ["Pittsburgh"],
            "hood": [None],
        }).cast({"stop_id": pl.Utf8, "stop_name": pl.Utf8, "county": pl.Utf8,
                 "muni": pl.Utf8, "hood": pl.Utf8})
        # Should not raise
        result = validate(df, STOPS)
        assert result.shape == (1, 8)

    def test_empty_dataframe_passes(self):
        """An empty DataFrame with correct schema should pass."""
        df = pl.DataFrame(
            schema={"route_id": pl.Utf8, "route_name": pl.Utf8, "mode": pl.Utf8}
        )
        result = validate(df, ROUTES)
        assert len(result) == 0


class TestAllSchemas:
    """Verify all exported schemas have required fields."""

    @pytest.mark.parametrize("schema", [
        ROUTES, STOPS, ROUTE_STOPS, STOP_REFERENCE,
        OTP_MONTHLY, OTP_NULL_CLASSIFICATION, NTD_AGENCY, NTD_RIDERSHIP, NTD_ANNUAL_SERVICE,
    ])
    def test_schema_has_name_and_columns(self, schema):
        assert isinstance(schema.name, str)
        assert len(schema.columns) > 0
        assert all(isinstance(k, str) for k in schema.columns)
        assert all(v in (pl.Utf8, pl.Int64, pl.Float64) for v in schema.columns.values())

    @pytest.mark.parametrize("schema", [
        ROUTES, STOPS, ROUTE_STOPS, STOP_REFERENCE,
        OTP_MONTHLY, OTP_NULL_CLASSIFICATION, NTD_AGENCY, NTD_RIDERSHIP, NTD_ANNUAL_SERVICE,
    ])
    def test_nullable_is_subset_of_columns(self, schema):
        assert schema.nullable <= set(schema.columns)
