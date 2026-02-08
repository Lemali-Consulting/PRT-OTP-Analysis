"""Analysis of inbound vs outbound trip asymmetry and its correlation with OTP."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load directional trip counts and average OTP per route."""
    directional = query_to_polars("""
        SELECT route_id, direction,
               SUM(trips_wd) AS trips_wd,
               SUM(trips_7d) AS trips_7d
        FROM route_stops
        WHERE direction IN ('IB', 'OB')
        GROUP BY route_id, direction
    """)
    avg_otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
    """)
    return directional, avg_otp


def analyze(directional: pl.DataFrame, avg_otp: pl.DataFrame) -> tuple[pl.DataFrame, float]:
    """Compute asymmetry index per route and correlate with OTP."""
    # Pivot to get IB and OB columns
    pivoted = directional.pivot(on="direction", index="route_id", values="trips_wd")

    # Rename columns safely
    if "IB" in pivoted.columns and "OB" in pivoted.columns:
        pivoted = pivoted.rename({"IB": "ib_trips_wd", "OB": "ob_trips_wd"})
    else:
        print("  Warning: Missing IB or OB direction data")
        return pl.DataFrame(), 0.0

    # Fill nulls (routes that only have one direction)
    pivoted = pivoted.with_columns(
        pl.col("ib_trips_wd").fill_null(0),
        pl.col("ob_trips_wd").fill_null(0),
    )

    # Compute asymmetry index
    pivoted = pivoted.with_columns(
        total_trips=pl.col("ib_trips_wd") + pl.col("ob_trips_wd"),
    )
    pivoted = pivoted.filter(pl.col("total_trips") > 0)
    pivoted = pivoted.with_columns(
        asymmetry_index=(
            (pl.col("ib_trips_wd") - pl.col("ob_trips_wd")).abs()
            / pl.col("total_trips")
        ),
    )

    # Join with OTP
    result = pivoted.join(avg_otp, on="route_id", how="inner")

    # Correlation
    r = result.select(pl.corr("asymmetry_index", "avg_otp")).item()

    return result.sort("asymmetry_index", descending=True), r


def make_chart(df: pl.DataFrame, r: float) -> None:
    """Generate scatter plot of directional asymmetry vs OTP."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(
            subset["asymmetry_index"].to_list(),
            subset["avg_otp"].to_list(),
            color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5,
        )

    # Regression line
    x_vals = df["asymmetry_index"].to_list()
    y_vals = df["avg_otp"].to_list()
    n = len(x_vals)
    if n > 1:
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

    ax.set_xlabel("Directional Asymmetry Index |IB - OB| / (IB + OB)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Directional Trip Asymmetry vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.05, 1.05)

    fig.tight_layout()
    fig.savefig(OUT / "directional_asymmetry.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'directional_asymmetry.png'}")


def main() -> None:
    """Entry point: load data, analyze asymmetry, chart, and save."""
    print("=" * 60)
    print("Analysis 11: Directional Asymmetry")
    print("=" * 60)

    print("\nLoading data...")
    directional, avg_otp = load_data()
    print(f"  {len(directional)} directional records, {len(avg_otp)} routes with OTP")

    print("\nAnalyzing...")
    result, r = analyze(directional, avg_otp)
    if len(result) == 0:
        print("  No data to analyze.")
        return

    print(f"  {len(result)} routes analyzed")
    print(f"  Pearson r (asymmetry vs OTP) = {r:.4f}")

    top5 = result.head(5)
    print("\n  Most asymmetric routes:")
    for row in top5.iter_rows(named=True):
        print(f"    {row['route_id']:>5} - {row['route_name']}: "
              f"IB={row['ib_trips_wd']}, OB={row['ob_trips_wd']}, "
              f"asymmetry={row['asymmetry_index']:.3f}, OTP={row['avg_otp']:.1%}")

    print("\nSaving CSV...")
    result.write_csv(OUT / "directional_asymmetry.csv")
    print(f"  Saved to {OUT / 'directional_asymmetry.csv'}")

    print("\nGenerating chart...")
    make_chart(result, r)

    print("\nDone.")


if __name__ == "__main__":
    main()
