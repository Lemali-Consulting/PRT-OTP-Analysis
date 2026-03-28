"""Analysis 20: Test whether OTP declines predict subsequent ridership losses using lagged cross-correlation and Granger causality."""

import numpy as np
import polars as pl
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

from prt_otp_analysis.common import analysis_dir, correlate, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)

MIN_MONTHS = 36
MAX_LAG = 6


def load_data() -> pl.DataFrame:
    """Load paired monthly OTP and weekday ridership for routes with enough data."""
    df = query_to_polars("""
        SELECT o.route_id, o.month, o.otp, r.avg_riders
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        ORDER BY o.route_id, o.month
    """)

    # Filter to routes with at least MIN_MONTHS of paired data
    route_counts = df.group_by("route_id").agg(pl.col("month").count().alias("n"))
    keep = route_counts.filter(pl.col("n") >= MIN_MONTHS)["route_id"].to_list()
    df = df.filter(pl.col("route_id").is_in(keep))

    return df


def detrend(df: pl.DataFrame) -> pl.DataFrame:
    """Subtract system-wide monthly mean from each route's OTP and ridership."""
    system = df.group_by("month").agg(
        otp_sys=pl.col("otp").mean(),
        riders_sys=pl.col("avg_riders").mean(),
    )
    df = df.join(system, on="month")
    df = df.with_columns(
        otp_dt=(pl.col("otp") - pl.col("otp_sys")),
        riders_dt=(pl.col("avg_riders") - pl.col("riders_sys")),
    )
    return df


def compute_lagged_crosscorr(df: pl.DataFrame) -> pl.DataFrame:
    """Compute lagged cross-correlations (OTP leading ridership) for each route."""
    routes = df["route_id"].unique().sort().to_list()
    results = []

    for route in routes:
        rdf = df.filter(pl.col("route_id") == route).sort("month")
        otp = rdf["otp_dt"].to_numpy()
        riders = rdf["riders_dt"].to_numpy()

        for lag in range(0, MAX_LAG + 1):
            if lag == 0:
                lag_df = pl.DataFrame({"otp": otp, "riders": riders})
            else:
                # OTP at time t correlated with ridership at time t+lag
                lag_df = pl.DataFrame({"otp": otp[:-lag], "riders": riders[lag:]})
            corr = correlate(lag_df, "otp", "riders")
            results.append({
                "route_id": route,
                "lag": lag,
                "correlation": corr["pearson_r"],
                "p_value": corr["pearson_p"],
            })

    return pl.DataFrame(results)


def aggregate_crosscorr(ccdf: pl.DataFrame) -> pl.DataFrame:
    """Summarize cross-correlations across routes by lag."""
    return (
        ccdf.group_by("lag")
        .agg(
            median_r=pl.col("correlation").median(),
            q25_r=pl.col("correlation").quantile(0.25),
            q75_r=pl.col("correlation").quantile(0.75),
            mean_r=pl.col("correlation").mean(),
            n_significant=((pl.col("p_value") < 0.05) & (pl.col("correlation") > 0)).sum(),
            n_routes=pl.col("route_id").count(),
        )
        .sort("lag")
    )


def check_stationarity(df: pl.DataFrame, alpha: float = 0.05) -> dict:
    """Run ADF tests on each route's detrended OTP and ridership series.

    Returns a dict with summary statistics and a per-route DataFrame.
    """
    routes = df["route_id"].unique().sort().to_list()
    results = []
    for route in routes:
        rdf = df.filter(pl.col("route_id") == route).sort("month")
        otp = rdf["otp_dt"].to_numpy()
        riders = rdf["riders_dt"].to_numpy()
        try:
            otp_adf_p = adfuller(otp, autolag="AIC")[1]
        except Exception:
            otp_adf_p = None
        try:
            riders_adf_p = adfuller(riders, autolag="AIC")[1]
        except Exception:
            riders_adf_p = None
        results.append({
            "route_id": route,
            "otp_adf_p": otp_adf_p,
            "riders_adf_p": riders_adf_p,
            "otp_stationary": otp_adf_p is not None and otp_adf_p < alpha,
            "riders_stationary": riders_adf_p is not None and riders_adf_p < alpha,
        })
    adf_df = pl.DataFrame(results).with_columns(
        pl.col("otp_stationary").cast(pl.Boolean),
        pl.col("riders_stationary").cast(pl.Boolean),
    )
    n = len(routes)
    n_otp_stat = adf_df.filter(pl.col("otp_stationary")).height
    n_riders_stat = adf_df.filter(pl.col("riders_stationary")).height
    n_both_stat = adf_df.filter(pl.col("otp_stationary") & pl.col("riders_stationary")).height
    return {
        "adf_df": adf_df,
        "n_routes": n,
        "n_otp_stationary": n_otp_stat,
        "n_riders_stationary": n_riders_stat,
        "n_both_stationary": n_both_stat,
    }


