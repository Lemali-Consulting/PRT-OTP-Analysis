"""Shared utilities for analysis scripts: DB access, paths, constants, and plotting."""

from prt_otp_analysis.common.db import (
    CONFIDENCE_95_PERCENTILE,
    DATA_DIR,
    DB_PATH,
    OTP_GOOD_THRESHOLD,
    OTP_WARNING_THRESHOLD,
    PEERS,
    PRE_COVID_BASELINE_MONTH,
    PRE_COVID_BASELINE_YEAR,
    PROJECT_ROOT,
    Z_CRITICAL_95,
    classify_bus_route,
    get_db,
    output_dir,
    query_to_polars,
)
from prt_otp_analysis.common.io import print_done, print_header, save_chart, save_csv
from prt_otp_analysis.common.plotting import setup_plotting
from prt_otp_analysis.common.schemas import validate
from prt_otp_analysis.common.stats import (
    correlate,
    correlate_by_mode,
    gini,
    weighted_mean,
)

__all__ = [
    "CONFIDENCE_95_PERCENTILE",
    "DATA_DIR",
    "DB_PATH",
    "OTP_GOOD_THRESHOLD",
    "OTP_WARNING_THRESHOLD",
    "PEERS",
    "PRE_COVID_BASELINE_MONTH",
    "PRE_COVID_BASELINE_YEAR",
    "PROJECT_ROOT",
    "Z_CRITICAL_95",
    "classify_bus_route",
    "get_db",
    "output_dir",
    "print_done",
    "print_header",
    "query_to_polars",
    "save_chart",
    "save_csv",
    "correlate",
    "correlate_by_mode",
    "gini",
    "setup_plotting",
    "validate",
    "weighted_mean",
]
