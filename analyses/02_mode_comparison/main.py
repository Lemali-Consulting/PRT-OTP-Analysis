"""Mode and route-type comparison: BUS vs RAIL, local vs limited vs express, with statistical tests."""

from pathlib import Path

import polars as pl
from scipy.stats import mannwhitneyu, ttest_rel

from prt_otp_analysis.common import (
    classify_bus_route,
    output_dir,
    query_to_polars,
    setup_plotting,
)

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load OTP data with route metadata, excluding UNKNOWN-mode routes."""
    return query_to_polars("""
        SELECT o.route_id, o.month, o.otp, r.route_name, r.mode,
               COALESCE(rs_agg.trips_7d, 0) AS trips_7d
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        LEFT JOIN (
            SELECT route_id, SUM(trips_7d) AS trips_7d
            FROM route_stops
            GROUP BY route_id
        ) rs_agg ON o.route_id = rs_agg.route_id
        WHERE r.mode != 'UNKNOWN'
    """)


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, dict]:
    """Compute OTP by mode, by bus subtype, paired-route comparisons, and statistical tests."""
    # Classify bus routes
    df = df.with_columns(
        bus_type=pl.when(pl.col("mode") == "BUS")
        .then(pl.col("route_id").map_elements(classify_bus_route, return_dtype=pl.String))
        .otherwise(pl.lit(None)),
    )

    # Mode-level monthly OTP (unweighted)
    mode_monthly = (
        df.group_by(["mode", "month"])
        .agg(
            avg_otp=pl.col("otp").mean(),
            route_count=pl.col("route_id").n_unique(),
        )
        .sort(["mode", "month"])
    )

    # Mode-level monthly OTP (trip-weighted)
    mode_monthly_weighted = (
        df.group_by(["mode", "month"])
        .agg(
            weighted_otp=pl.when(pl.col("trips_7d").sum() > 0)
            .then((pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum())
            .otherwise(pl.col("otp").mean()),
            route_count=pl.col("route_id").n_unique(),
        )
        .sort(["mode", "month"])
    )

    # Bus-subtype monthly OTP
    bus_monthly = (
        df.filter(pl.col("mode") == "BUS")
        .group_by(["bus_type", "month"])
        .agg(avg_otp=pl.col("otp").mean(), route_count=pl.col("route_id").n_unique())
        .sort(["bus_type", "month"])
    )

    # Paired route comparison: find base routes with L/X counterparts
    route_ids = df["route_id"].unique().to_list()
    pairs = []
    for rid in route_ids:
        if rid.endswith("L") and rid[:-1] in route_ids:
            pairs.append((rid[:-1], rid, "local-vs-limited"))
        elif rid.endswith("X") and rid[:-1] in route_ids:
            pairs.append((rid[:-1], rid, "local-vs-express"))

    pair_rows = []
    for base_id, variant_id, pair_type in pairs:
        base = df.filter(pl.col("route_id") == base_id).select("month", otp_base=pl.col("otp"))
        variant = df.filter(pl.col("route_id") == variant_id).select("month", otp_variant=pl.col("otp"))
        joined = base.join(variant, on="month")
        if len(joined) > 0:
            joined = joined.with_columns(
                base_id=pl.lit(base_id),
                variant_id=pl.lit(variant_id),
                pair_type=pl.lit(pair_type),
                otp_diff=pl.col("otp_variant") - pl.col("otp_base"),
            )
            pair_rows.append(joined)

    paired = pl.concat(pair_rows) if pair_rows else pl.DataFrame()

    # --- Statistical tests ---
    test_results = {}

    # Mann-Whitney U test: bus vs rail monthly OTP distributions
    bus_monthly_otp = mode_monthly.filter(pl.col("mode") == "BUS")["avg_otp"].to_list()
    rail_monthly_otp = mode_monthly.filter(pl.col("mode") == "RAIL")["avg_otp"].to_list()
    if len(bus_monthly_otp) > 0 and len(rail_monthly_otp) > 0:
        u_stat, u_pval = mannwhitneyu(rail_monthly_otp, bus_monthly_otp, alternative="two-sided")
        test_results["mann_whitney_u"] = u_stat
        test_results["mann_whitney_p"] = u_pval
        test_results["bus_n_months"] = len(bus_monthly_otp)
        test_results["rail_n_months"] = len(rail_monthly_otp)
        test_results["bus_median_otp"] = sorted(bus_monthly_otp)[len(bus_monthly_otp) // 2]
        test_results["rail_median_otp"] = sorted(rail_monthly_otp)[len(rail_monthly_otp) // 2]

    # Paired t-test for local vs limited route pairs
    if len(paired) > 0:
        pair_labels = paired.select("base_id", "variant_id").unique()
        pair_means = []
        for row in pair_labels.iter_rows(named=True):
            pair_data = paired.filter(
                (pl.col("base_id") == row["base_id"]) & (pl.col("variant_id") == row["variant_id"])
            )
            pair_means.append(pair_data["otp_diff"].mean())

        test_results["n_pairs"] = len(pair_means)
        test_results["pair_mean_diff"] = sum(pair_means) / len(pair_means) if pair_means else 0

        # Paired t-test on per-month differences across all pairs combined
        # For each pair, collect the per-month OTP differences
        all_base_otp = []
        all_variant_otp = []
        for row in pair_labels.iter_rows(named=True):
            pair_data = paired.filter(
                (pl.col("base_id") == row["base_id"]) & (pl.col("variant_id") == row["variant_id"])
            )
            all_base_otp.extend(pair_data["otp_base"].to_list())
            all_variant_otp.extend(pair_data["otp_variant"].to_list())

        if len(all_base_otp) >= 2:
            t_stat, t_pval = ttest_rel(all_variant_otp, all_base_otp)
            import numpy as np
            diffs = [v - b for v, b in zip(all_variant_otp, all_base_otp)]
            n = len(diffs)
            mean_diff = np.mean(diffs)
            se_diff = np.std(diffs, ddof=1) / np.sqrt(n)
            from scipy.stats import t as t_dist
            ci_margin = t_dist.ppf(0.975, df=n - 1) * se_diff
            test_results["paired_t_stat"] = t_stat
            test_results["paired_t_pval"] = t_pval
            test_results["paired_mean_diff"] = mean_diff
            test_results["paired_ci_lower"] = mean_diff - ci_margin
            test_results["paired_ci_upper"] = mean_diff + ci_margin
            test_results["paired_n_obs"] = n

    # Trip-weighted mode averages
    for mode in ["BUS", "RAIL"]:
        data = mode_monthly_weighted.filter(pl.col("mode") == mode)
        if len(data) > 0:
            test_results[f"{mode.lower()}_weighted_avg"] = data["weighted_otp"].mean()

    return mode_monthly, bus_monthly, paired, mode_monthly_weighted, test_results


def make_chart(
    mode_monthly: pl.DataFrame,
    bus_monthly: pl.DataFrame,
    paired: pl.DataFrame,
) -> None:
    """Generate a 4-panel mode comparison chart."""
    plt = setup_plotting()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b"}
    bus_type_colors = {"local": "#3b82f6", "limited": "#8b5cf6", "express": "#ef4444", "busway": "#f59e0b", "flyer": "#06b6d4"}

    # Top-left: Mode time series
    ax = axes[0, 0]
    for mode in ["BUS", "RAIL"]:
        data = mode_monthly.filter(pl.col("mode") == mode).sort("month")
        if len(data) == 0:
            continue
        months = data["month"].to_list()
        vals = data["avg_otp"].to_list()
        n_routes = int(data["route_count"].median())
        ax.plot(range(len(months)), vals, color=mode_colors[mode], linewidth=1.2,
                label=f"{mode} (n={n_routes} routes)")
        tick_pos = [i for i, m in enumerate(months) if m.endswith("-01")]
        tick_lbl = [months[i][:4] for i in tick_pos]
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_lbl)
    ax.set_title("OTP by Mode (UNKNOWN excluded)")
    ax.set_ylabel("Average OTP")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)

    # Top-right: Bus subtype time series
    ax = axes[0, 1]
    for btype in ["local", "limited", "express", "busway", "flyer"]:
        data = bus_monthly.filter(pl.col("bus_type") == btype).sort("month")
        if len(data) == 0:
            continue
        months = data["month"].to_list()
        vals = data["avg_otp"].to_list()
        ax.plot(range(len(months)), vals, color=bus_type_colors[btype], linewidth=1.2, label=btype)
        tick_pos = [i for i, m in enumerate(months) if m.endswith("-01")]
        tick_lbl = [months[i][:4] for i in tick_pos]
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_lbl)
    ax.set_title("OTP by Bus Type")
    ax.set_ylabel("Average OTP")
    ax.legend(fontsize=8)
    ax.set_ylim(0, 1)

    # Bottom-left: Paired route comparison
    ax = axes[1, 0]
    if len(paired) > 0:
        pair_labels = paired.select("base_id", "variant_id").unique()
        for row in pair_labels.iter_rows(named=True):
            pair_data = paired.filter(
                (pl.col("base_id") == row["base_id"]) & (pl.col("variant_id") == row["variant_id"])
            ).sort("month")
            months = pair_data["month"].to_list()
            diffs = pair_data["otp_diff"].to_list()
            ax.plot(range(len(months)), diffs, linewidth=0.8, alpha=0.7,
                    label=f"{row['base_id']} vs {row['variant_id']}")
            tick_pos = [i for i, m in enumerate(months) if m.endswith("-01")]
            tick_lbl = [months[i][:4] for i in tick_pos]
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(tick_lbl)
        ax.axhline(0, color="black", linewidth=0.5)
        ax.legend(fontsize=7, loc="lower left")
    ax.set_title("Paired Route OTP Difference (variant - base)")
    ax.set_ylabel("OTP Difference")

    # Bottom-right: Mode gap over time (RAIL - BUS)
    ax = axes[1, 1]
    rail = mode_monthly.filter(pl.col("mode") == "RAIL").select("month", rail_otp=pl.col("avg_otp"))
    bus = mode_monthly.filter(pl.col("mode") == "BUS").select("month", bus_otp=pl.col("avg_otp"))
    gap = rail.join(bus, on="month").sort("month")
    if len(gap) > 0:
        gap = gap.with_columns(gap_val=pl.col("rail_otp") - pl.col("bus_otp"))
        months = gap["month"].to_list()
        gap_vals = gap["gap_val"].to_list()
        x = list(range(len(months)))
        colors = ["#22c55e" if v >= 0 else "#ef4444" for v in gap_vals]
        ax.bar(x, gap_vals, color=colors, width=1.0, alpha=0.7)
        ax.axhline(0, color="black", linewidth=0.5)

        # Trend line
        n = len(x)
        x_mean = sum(x) / n
        y_mean = sum(gap_vals) / n
        cov_xy = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, gap_vals)) / n
        var_x = sum((xi - x_mean) ** 2 for xi in x) / n
        if var_x > 0:
            slope = cov_xy / var_x
            intercept = y_mean - slope * x_mean
            trend = [slope * xi + intercept for xi in x]
            ax.plot(x, trend, color="#1e40af", linewidth=1.5, linestyle="--", label=f"trend (slope={slope:.5f})")
            ax.legend(fontsize=8)

        tick_pos = [i for i, m in enumerate(months) if m.endswith("-01")]
        tick_lbl = [months[i][:4] for i in tick_pos]
        ax.set_xticks(tick_pos)
        ax.set_xticklabels(tick_lbl)
    ax.set_title("RAIL - BUS OTP Gap")
    ax.set_ylabel("OTP Difference")

    fig.suptitle("Mode & Route-Type Comparison", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "mode_comparison.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'mode_comparison.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 02: Mode Comparison")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} OTP observations loaded")

    print("\nAnalyzing...")
    mode_monthly, bus_monthly, paired, mode_monthly_weighted, test_results = analyze(df)

    # Summary
    for mode in ["BUS", "RAIL"]:
        data = mode_monthly.filter(pl.col("mode") == mode)
        if len(data) > 0:
            avg = data["avg_otp"].mean()
            print(f"  {mode}: overall avg OTP (unweighted) = {avg:.1%}")
        w_key = f"{mode.lower()}_weighted_avg"
        if w_key in test_results:
            print(f"  {mode}: overall avg OTP (trip-weighted) = {test_results[w_key]:.1%}")

    # Mann-Whitney test
    if "mann_whitney_u" in test_results:
        print(f"\n  Mann-Whitney U test (RAIL vs BUS monthly OTP):")
        print(f"    U = {test_results['mann_whitney_u']:.1f}, p = {test_results['mann_whitney_p']:.2e}")
        print(f"    RAIL median = {test_results['rail_median_otp']:.1%}, BUS median = {test_results['bus_median_otp']:.1%}")

    if len(paired) > 0:
        avg_diff = paired["otp_diff"].mean()
        print(f"\n  Paired routes: avg OTP diff (variant - base) = {avg_diff:+.4f}")
        print(f"  {paired.select('base_id', 'variant_id').unique().height} route pairs found")

        if "paired_t_stat" in test_results:
            print(f"  Paired t-test on monthly OTP differences:")
            print(f"    t = {test_results['paired_t_stat']:.3f}, p = {test_results['paired_t_pval']:.4f}")
            print(f"    Mean diff = {test_results['paired_mean_diff']:.4f}")
            print(f"    95% CI: [{test_results['paired_ci_lower']:.4f}, {test_results['paired_ci_upper']:.4f}]")
            print(f"    n = {test_results['paired_n_obs']} paired observations across {test_results['n_pairs']} pairs")

    print("\nSaving CSV...")
    # Combine mode and bus type data for CSV
    csv_data = pl.concat([
        mode_monthly.with_columns(bus_type=pl.lit(None, dtype=pl.String)),
        bus_monthly.with_columns(mode=pl.lit("BUS")),
    ], how="diagonal")
    csv_data.write_csv(OUT / "mode_comparison.csv")
    print(f"  Saved to {OUT / 'mode_comparison.csv'}")

    # Save weighted mode data
    mode_monthly_weighted.write_csv(OUT / "mode_comparison_weighted.csv")
    print(f"  Saved to {OUT / 'mode_comparison_weighted.csv'}")

    print("\nGenerating chart...")
    make_chart(mode_monthly, bus_monthly, paired)

    print("\nDone.")


if __name__ == "__main__":
    main()
