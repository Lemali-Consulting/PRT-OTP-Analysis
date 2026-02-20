"""Analysis 21: Compare ridership recovery trajectories with OTP recovery trajectories post-COVID."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    classify_bus_route,
    output_dir,
    query_to_polars,
    setup_plotting,
)

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

PRE_COVID_START = "2019-01"
PRE_COVID_END = "2020-02"
RECOVERY_START = "2023-01"
RECOVERY_END = "2024-10"
MIN_MONTHS = 6


def load_data() -> pl.DataFrame:
    """Compute pre-COVID and recovery-period averages for both OTP and ridership per route."""
    paired = query_to_polars("""
        SELECT o.route_id, r2.route_name, r2.mode, o.month, o.otp, r.avg_riders
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        JOIN routes r2 ON o.route_id = r2.route_id
    """)

    # Pre-COVID baseline
    pre = (
        paired.filter(
            (pl.col("month") >= PRE_COVID_START) & (pl.col("month") <= PRE_COVID_END)
        )
        .group_by("route_id", "route_name", "mode")
        .agg(
            baseline_otp=pl.col("otp").mean(),
            baseline_riders=pl.col("avg_riders").mean(),
            baseline_months=pl.col("month").count(),
        )
        .filter(pl.col("baseline_months") >= MIN_MONTHS)
    )

    # Recovery period
    post = (
        paired.filter(
            (pl.col("month") >= RECOVERY_START) & (pl.col("month") <= RECOVERY_END)
        )
        .group_by("route_id")
        .agg(
            recovery_otp=pl.col("otp").mean(),
            recovery_riders=pl.col("avg_riders").mean(),
            recovery_months=pl.col("month").count(),
        )
        .filter(pl.col("recovery_months") >= MIN_MONTHS)
    )

    df = pre.join(post, on="route_id", how="inner")

    # Compute deltas and ratios
    df = df.with_columns(
        otp_delta=(pl.col("recovery_otp") - pl.col("baseline_otp")),
        ridership_pct_change=(
            (pl.col("recovery_riders") - pl.col("baseline_riders")) / pl.col("baseline_riders")
        ),
    )

    # Add subtype
    df = df.with_columns(
        pl.when(pl.col("mode") == "BUS")
        .then(pl.col("route_id").map_elements(classify_bus_route, return_dtype=pl.Utf8))
        .otherwise(pl.col("mode").str.to_lowercase())
        .alias("subtype")
    )

    return df.sort("route_id")


def analyze(df: pl.DataFrame) -> dict:
    """Test correlation between ridership recovery and OTP recovery."""
    results = {"n_routes": len(df)}

    otp_d = df["otp_delta"].to_numpy()
    rider_r = df["ridership_pct_change"].to_numpy()

    # Pearson
    r_p, p_p = stats.pearsonr(rider_r, otp_d)
    results["pearson_r"] = r_p
    results["pearson_p"] = p_p

    # Spearman
    r_s, p_s = stats.spearmanr(rider_r, otp_d)
    results["spearman_r"] = r_s
    results["spearman_p"] = p_s

    # Summary counts
    results["n_both_improved"] = int(((otp_d > 0) & (rider_r > 0)).sum())
    results["n_both_declined"] = int(((otp_d < 0) & (rider_r < 0)).sum())
    results["n_otp_up_riders_down"] = int(((otp_d > 0) & (rider_r < 0)).sum())
    results["n_otp_down_riders_up"] = int(((otp_d < 0) & (rider_r > 0)).sum())

    # Kruskal-Wallis across subtypes for OTP delta
    subtypes = sorted(df["subtype"].unique().to_list())
    groups = []
    for st in subtypes:
        vals = df.filter(pl.col("subtype") == st)["otp_delta"].to_list()
        if len(vals) >= 3:
            groups.append(vals)
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        results["kruskal_h"] = h
        results["kruskal_p"] = p

    return results


def make_scatter(df: pl.DataFrame, results: dict) -> None:
    """Scatter plot: ridership recovery vs OTP recovery, colored by subtype."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 8))

    subtype_colors = {
        "local": "#3b82f6",
        "limited": "#22c55e",
        "express": "#f59e0b",
        "busway": "#8b5cf6",
        "flyer": "#06b6d4",
        "rail": "#ef4444",
        "unknown": "#9ca3af",
    }

    for st in sorted(df["subtype"].unique().to_list()):
        sdf = df.filter(pl.col("subtype") == st)
        ax.scatter(
            sdf["ridership_pct_change"].to_list(),
            sdf["otp_delta"].to_list(),
            s=40, alpha=0.7,
            color=subtype_colors.get(st, "#9ca3af"),
            edgecolors="white", linewidths=0.5,
            label=f"{st} (n={len(sdf)})",
        )

    # Reference lines
    ax.axhline(0, color="black", linewidth=0.5, alpha=0.5)
    ax.axvline(0, color="black", linewidth=0.5, alpha=0.5)

    # Regression line
    x = df["ridership_pct_change"].to_numpy()
    y = df["otp_delta"].to_numpy()
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.array([x.min(), x.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#1e40af", linewidth=1.5,
            linestyle="--", label=f"r={results['pearson_r']:.3f}, p={results['pearson_p']:.3f}")

    # Quadrant labels
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    ax.text(xlim[1] * 0.7, ylim[1] * 0.85, f"Both improved\n(n={results['n_both_improved']})",
            ha="center", fontsize=8, color="#16a34a", alpha=0.8)
    ax.text(xlim[0] * 0.7, ylim[0] * 0.85, f"Both declined\n(n={results['n_both_declined']})",
            ha="center", fontsize=8, color="#dc2626", alpha=0.8)
    ax.text(xlim[0] * 0.7, ylim[1] * 0.85, f"Riders down,\nOTP up (n={results['n_otp_up_riders_down']})",
            ha="center", fontsize=8, color="#9ca3af", alpha=0.8)
    ax.text(xlim[1] * 0.7, ylim[0] * 0.85, f"Riders up,\nOTP down (n={results['n_otp_down_riders_up']})",
            ha="center", fontsize=8, color="#9ca3af", alpha=0.8)

    ax.set_xlabel("Ridership Change (recovery / baseline - 1)")
    ax.set_ylabel("OTP Change (recovery - baseline)")
    ax.set_title("COVID Recovery: Ridership vs OTP by Route")
    ax.legend(loc="upper left", fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT / "recovery_scatter.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'recovery_scatter.png'}")


def make_subtype_chart(df: pl.DataFrame) -> None:
    """Side-by-side box plots: ridership recovery and OTP recovery by subtype."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    subtypes = sorted(df["subtype"].unique().to_list())
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#9ca3af"]

    # OTP recovery by subtype
    otp_data = []
    labels = []
    for st in subtypes:
        vals = df.filter(pl.col("subtype") == st)["otp_delta"].to_list()
        if len(vals) >= 3:
            otp_data.append(vals)
            labels.append(f"{st}\n(n={len(vals)})")

    bp1 = ax1.boxplot(otp_data, tick_labels=labels, patch_artist=True)
    for patch, color in zip(bp1["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax1.axhline(0, color="#dc2626", linewidth=1, linestyle="--", alpha=0.5)
    ax1.set_ylabel("OTP Change (recovery - baseline)")
    ax1.set_title("OTP Recovery by Subtype")

    # Ridership recovery by subtype
    rider_data = []
    labels2 = []
    for st in subtypes:
        vals = df.filter(pl.col("subtype") == st)["ridership_pct_change"].to_list()
        if len(vals) >= 3:
            rider_data.append(vals)
            labels2.append(f"{st}\n(n={len(vals)})")

    bp2 = ax2.boxplot(rider_data, tick_labels=labels2, patch_artist=True)
    for patch, color in zip(bp2["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax2.axhline(0, color="#dc2626", linewidth=1, linestyle="--", alpha=0.5)
    ax2.set_ylabel("Ridership Change (recovery / baseline - 1)")
    ax2.set_title("Ridership Recovery by Subtype")

    fig.tight_layout()
    fig.savefig(OUT / "recovery_by_subtype.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'recovery_by_subtype.png'}")


def main() -> None:
    """Entry point: load, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 21: COVID Ridership vs OTP Recovery")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df)} routes with both pre-COVID and recovery data")
    print(f"  Pre-COVID: {PRE_COVID_START} to {PRE_COVID_END}")
    print(f"  Recovery:  {RECOVERY_START} to {RECOVERY_END}")

    print("\nAnalyzing...")
    results = analyze(df)

    print(f"\n  Quadrant breakdown:")
    print(f"    Both improved:           {results['n_both_improved']}")
    print(f"    Both declined:           {results['n_both_declined']}")
    print(f"    OTP up, riders down:     {results['n_otp_up_riders_down']}")
    print(f"    OTP down, riders up:     {results['n_otp_down_riders_up']}")

    print(f"\n  Ridership recovery vs OTP recovery:")
    print(f"    Pearson:  r = {results['pearson_r']:.4f}, p = {results['pearson_p']:.4f}")
    print(f"    Spearman: r = {results['spearman_r']:.4f}, p = {results['spearman_p']:.4f}")

    if "kruskal_h" in results:
        print(f"\n  Kruskal-Wallis (OTP delta by subtype):")
        print(f"    H = {results['kruskal_h']:.3f}, p = {results['kruskal_p']:.4f}")

    # System-wide ridership recovery
    median_rider = df["ridership_pct_change"].median()
    mean_rider = df["ridership_pct_change"].mean()
    print(f"\n  System ridership recovery:")
    print(f"    Median: {median_rider:+.1%}")
    print(f"    Mean:   {mean_rider:+.1%}")
    n_rider_recovered = df.filter(pl.col("ridership_pct_change") >= 0).height
    print(f"    Routes at/above pre-COVID: {n_rider_recovered}/{len(df)}")

    # Extreme routes
    print("\n  Most ridership recovery with OTP decline:")
    worst = (
        df.filter((pl.col("ridership_pct_change") > 0) & (pl.col("otp_delta") < -0.05))
        .sort("otp_delta")
        .head(5)
    )
    for row in worst.iter_rows(named=True):
        print(f"    {row['route_id']:>5s} - {row['route_name']:<30s}  "
              f"riders {row['ridership_pct_change']:+.0%}, OTP {row['otp_delta']:+.1%}")

    print("\n  Most ridership loss with OTP improvement:")
    best = (
        df.filter((pl.col("ridership_pct_change") < -0.1) & (pl.col("otp_delta") > 0))
        .sort("otp_delta", descending=True)
        .head(5)
    )
    for row in best.iter_rows(named=True):
        print(f"    {row['route_id']:>5s} - {row['route_name']:<30s}  "
              f"riders {row['ridership_pct_change']:+.0%}, OTP {row['otp_delta']:+.1%}")

    print("\nSaving CSV...")
    df.write_csv(OUT / "recovery_data.csv")
    print(f"  {OUT / 'recovery_data.csv'}")

    print("\nGenerating charts...")
    make_scatter(df, results)
    make_subtype_chart(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