def run_granger_tests(df: pl.DataFrame, adf_df: pl.DataFrame) -> pl.DataFrame:
    """Run Granger causality tests (OTP -> ridership) for each route.

    First-differences non-stationary series before testing.
    """
    routes = df["route_id"].unique().sort().to_list()
    n_routes = len(routes)
    adf_lookup = {
        row["route_id"]: (row["otp_stationary"], row["riders_stationary"])
        for row in adf_df.iter_rows(named=True)
    }
    results = []

    for route in routes:
        rdf = df.filter(pl.col("route_id") == route).sort("month")
        otp = rdf["otp_dt"].to_numpy()
        riders = rdf["riders_dt"].to_numpy()

        otp_stat, riders_stat = adf_lookup.get(route, (True, True))
        differenced = not (otp_stat and riders_stat)

        # First-difference if either series is non-stationary
        if differenced:
            otp = np.diff(otp)
            riders = np.diff(riders)

        if len(otp) < MAX_LAG + 5:
            results.append({
                "route_id": route, "best_lag": None, "f_stat": None,
                "p_value": None, "p_bonferroni": None,
                "n_months": len(rdf), "differenced": differenced,
            })
            continue

        # statsmodels expects [y, x] where we test if x Granger-causes y
        data = np.column_stack([riders, otp])

        best_lag = None
        best_p = 1.0
        best_f = 0.0

        try:
            res = grangercausalitytests(data, maxlag=MAX_LAG, verbose=False)
            for lag in range(1, MAX_LAG + 1):
                f_stat = res[lag][0]["ssr_ftest"][0]
                p_val = res[lag][0]["ssr_ftest"][1]
                if p_val < best_p:
                    best_p = p_val
                    best_f = f_stat
                    best_lag = lag
        except Exception:
            best_lag = None
            best_p = None
            best_f = None

        results.append({
            "route_id": route,
            "best_lag": best_lag,
            "f_stat": best_f,
            "p_value": best_p,
            "p_bonferroni": min(best_p * n_routes, 1.0) if best_p is not None else None,
            "n_months": len(rdf),
            "differenced": differenced,
        })

    return pl.DataFrame(results)


def make_crosscorr_chart(agg: pl.DataFrame) -> None:
    """Plot median cross-correlation by lag with IQR band."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 5))

    lags = agg["lag"].to_list()
    median = agg["median_r"].to_list()
    q25 = agg["q25_r"].to_list()
    q75 = agg["q75_r"].to_list()

    ax.plot(lags, median, "o-", color="#2563eb", linewidth=2, markersize=8, label="Median r")
    ax.fill_between(lags, q25, q75, alpha=0.2, color="#2563eb", label="IQR")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Lag (months, OTP leading ridership)")
    ax.set_ylabel("Pearson r (detrended)")
    ax.set_title("Lagged Cross-Correlation: OTP -> Ridership")
    ax.set_xticks(lags)
    ax.legend()

    save_chart(fig, OUT / "lagged_crosscorr.png")


def make_granger_chart(gdf: pl.DataFrame) -> None:
    """Plot histogram of Granger p-values and best-lag distribution."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    valid = gdf.filter(pl.col("p_value").is_not_null())
    pvals = valid["p_value"].to_numpy()
    best_lags = valid["best_lag"].to_numpy()

    # P-value histogram
    ax1.hist(pvals, bins=20, range=(0, 1), color="#2563eb", edgecolor="white", alpha=0.8)
    ax1.axvline(0.05, color="#ef4444", linestyle="--", label="p = 0.05")
    n_sig = (pvals < 0.05).sum()
    n_bonf = valid.filter(pl.col("p_bonferroni") < 0.05).height
    ax1.set_xlabel("p-value (best lag, SSR F-test)")
    ax1.set_ylabel("Number of routes")
    ax1.set_title(f"Granger Causality p-values\n{n_sig}/{len(pvals)} sig. at 0.05, "
                  f"{n_bonf}/{len(pvals)} after Bonferroni")
    ax1.legend()

    # Best-lag distribution (for significant routes only)
    sig_lags = best_lags[pvals < 0.05]
    if len(sig_lags) > 0:
        ax2.hist(sig_lags, bins=range(1, MAX_LAG + 2), color="#e11d48",
                 edgecolor="white", alpha=0.8, align="left")
    ax2.set_xlabel("Best lag (months)")
    ax2.set_ylabel("Number of routes")
    ax2.set_title(f"Optimal Lag for Significant Routes (n={len(sig_lags)})")
    ax2.set_xticks(range(1, MAX_LAG + 1))

    save_chart(fig, OUT / "granger_summary.png")


