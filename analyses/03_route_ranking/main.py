"""Route ranking by average OTP, trend slope, and volatility."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12  # minimum months of data to include in rankings


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load OTP data with route metadata, and stop counts per route."""
    otp = query_to_polars("""
        SELECT o.route_id, o.month, o.otp, r.route_name, r.mode
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
    """)
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops
        GROUP BY route_id
    """)
    return otp, stop_counts


def analyze(otp: pl.DataFrame, stop_counts: pl.DataFrame) -> pl.DataFrame:
    """Compute per-route summary stats, linear slope, and rankings."""
    # Assign numeric time index for slope calculation
    months_sorted = otp.select("month").unique().sort("month")
    months_sorted = months_sorted.with_row_index("time_idx")
    otp = otp.join(months_sorted, on="month")

    # Per-route summary stats
    summary = (
        otp.group_by(["route_id", "route_name", "mode"])
        .agg(
            months=pl.col("otp").count(),
            mean_otp=pl.col("otp").mean(),
            std_otp=pl.col("otp").std(),
            min_otp=pl.col("otp").min(),
            max_otp=pl.col("otp").max(),
            # Slope via formula: cov(time, otp) / var(time)
            slope=(
                (pl.col("time_idx") * pl.col("otp")).mean()
                - pl.col("time_idx").mean() * pl.col("otp").mean()
            )
            / pl.col("time_idx").var(),
        )
        .sort("route_id")
    )

    # Join stop counts
    summary = summary.join(stop_counts, on="route_id", how="left")

    # Flag limited-data routes
    summary = summary.with_columns(
        limited_data=pl.col("months") < MIN_MONTHS,
    )

    # Flag high-volatility routes (std > 2x median std across all routes)
    median_std = summary.filter(~pl.col("limited_data"))["std_otp"].median()
    summary = summary.with_columns(
        high_volatility=pl.col("std_otp") > (2 * median_std),
    )

    # Rankings (only for routes with sufficient data)
    rankable = summary.filter(~pl.col("limited_data"))
    avg_ranks = rankable.select("route_id", pl.col("mean_otp").rank(descending=True).alias("rank_avg"))
    slope_ranks = rankable.select("route_id", pl.col("slope").rank(descending=True).alias("rank_slope"))
    vol_ranks = rankable.select("route_id", pl.col("std_otp").rank(descending=False).alias("rank_volatility"))

    summary = (
        summary
        .join(avg_ranks, on="route_id", how="left")
        .join(slope_ranks, on="route_id", how="left")
        .join(vol_ranks, on="route_id", how="left")
    )

    return summary.sort("rank_avg", nulls_last=True)


def make_chart(df: pl.DataFrame) -> None:
    """Generate top/bottom routes bar charts."""
    plt = setup_plotting()
    from matplotlib.patches import Patch

    rankable = df.filter(~pl.col("limited_data"))
    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Top 10 and Bottom 10 by average OTP
    ax = axes[0]
    top10 = rankable.sort("mean_otp", descending=True).head(10)
    bottom10 = rankable.sort("mean_otp").head(10).sort("mean_otp", descending=True)
    combined = pl.concat([top10, bottom10])

    labels = [f"{r} - {n}" for r, n in zip(combined["route_id"].to_list(), combined["route_name"].to_list())]
    values = combined["mean_otp"].to_list()
    colors = [mode_colors.get(m, "#9ca3af") for m in combined["mode"].to_list()]

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Average OTP")
    ax.set_title("Top 10 & Bottom 10 Routes by Average OTP")
    ax.invert_yaxis()
    ax.set_xlim(0, 1)

    # Right: Top 10 improving and Top 10 declining by slope
    ax = axes[1]
    improving = rankable.sort("slope", descending=True).head(10)
    declining = rankable.sort("slope").head(10).sort("slope", descending=True)
    combined2 = pl.concat([improving, declining])

    labels2 = [f"{r} - {n}" for r, n in zip(combined2["route_id"].to_list(), combined2["route_name"].to_list())]
    values2 = combined2["slope"].to_list()
    colors2 = ["#22c55e" if v >= 0 else "#ef4444" for v in values2]

    y_pos2 = range(len(labels2))
    ax.barh(y_pos2, values2, color=colors2)
    ax.set_yticks(y_pos2)
    ax.set_yticklabels(labels2, fontsize=8)
    ax.set_xlabel("Slope (OTP change per month-index)")
    ax.set_title("Top 10 Improving & Declining Routes")
    ax.invert_yaxis()
    ax.axvline(0, color="black", linewidth=0.5)

    legend_patches = [Patch(facecolor=c, label=m) for m, c in mode_colors.items() if m != "UNKNOWN"]
    axes[0].legend(handles=legend_patches, loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT / "top_bottom_routes.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'top_bottom_routes.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 03: Route Ranking")
    print("=" * 60)

    print("\nLoading data...")
    otp, stop_counts = load_data()
    print(f"  {len(otp):,} OTP observations, {len(stop_counts)} routes with stop data")

    print("\nAnalyzing...")
    result = analyze(otp, stop_counts)
    rankable = result.filter(~pl.col("limited_data"))
    limited = result.filter(pl.col("limited_data"))
    print(f"  {len(rankable)} routes ranked ({MIN_MONTHS}+ months of data)")
    print(f"  {len(limited)} routes excluded (fewer than {MIN_MONTHS} months)")
    hv = result.filter(pl.col("high_volatility"))
    print(f"  {len(hv)} high-volatility routes flagged")

    print("\nSaving CSV...")
    result.write_csv(OUT / "route_ranking.csv")
    print(f"  Saved to {OUT / 'route_ranking.csv'}")

    print("\nGenerating chart...")
    make_chart(result)

    print("\nDone.")


if __name__ == "__main__":
    main()
