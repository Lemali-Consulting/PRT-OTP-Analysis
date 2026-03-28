"""Correlation analysis of weekday trip frequency versus on-time performance."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import correlate_by_mode, output_dir, print_done, print_header, query_to_polars, save_chart, save_csv, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load per-route peak trip frequency, average OTP, and mode."""
    frequency = query_to_polars("""
        SELECT route_id, MAX(trips_wd) AS max_trips_wd
        FROM route_stops
        WHERE trips_wd IS NOT NULL
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
    return avg_otp.join(frequency, on="route_id", how="inner")


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    """Compute Pearson and Spearman correlations, overall and bus-only."""
    corr = correlate_by_mode(df, "max_trips_wd", "avg_otp")
    results = {}
    results["all_pearson_r"] = corr["all"]["pearson_r"]
    results["all_pearson_p"] = corr["all"]["pearson_p"]
    results["bus_pearson_r"] = corr["bus"]["pearson_r"]
    results["bus_pearson_p"] = corr["bus"]["pearson_p"]
    results["bus_spearman_r"] = corr["bus"]["spearman_r"]
    results["bus_spearman_p"] = corr["bus"]["spearman_p"]
    results["bus_n"] = corr["bus"]["n"]

    return df, results


def make_chart(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter plot of trip frequency vs OTP with bus-only trendline."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["max_trips_wd"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Bus-only regression line
    bus = df.filter(pl.col("mode") == "BUS")
    x_vals = bus["max_trips_wd"].to_list()
    y_vals = bus["avg_otp"].to_list()
    if len(x_vals) > 1:
        reg = stats.linregress(x_vals, y_vals)
        x_line = [min(x_vals), max(x_vals)]
        y_line = [reg.slope * xi + reg.intercept for xi in x_line]
        r_bus = results["bus_pearson_r"]
        p_bus = results["bus_pearson_p"]
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"BUS trend (r={r_bus:.3f}, p={p_bus:.3f})")

    ax.set_xlabel("Peak Weekday Trips (max across stops)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Trip Frequency vs On-Time Performance by Route")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)

    save_chart(fig, OUT / "frequency_vs_otp.png")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print_header(10, "Trip Frequency vs OTP")

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df)} routes with both frequency and OTP data")

    print("\nAnalyzing...")
    df, results = analyze(df)
    print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f})")
    print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
    print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
    print(f"               n = {results['bus_n']} bus routes")

    print("\nSaving CSV...")
    save_csv(df, OUT / "frequency_otp.csv")

    print("\nGenerating chart...")
    make_chart(df, results)

    print_done()


if __name__ == "__main__":
    main()