@run_analysis(20, "OTP -> Ridership Causality")
def main() -> None:
    """Entry point: load, detrend, cross-correlate, Granger test, chart, and save."""
    print("\nLoading data...")
    df = load_data()
    n_routes = df["route_id"].n_unique()
    print(f"  {len(df):,} route-month observations ({n_routes} routes, {MIN_MONTHS}+ months each)")

    print("\nDetrending (subtracting system monthly mean)...")
    df = detrend(df)

    print("\nComputing lagged cross-correlations (lags 0--6)...")
    ccdf = compute_lagged_crosscorr(df)
    agg = aggregate_crosscorr(ccdf)
    print("\n  Lag  Median r   IQR              Sig+ routes")
    print("  ---  --------   ---------------  -----------")
    for row in agg.iter_rows(named=True):
        print(f"  {row['lag']:>3d}  {row['median_r']:>8.4f}   "
              f"[{row['q25_r']:+.4f}, {row['q75_r']:+.4f}]  "
              f"{row['n_significant']}/{row['n_routes']}")

    print("\nChecking stationarity (ADF tests on detrended series)...")
    adf_results = check_stationarity(df)
    print(f"  OTP stationary:      {adf_results['n_otp_stationary']}/{adf_results['n_routes']} routes")
    print(f"  Ridership stationary: {adf_results['n_riders_stationary']}/{adf_results['n_routes']} routes")
    print(f"  Both stationary:     {adf_results['n_both_stationary']}/{adf_results['n_routes']} routes")
    n_diff = adf_results['n_routes'] - adf_results['n_both_stationary']
    print(f"  Will first-difference {n_diff} routes before Granger testing")

    print("\nRunning Granger causality tests...")
    gdf = run_granger_tests(df, adf_results["adf_df"])
    valid = gdf.filter(pl.col("p_value").is_not_null())
    n_sig = valid.filter(pl.col("p_value") < 0.05).height
    n_bonf = valid.filter(pl.col("p_bonferroni") < 0.05).height
    print(f"  {n_sig}/{valid.height} routes significant at p < 0.05")
    print(f"  {n_bonf}/{valid.height} routes significant after Bonferroni correction")

    # Most significant routes
    top = valid.sort("p_value").head(10)
    print("\n  Top 10 routes by Granger significance:")
    print(f"  {'Route':<10} {'Lag':>4} {'F-stat':>8} {'p-value':>10} {'p-Bonf':>10}")
    for row in top.iter_rows(named=True):
        print(f"  {row['route_id']:<10} {row['best_lag']:>4d} {row['f_stat']:>8.2f} "
              f"{row['p_value']:>10.4f} {row['p_bonferroni']:>10.4f}")

    print("\nSaving CSVs...")
    save_csv(ccdf, OUT / "lagged_crosscorr.csv")
    save_csv(gdf, OUT / "granger_results.csv")

    print("\nGenerating charts...")
    make_crosscorr_chart(agg)
    make_granger_chart(gdf)


if __name__ == "__main__":
    main()
