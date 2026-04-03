"""Integration tests: validate actual prt.db tables against declared schemas."""

import pytest

from prt_otp_analysis.common import query_to_polars
from prt_otp_analysis.common.schemas import (
    ALLEGHENY_GO_WEEKLY,
    NTD_AGENCY,
    NTD_ANNUAL_SERVICE,
    NTD_RIDERSHIP,
    OTP_MONTHLY,
    OTP_NULL_CLASSIFICATION,
    ROUTE_STOPS,
    ROUTES,
    STOP_REFERENCE,
    STOPS,
    validate,
)

ALL_TABLE_SCHEMAS = [
    ROUTES, STOPS, ROUTE_STOPS, STOP_REFERENCE,
    OTP_MONTHLY, NTD_AGENCY, NTD_RIDERSHIP, NTD_ANNUAL_SERVICE,
    OTP_NULL_CLASSIFICATION, ALLEGHENY_GO_WEEKLY,
]


@pytest.mark.parametrize("schema", ALL_TABLE_SCHEMAS, ids=lambda s: s.name)
def test_actual_table_matches_schema(schema):
    """SELECT * from each table and validate against its schema."""
    df = query_to_polars(f"SELECT * FROM {schema.name} LIMIT 100")
    validate(df, schema)
