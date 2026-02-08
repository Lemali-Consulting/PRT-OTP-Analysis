"""Scatter analysis of route stop count versus average on-time performance."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


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
    """)
    return avg_otp.join(stop_counts, on="route_id", how="inner")


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Compute Pearson and Spearman correlations, overall and bus-only."""
    results = {}

    # All routes
    r_all, p_all = stats.pearsonr(df["stop_count"].to_list(), df["avg_otp"].to_list())
    results["all_pearson_r"] = r_all
    results["all_pearson_p"] = p_all

    # Bus only
    bus = df.filter(pl.col("mode") == "BUS")
    r_bus, p_bus = stats.pearsonr(bus["stop_count"].to_list(), bus["avg_otp"].to_list())
    rho_bus, p_rho = stats.spearmanr(bus["stop_count"].to_list(), bus["avg_otp"].to_list())
    results["bus_pearson_r"] = r_bus
    results["bus_pearson_p"] = p_bus
    results["bus_spearman_r"] = rho_bus
    results["bus_spearman_p"] = p_rho
    results["bus_n"] = len(bus)

    return df, results


def make_chart(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter plot of stop count vs OTP with bus-only trendline."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["stop_count"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Bus-only regression line
    bus = df.filter(pl.col("mode") == "BUS")
    x_vals = bus["stop_count"].to_list()
    y_vals = bus["avg_otp"].to_list()
    n = len(x_vals)
    x_mean = sum(x_vals) / n
    y_mean = sum(y_vals) / n
    var_x = sum((xi - x_mean) ** 2 for xi in x_vals) / n
    if var_x > 0:
        cov_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x_vals, y_vals)) / n
        slope = cov_xy / var_x
        intercept = y_mean - slope * x_mean
        x_line = [min(x_vals), max(x_vals)]
        y_line = [slope * xi + intercept for xi in x_line]
        r_bus = results["bus_pearson_r"]
        p_bus = results["bus_pearson_p"]
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"BUS trend (r={r_bus:.3f}, p={p_bus:.3f})")

    ax.set_xlabel("Number of Stops")
    ax.set_ylabel("Average OTP")
    ax.set_title("Stop Count vs On-Time Performance by Route")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)

    fig.tight_layout()
    fig.savefig(OUT / "stop_count_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'stop_count_vs_otp.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 07: Stop Count vs OTP")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df)} routes with both stop count and OTP data")

    print("\nAnalyzing...")
    df, results = analyze(df)
    print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f})")
    print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
    print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
    print(f"               n = {results['bus_n']} bus routes")

    print("\nSaving CSV...")
    df.write_csv(OUT / "stop_count_otp.csv")
    print(f"  Saved to {OUT / 'stop_count_otp.csv'}")

    print("\nGenerating chart...")
    make_chart(df, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
