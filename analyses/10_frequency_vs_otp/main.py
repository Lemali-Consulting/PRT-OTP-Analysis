"""Correlation analysis of weekday trip frequency versus on-time performance."""

import polars as pl

from prt_otp_analysis.common import analysis_dir, correlate_by_mode, mode_scatter, phase, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)


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
    return df, correlate_by_mode(df, "max_trips_wd", "avg_otp")


def make_chart(df: pl.DataFrame) -> None:
    """Generate scatter plot of trip frequency vs OTP with bus-only trendline."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))
    mode_scatter(ax, df, "max_trips_wd", "avg_otp")
    ax.set_xlabel("Peak Weekday Trips (max across stops)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Trip Frequency vs On-Time Performance by Route")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    save_chart(fig, OUT / "frequency_vs_otp.png")


@run_analysis(10, "Trip Frequency vs OTP")
def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    with phase("Loading data"):
        df = load_data()
        print(f"  {len(df)} routes with both frequency and OTP data")

    with phase("Analyzing"):
        df, results = analyze(df)
        print(f"  All routes:  Pearson r = {results['all_pearson_r']:.4f} (p = {results['all_pearson_p']:.4f})")
        print(f"  Bus only:    Pearson r = {results['bus_pearson_r']:.4f} (p = {results['bus_pearson_p']:.4f})")
        print(f"               Spearman r = {results['bus_spearman_r']:.4f} (p = {results['bus_spearman_p']:.4f})")
        print(f"               n = {results['bus_n']} bus routes")

    with phase("Saving CSV"):
        save_csv(df, OUT / "frequency_otp.csv")

    with phase("Generating chart"):
        make_chart(df)


if __name__ == "__main__":
    main()
