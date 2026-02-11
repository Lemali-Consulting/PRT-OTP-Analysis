"""Weekend vs weekday service profile analysis of on-time performance."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load per-route service profile and average OTP."""
    trips = query_to_polars("""
        SELECT route_id,
               MAX(trips_wd) AS max_wd,
               MAX(trips_sa) AS max_sa,
               MAX(trips_su) AS max_su
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
    df = avg_otp.join(trips, on="route_id", how="inner")

    # Weekend ratio: (sa + su) / (2 * wd), capped at 0 if no weekday service
    df = df.with_columns(
        pl.when(pl.col("max_wd") > 0)
        .then((pl.col("max_sa") + pl.col("max_su")) / (2.0 * pl.col("max_wd")))
        .otherwise(0.0)
        .alias("weekend_ratio")
    )

    # Classify service profile
    df = df.with_columns(
        pl.when(pl.col("weekend_ratio") < 0.3).then(pl.lit("weekday-heavy (<0.3)"))
        .when(pl.col("weekend_ratio") <= 0.7).then(pl.lit("balanced (0.3-0.7)"))
        .otherwise(pl.lit("weekend-heavy (>0.7)"))
        .alias("service_tier")
    )

    return df


def analyze(df: pl.DataFrame) -> dict:
    """Compute correlations and tier statistics."""
    results = {}
    results["n_routes"] = len(df)

    # Filter to routes with weekday service for meaningful ratio
    with_wd = df.filter(pl.col("max_wd") > 0)

    r, p = stats.pearsonr(with_wd["weekend_ratio"].to_list(), with_wd["avg_otp"].to_list())
    results["ratio_r"] = r
    results["ratio_p"] = p

    rho, p_rho = stats.spearmanr(with_wd["weekend_ratio"].to_list(), with_wd["avg_otp"].to_list())
    results["ratio_rho"] = rho
    results["ratio_rho_p"] = p_rho

    # Bus-only (avoids Simpson's paradox)
    bus_wd = with_wd.filter(pl.col("mode") == "BUS")
    r, p = stats.pearsonr(bus_wd["weekend_ratio"].to_list(), bus_wd["avg_otp"].to_list())
    results["bus_ratio_r"] = r
    results["bus_ratio_p"] = p
    results["n_bus"] = len(bus_wd)

    # Tier stats
    for tier_label in ["weekday-heavy (<0.3)", "balanced (0.3-0.7)", "weekend-heavy (>0.7)"]:
        subset = df.filter(pl.col("service_tier") == tier_label)
        key = tier_label.split(" ")[0]
        results[f"{key}_n"] = len(subset)
        if len(subset) > 0:
            results[f"{key}_mean_otp"] = subset["avg_otp"].mean()
            results[f"{key}_median_otp"] = subset["avg_otp"].median()

    return results


def make_charts(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter and box plots."""
    plt = setup_plotting()
    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    # Scatter: weekend ratio vs OTP
    fig, ax = plt.subplots(figsize=(10, 7))
    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(subset["weekend_ratio"].to_list(), subset["avg_otp"].to_list(),
                   color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Weekend/Weekday Service Ratio")
    ax.set_ylabel("Average OTP")
    ax.set_title(f"Weekend Service Ratio vs OTP (r={results['ratio_r']:.3f}, p={results['ratio_p']:.3f})")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.05, 1.5)
    fig.tight_layout()
    fig.savefig(OUT / "weekend_ratio_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'weekend_ratio_vs_otp.png'}")

    # Box plot by service tier
    fig, ax = plt.subplots(figsize=(8, 6))
    tiers = ["weekday-heavy (<0.3)", "balanced (0.3-0.7)", "weekend-heavy (>0.7)"]
    box_data = []
    box_labels = []
    for tier in tiers:
        vals = df.filter(pl.col("service_tier") == tier)["avg_otp"].to_list()
        if vals:
            box_data.append(vals)
            box_labels.append(f"{tier}\n(n={len(vals)})")
    bp = ax.boxplot(box_data, tick_labels=box_labels, patch_artist=True)
    colors = ["#ef4444", "#f59e0b", "#22c55e"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel("Average OTP")
    ax.set_title("OTP by Service Profile Tier")
    fig.tight_layout()
    fig.savefig(OUT / "service_tier_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'service_tier_comparison.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 17: Weekend vs Weekday Service Profile")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df)} routes with service profile and OTP data")

    print("\nAnalyzing...")
    results = analyze(df)
    print(f"  All-mode:  Pearson r = {results['ratio_r']:.4f} (p = {results['ratio_p']:.4f})")
    print(f"             Spearman rho = {results['ratio_rho']:.4f} (p = {results['ratio_rho_p']:.4f})")
    print(f"  Bus-only:  Pearson r = {results['bus_ratio_r']:.4f} (p = {results['bus_ratio_p']:.4f}), "
          f"n = {results['n_bus']}")
    for tier, key in [("Weekday-heavy", "weekday-heavy"), ("Balanced", "balanced"), ("Weekend-heavy", "weekend-heavy")]:
        n = results.get(f"{key}_n", 0)
        if n > 0:
            print(f"  {tier}: n={n}, mean OTP={results[f'{key}_mean_otp']:.1%}")

    print("\nSaving CSV...")
    df.write_csv(OUT / "service_profile.csv")
    print(f"  Saved to {OUT / 'service_profile.csv'}")

    print("\nGenerating charts...")
    make_charts(df, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
