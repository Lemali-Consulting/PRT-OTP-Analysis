"""Route ranking by average OTP, trend slope, and volatility."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12  # minimum months of data to include in rankings
POST_COVID_START = "2022-01"  # start of post-COVID period for slope calculation


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
    """Compute per-route summary stats, post-COVID slope, and rankings."""
    # Per-route all-time summary stats
    summary = (
        otp.group_by(["route_id", "route_name", "mode"])
        .agg(
            months=pl.col("otp").count(),
            mean_otp=pl.col("otp").mean(),
            std_otp=pl.col("otp").std(),
            min_otp=pl.col("otp").min(),
            max_otp=pl.col("otp").max(),
        )
        .sort("route_id")
    )

    # Trailing 12-month average OTP
    all_months = otp.select("month").unique().sort("month")["month"].to_list()
    trailing_start = all_months[-12] if len(all_months) >= 12 else all_months[0]
    recent_avg = (
        otp.filter(pl.col("month") >= trailing_start)
        .group_by("route_id")
        .agg(recent_mean_otp=pl.col("otp").mean())
    )
    summary = summary.join(recent_avg, on="route_id", how="left")

    # Post-COVID slope (per year) using scipy.stats.linregress for SEs and CIs
    post_covid = otp.filter(pl.col("month") >= POST_COVID_START)
    pc_months = post_covid.select("month").unique().sort("month")
    pc_months = pc_months.with_row_index("time_idx")
    post_covid = post_covid.join(pc_months, on="month")

    # Compute actual time span (in months) for each route's post-COVID observations
    span_df = (
        post_covid.group_by("route_id")
        .agg(
            slope_months=pl.col("otp").count(),
            first_month=pl.col("month").min(),
            last_month=pl.col("month").max(),
            time_idx_min=pl.col("time_idx").min(),
            time_idx_max=pl.col("time_idx").max(),
        )
        .with_columns(
            obs_span_months=(pl.col("time_idx_max") - pl.col("time_idx_min") + 1).cast(pl.Int64),
        )
    )

    # Only keep routes with enough post-COVID data
    span_df = span_df.filter(pl.col("slope_months") >= MIN_MONTHS)

    # Compute slope, stderr, and CI per route using linregress (with zero-variance guard)
    slope_records = []
    for route_id in span_df["route_id"].to_list():
        route_data = post_covid.filter(pl.col("route_id") == route_id).sort("time_idx")
        x = route_data["time_idx"].to_numpy().astype(float)
        y = route_data["otp"].to_numpy().astype(float)

        # Zero-variance guard: if all time_idx values are the same, slope is undefined
        if np.var(x) == 0:
            slope_records.append({
                "route_id": route_id,
                "slope": 0.0,
                "slope_stderr": float("nan"),
                "slope_ci_lo": float("nan"),
                "slope_ci_hi": float("nan"),
                "slope_significant": False,
            })
            continue

        result = stats.linregress(x, y)
        slope_per_month = result.slope
        stderr_per_month = result.stderr
        # Convert to per-year units
        slope_yr = slope_per_month * 12
        stderr_yr = stderr_per_month * 12
        ci_lo = slope_yr - 1.96 * stderr_yr
        ci_hi = slope_yr + 1.96 * stderr_yr
        # Significant if 95% CI excludes zero
        significant = (ci_lo > 0) or (ci_hi < 0)

        slope_records.append({
            "route_id": route_id,
            "slope": slope_yr,
            "slope_stderr": stderr_yr,
            "slope_ci_lo": ci_lo,
            "slope_ci_hi": ci_hi,
            "slope_significant": significant,
        })

    slope_df = pl.DataFrame(slope_records)
    slope_df = slope_df.join(
        span_df.select("route_id", "slope_months", "obs_span_months", "first_month", "last_month"),
        on="route_id",
        how="left",
    )

    summary = summary.join(
        slope_df.select(
            "route_id", "slope", "slope_stderr", "slope_ci_lo", "slope_ci_hi",
            "slope_significant", "slope_months", "obs_span_months",
        ),
        on="route_id",
        how="left",
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
    avg_ranks = rankable.select("route_id", pl.col("recent_mean_otp").rank(descending=True).alias("rank_avg"))
    slope_ranks = rankable.filter(pl.col("slope").is_not_null()).select(
        "route_id", pl.col("slope").rank(descending=True).alias("rank_slope")
    )
    vol_ranks = rankable.select("route_id", pl.col("std_otp").rank(descending=False).alias("rank_volatility"))

    # Within-mode rank (rank routes within their mode group)
    mode_avg_ranks = (
        rankable.with_columns(
            mode_rank=pl.col("recent_mean_otp").rank(descending=True).over("mode")
        )
        .select("route_id", "mode_rank")
    )

    summary = (
        summary
        .join(avg_ranks, on="route_id", how="left")
        .join(slope_ranks, on="route_id", how="left")
        .join(vol_ranks, on="route_id", how="left")
        .join(mode_avg_ranks, on="route_id", how="left")
    )

    return summary.sort("rank_avg", nulls_last=True)


def make_chart(df: pl.DataFrame) -> None:
    """Generate top/bottom routes bar charts."""
    plt = setup_plotting()
    from matplotlib.patches import Patch

    rankable = df.filter(~pl.col("limited_data"))
    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Top 10 and Bottom 10 by recent average OTP
    ax = axes[0]
    has_recent = rankable.filter(pl.col("recent_mean_otp").is_not_null())
    top10 = has_recent.sort("recent_mean_otp", descending=True).head(10)
    bottom10 = has_recent.sort("recent_mean_otp").head(10).sort("recent_mean_otp", descending=True)
    combined = pl.concat([top10, bottom10])

    labels = [f"{r} - {n}" for r, n in zip(combined["route_id"].to_list(), combined["route_name"].to_list())]
    values = combined["recent_mean_otp"].to_list()
    colors = [mode_colors.get(m, "#9ca3af") for m in combined["mode"].to_list()]

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Average OTP (trailing 12 months)")
    ax.set_title("Top 10 & Bottom 10 Routes by Recent OTP")
    ax.invert_yaxis()
    ax.set_xlim(0, 1)

    # Right: Top 10 improving and Top 10 declining by post-COVID slope
    ax = axes[1]
    has_slope = rankable.filter(pl.col("slope").is_not_null())
    improving = has_slope.sort("slope", descending=True).head(10)
    declining = has_slope.sort("slope").head(10).sort("slope", descending=True)
    combined2 = pl.concat([improving, declining])

    labels2 = [f"{r} - {n}" for r, n in zip(combined2["route_id"].to_list(), combined2["route_name"].to_list())]
    values2 = combined2["slope"].to_list()
    colors2 = ["#22c55e" if v >= 0 else "#ef4444" for v in values2]

    y_pos2 = range(len(labels2))
    ax.barh(y_pos2, values2, color=colors2)
    ax.set_yticks(y_pos2)
    ax.set_yticklabels(labels2, fontsize=8)
    ax.set_xlabel("Slope (OTP change per year, post-2022)")
    ax.set_title("Top 10 Improving & Declining Routes (post-COVID)")
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
    print(f"  Slope period: {POST_COVID_START} onward (per-year units)")

    # Report slope significance
    has_slope = result.filter(pl.col("slope").is_not_null())
    sig_slopes = has_slope.filter(pl.col("slope_significant") == True)
    print(f"  {len(sig_slopes)} of {len(has_slope)} slopes are statistically significant (95% CI excludes zero)")

    # Report routes with null stop counts
    null_stops = result.filter(pl.col("stop_count").is_null())
    if len(null_stops) > 0:
        ids = null_stops["route_id"].to_list()
        print(f"  {len(null_stops)} routes lack stop count data: {', '.join(str(r) for r in ids)}")

    # Report modes
    for mode in sorted(rankable["mode"].unique().to_list()):
        mode_count = len(rankable.filter(pl.col("mode") == mode))
        print(f"  Mode {mode}: {mode_count} routes ranked")

    print("\nSaving CSV...")
    result.write_csv(OUT / "route_ranking.csv")
    print(f"  Saved to {OUT / 'route_ranking.csv'}")

    print("\nGenerating chart...")
    make_chart(result)

    print("\nDone.")


if __name__ == "__main__":
    main()
