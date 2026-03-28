"""Scatter analysis of route stop count versus average on-time performance."""

import polars as pl
from scipy import stats

from prt_otp_analysis.common import MODE_COLORS, analysis_dir, correlate_by_mode, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

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


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Compute Pearson and Spearman correlations, overall and bus-only."""
    return df, correlate_by_mode(df, "stop_count", "avg_otp")


def make_chart(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter plot of stop count vs OTP with bus-only trendline."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    for mode, color in MODE_COLORS.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["stop_count"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Bus-only regression line using linregress for consistency with Pearson r
    bus = df.filter(pl.col("mode") == "BUS")
    x_vals = bus["stop_count"].to_list()
    y_vals = bus["avg_otp"].to_list()
    if len(x_vals) >= 3:
        lr = stats.linregress(x_vals, y_vals)
        x_line = [min(x_vals), max(x_vals)]
        y_line = [lr.slope * xi + lr.intercept for xi in x_line]
        r_bus = results["bus_pearson_r"]
        p_bus = results["bus_pearson_p"]
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"BUS trend (r={r_bus:.3f}, p={p_bus:.3f})")

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

    with phase("Saving CSV"):
        save_csv(df, OUT / "stop_count_otp.csv")

    with phase("Generating chart"):
        make_chart(df, results)


if __name__ == "__main__":
    main()
