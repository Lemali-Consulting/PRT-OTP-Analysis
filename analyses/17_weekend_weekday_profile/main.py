"""Weekend vs weekday service profile analysis of on-time performance."""

import polars as pl

from prt_otp_analysis.common import MODE_COLORS, analysis_dir, correlate, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting

OUT = analysis_dir(__file__)

# Weekend-to-weekday service ratio boundaries for tier classification.
WEEKEND_RATIO_LOW = 0.3   # below = weekday-heavy
WEEKEND_RATIO_HIGH = 0.7  # above = weekend-heavy


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
    wkday_label = f"weekday-heavy (<{WEEKEND_RATIO_LOW})"
    balanced_label = f"balanced ({WEEKEND_RATIO_LOW}-{WEEKEND_RATIO_HIGH})"
    wkend_label = f"weekend-heavy (>{WEEKEND_RATIO_HIGH})"
    df = df.with_columns(
        pl.when(pl.col("weekend_ratio") < WEEKEND_RATIO_LOW).then(pl.lit(wkday_label))
        .when(pl.col("weekend_ratio") <= WEEKEND_RATIO_HIGH).then(pl.lit(balanced_label))
        .otherwise(pl.lit(wkend_label))
        .alias("service_tier")
    )

    return df


def analyze(df: pl.DataFrame) -> dict:
    """Compute correlations and tier statistics."""
    results = {}
    results["n_routes"] = len(df)

    # Filter to routes with weekday service for meaningful ratio
    with_wd = df.filter(pl.col("max_wd") > 0)

    all_corr = correlate(with_wd, "weekend_ratio", "avg_otp")
    results["ratio_r"] = all_corr["pearson_r"]
    results["ratio_p"] = all_corr["pearson_p"]
    results["ratio_rho"] = all_corr["spearman_r"]
    results["ratio_rho_p"] = all_corr["spearman_p"]

    # Bus-only (avoids Simpson's paradox)
    bus_wd = with_wd.filter(pl.col("mode") == "BUS")
    bus_corr = correlate(bus_wd, "weekend_ratio", "avg_otp")
    results["bus_ratio_r"] = bus_corr["pearson_r"]
    results["bus_ratio_p"] = bus_corr["pearson_p"]
    results["n_bus"] = bus_corr["n"]

    # Tier stats
    for tier_label in [f"weekday-heavy (<{WEEKEND_RATIO_LOW})", f"balanced ({WEEKEND_RATIO_LOW}-{WEEKEND_RATIO_HIGH})", f"weekend-heavy (>{WEEKEND_RATIO_HIGH})"]:
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
    # Scatter: weekend ratio vs OTP
    fig, ax = plt.subplots(figsize=(10, 7))
    for mode, color in MODE_COLORS.items():
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
    save_chart(fig, OUT / "weekend_ratio_vs_otp.png")

    # Box plot by service tier
    fig, ax = plt.subplots(figsize=(8, 6))
    tiers = [f"weekday-heavy (<{WEEKEND_RATIO_LOW})", f"balanced ({WEEKEND_RATIO_LOW}-{WEEKEND_RATIO_HIGH})", f"weekend-heavy (>{WEEKEND_RATIO_HIGH})"]
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
    save_chart(fig, OUT / "service_tier_comparison.png")


@run_analysis(17, "Weekend vs Weekday Service Profile")
def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
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

    save_csv(df, OUT / "service_profile.csv")

    print("\nGenerating charts...")
    make_charts(df, results)


if __name__ == "__main__":
    main()
