"""Statistical helpers and output utilities shared across analyses."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats as sp_stats


def weighted_mean(
    value: str | pl.Expr,
    weight: str | pl.Expr,
    *,
    safe: bool = False,
) -> pl.Expr:
    """Return a Polars expression for the weighted mean of *value* by *weight*.

    When *safe* is True, falls back to the unweighted mean if sum of weights is zero.
    """
    val = pl.col(value) if isinstance(value, str) else value
    wt = pl.col(weight) if isinstance(weight, str) else weight

    expr = (val * wt).sum() / wt.sum()

    if safe:
        expr = pl.when(wt.sum() > 0).then(expr).otherwise(val.mean())

    return expr


def correlate(
    df: pl.DataFrame,
    x_col: str,
    y_col: str,
    *,
    min_n: int = 3,
) -> dict[str, float]:
    """Compute Pearson and Spearman correlations between two columns.

    Rows with null in either column are dropped. Returns NaN values if
    fewer than *min_n* rows remain.
    """
    clean_df = df.drop_nulls(subset=[x_col, y_col])
    n = len(clean_df)
    nan = float("nan")

    if n < min_n:
        return {
            "pearson_r": nan, "pearson_p": nan,
            "spearman_r": nan, "spearman_p": nan, "n": n,
        }

    x = clean_df[x_col].to_list()
    y = clean_df[y_col].to_list()

    pr, pp = sp_stats.pearsonr(x, y)
    sr, sp = sp_stats.spearmanr(x, y)

    return {"pearson_r": pr, "pearson_p": pp, "spearman_r": sr, "spearman_p": sp, "n": n}


def correlate_by_mode(
    df: pl.DataFrame,
    x_col: str,
    y_col: str,
    *,
    min_n: int = 3,
) -> dict[str, dict[str, float]]:
    """Compute correlations for all routes and for bus-only routes.

    *df* must have a ``mode`` column.
    """
    return {
        "all": correlate(df, x_col, y_col, min_n=min_n),
        "bus": correlate(
            df.filter(pl.col("mode") == "BUS"), x_col, y_col, min_n=min_n,
        ),
    }


def gini(values: list[float]) -> float:
    """Compute the Gini coefficient for a list of non-negative values.

    Returns NaN if fewer than 2 non-NaN values or if the sum is zero.
    """
    arr = np.array(values, dtype=float)
    arr = arr[~np.isnan(arr)]
    if len(arr) < 2 or arr.sum() == 0:
        return float("nan")
    arr = np.sort(arr)
    n = len(arr)
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))


from prt_otp_analysis.common.io import save_csv as save_csv  # re-export
