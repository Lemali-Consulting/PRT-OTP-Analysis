"""Scatter analysis of route stop count versus average on-time performance."""

import polars as pl
from scipy.stats import pearsonr

from prt_otp_analysis.common import analysis_dir, correlate_by_mode, mode_scatter, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)


def load_data() -> pl.DataFrame:
    """Load per-route stop counts, average OTP, and mode."""
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops
        GROUP BY route_id
    """)
    avg_otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)
    return avg_otp.join(stop_counts, on="route_id", how="inner")


def _high_leverage(x: list[float], cutoff_mult: float = 3.0) -> list[bool]:
    """Flag points whose simple-regression leverage exceeds the cutoff.

    Returns one bool per point. Leverage h_i = 1/n + (x_i - mean)^2 / Sxx;
    a point is flagged when h_i > cutoff_mult * (2/n), the standard rule of
    thumb for a two-parameter (slope + intercept) regression.
    """
    n = len(x)
    mean_x = sum(x) / n
    sxx = sum((xi - mean_x) ** 2 for xi in x)
    cutoff = cutoff_mult * 2 / n
    return [(1 / n + (xi - mean_x) ** 2 / sxx) > cutoff for xi in x]


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Compute correlations plus a leverage-robustness check for bus routes.

    Adds ``bus_robust_*`` keys: the bus-only Pearson correlation recomputed
    after dropping high-leverage routes (the few extreme-stop-count points
    that disproportionately steer the trendline).
    """
    results = correlate_by_mode(df, "stop_count", "avg_otp")

    bus_df = df.filter(pl.col("mode") == "BUS")
    flagged = pl.Series(_high_leverage(bus_df["stop_count"].to_list()))
    robust_df = bus_df.filter(~flagged)
    r, p = pearsonr(robust_df["stop_count"].to_list(), robust_df["avg_otp"].to_list())
    results["bus_robust_pearson_r"] = float(r)
    results["bus_robust_pearson_p"] = float(p)
    results["bus_robust_n"] = robust_df.height
    results["bus_excluded_routes"] = bus_df.filter(flagged)["route_id"].to_list()
    return df, results


def make_chart(df: pl.DataFrame) -> None:
    """Generate scatter plot of stop count vs OTP with bus-only trendline."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))
    mode_scatter(ax, df, "stop_count", "avg_otp")
    for route in ("59", "77"):
        row = df.filter(pl.col("route_id") == route)
        if row.height:
            ax.annotate(
                f"Route {route}",
                (row["stop_count"][0], row["avg_otp"][0]),
                textcoords="offset points",
                xytext=(-9, 9),
                fontsize=8,
                ha="right",
                color="#1e3a5f",
            )
    ax.set_xlabel("Number of Stops")
    ax.set_ylabel("Average OTP")
    ax.set_title("Stop Count vs On-Time Performance by Route")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    save_chart(fig, OUT / "stop_count_vs_otp.png")


@run_analysis(7, "Stop Count vs OTP")
def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    with phase("Loading data"):
        df = load_data()
        print(f"  {len(df)} routes with both stop count and OTP data")

    with phase("Analyzing"):
        df, results = analyze(df)
        print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f}), n = {results['all_n']}")
        print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
        print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
        print(f"               n = {results['bus_n']} bus routes")
        excluded = ", ".join(results["bus_excluded_routes"]) or "none"
        print(f"  Bus robust:  Pearson r = {results['bus_robust_pearson_r']:.4f} (p = {results['bus_robust_pearson_p']:.4f}), n = {results['bus_robust_n']}")
        print(f"               high-leverage routes excluded: {excluded}")

    with phase("Saving CSV"):
        save_csv(df, OUT / "stop_count_otp.csv")

    with phase("Generating chart"):
        make_chart(df)


if __name__ == "__main__":
    main()
