"""Correlation analysis of weekday trip frequency versus on-time performance."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load per-route trip frequency, average OTP, and mode."""
    frequency = query_to_polars("""
        SELECT route_id,
               SUM(trips_wd) AS total_trips_wd,
               SUM(trips_7d) AS total_trips_7d
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
    return avg_otp.join(frequency, on="route_id", how="inner")


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, float]:
    """Compute Pearson correlation between weekday trips and OTP."""
    r = df.select(pl.corr("total_trips_wd", "avg_otp")).item()
    return df, r


def make_chart(df: pl.DataFrame, r: float) -> None:
    """Generate scatter plot of trip frequency vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["total_trips_wd"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Regression line
    x_vals = df["total_trips_wd"].to_list()
    y_vals = df["avg_otp"].to_list()
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
        ax.plot(x_line, y_line, color="#1e40af", linewidth=1.5, linestyle="--",
                label=f"trend (r={r:.3f})")

    ax.set_xlabel("Total Weekday Stop-Visits")
    ax.set_ylabel("Average OTP")
    ax.set_title("Trip Frequency vs On-Time Performance by Route")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)

    fig.tight_layout()
    fig.savefig(OUT / "frequency_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'frequency_vs_otp.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 10: Trip Frequency vs OTP")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df)} routes with both frequency and OTP data")

    print("\nAnalyzing...")
    df, r = analyze(df)
    print(f"  Pearson r = {r:.4f}")

    print("\nSaving CSV...")
    df.write_csv(OUT / "frequency_otp.csv")
    print(f"  Saved to {OUT / 'frequency_otp.csv'}")

    print("\nGenerating chart...")
    make_chart(df, r)

    print("\nDone.")


if __name__ == "__main__":
    main()
