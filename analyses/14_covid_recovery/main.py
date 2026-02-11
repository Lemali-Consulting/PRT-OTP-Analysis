"""COVID recovery analysis: which routes recovered and which didn't?"""

from pathlib import Path

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
MIN_MONTHS = 6


def load_data() -> tuple[pl.DataFrame, str, str]:
    """Compute pre-COVID baseline and current OTP for each route."""
    otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode, o.month, o.otp
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
    """)
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops
        GROUP BY route_id
    """)

    # Find the last 12 months in the dataset
    all_months = sorted(otp["month"].unique().to_list())
    current_months = all_months[-12:]
    current_start = current_months[0]
    current_end = current_months[-1]

    # Pre-COVID baseline
    baseline = (
        otp.filter((pl.col("month") >= PRE_COVID_START) & (pl.col("month") <= PRE_COVID_END))
        .group_by("route_id", "route_name", "mode")
        .agg(
            pl.col("otp").mean().alias("baseline_otp"),
            pl.col("otp").len().alias("baseline_months"),
        )
        .filter(pl.col("baseline_months") >= MIN_MONTHS)
    )

    # Current period
    current = (
        otp.filter(pl.col("month") >= current_start)
        .group_by("route_id")
        .agg(
            pl.col("otp").mean().alias("current_otp"),
            pl.col("otp").len().alias("current_months"),
        )
        .filter(pl.col("current_months") >= MIN_MONTHS)
    )

    df = baseline.join(current, on="route_id", how="inner")
    df = df.join(stop_counts, on="route_id", how="left")
    df = df.with_columns(
        (pl.col("current_otp") - pl.col("baseline_otp")).alias("recovery_delta"),
        (pl.col("current_otp") / pl.col("baseline_otp")).alias("recovery_ratio"),
    )
    # Add bus subtype
    df = df.with_columns(
        pl.when(pl.col("mode") == "BUS")
        .then(pl.col("route_id").map_elements(classify_bus_route, return_dtype=pl.Utf8))
        .otherwise(pl.col("mode").str.to_lowercase())
        .alias("subtype")
    )
    return df.sort("recovery_delta"), current_start, current_end


def analyze(df: pl.DataFrame) -> dict:
    """Compute summary statistics on recovery, including regression-to-the-mean test."""
    results = {}
    results["n_routes"] = len(df)
    results["median_delta"] = df["recovery_delta"].median()
    results["mean_delta"] = df["recovery_delta"].mean()
    results["n_improved"] = len(df.filter(pl.col("recovery_delta") > 0))
    results["n_declined"] = len(df.filter(pl.col("recovery_delta") < 0))

    # Correlation: stop count vs recovery delta (bus only)
    bus = df.filter(pl.col("mode") == "BUS").drop_nulls("stop_count")
    if len(bus) > 5:
        r, p = stats.pearsonr(bus["stop_count"].to_list(), bus["recovery_delta"].to_list())
        results["stops_recovery_r"] = r
        results["stops_recovery_p"] = p

    # Regression-to-the-mean test: baseline vs delta
    r, p = stats.pearsonr(df["baseline_otp"].to_list(), df["recovery_delta"].to_list())
    results["rtm_r"] = r
    results["rtm_p"] = p

    # Kruskal-Wallis test across subtypes (non-parametric, handles unequal groups)
    subtypes = sorted(df["subtype"].unique().to_list())
    groups = []
    for st in subtypes:
        vals = df.filter(pl.col("subtype") == st)["recovery_delta"].to_list()
        if len(vals) >= 3:
            groups.append(vals)
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        results["kruskal_h"] = h
        results["kruskal_p"] = p

    return results


def make_charts(df: pl.DataFrame, results: dict) -> None:
    """Generate recovery distribution, subtype box plot, and RTM scatter."""
    plt = setup_plotting()

    # Recovery distribution histogram
    fig, ax = plt.subplots(figsize=(10, 6))
    deltas = df["recovery_delta"].to_list()
    ax.hist(deltas, bins=25, color="#3b82f6", edgecolor="white", alpha=0.8)
    ax.axvline(0, color="#dc2626", linewidth=1.5, linestyle="--", label="No change")
    ax.axvline(results["median_delta"], color="#16a34a", linewidth=1.5, linestyle="--",
               label=f"Median ({results['median_delta']:+.1%})")
    ax.set_xlabel("OTP Change (Current - Pre-COVID)")
    ax.set_ylabel("Number of Routes")
    ax.set_title("Distribution of OTP Recovery from Pre-COVID Baseline")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "recovery_distribution.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'recovery_distribution.png'}")

    # Recovery by subtype box plot
    fig, ax = plt.subplots(figsize=(10, 6))
    subtypes = sorted(df["subtype"].unique().to_list())
    box_data = []
    box_labels = []
    for st in subtypes:
        vals = df.filter(pl.col("subtype") == st)["recovery_delta"].to_list()
        if len(vals) >= 3:
            box_data.append(vals)
            box_labels.append(f"{st}\n(n={len(vals)})")

    bp = ax.boxplot(box_data, tick_labels=box_labels, patch_artist=True)
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.axhline(0, color="#dc2626", linewidth=1, linestyle="--", alpha=0.5)
    ax.set_ylabel("OTP Change (Current - Pre-COVID)")
    ax.set_title("COVID Recovery by Route Type")
    fig.tight_layout()
    fig.savefig(OUT / "recovery_by_mode.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'recovery_by_mode.png'}")

    # Regression-to-the-mean scatter
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df["baseline_otp"].to_list(), df["recovery_delta"].to_list(),
               s=30, alpha=0.6, color="#3b82f6", edgecolors="white", linewidths=0.5)
    ax.axhline(0, color="#dc2626", linewidth=1, linestyle="--", alpha=0.5)
    import numpy as np
    x = np.array(df["baseline_otp"].to_list())
    y = np.array(df["recovery_delta"].to_list())
    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.array([x.min(), x.max()])
    ax.plot(x_line, slope * x_line + intercept, color="#1e40af", linewidth=1.5, linestyle="--",
            label=f"r={results['rtm_r']:.3f}, p={results['rtm_p']:.3f}")
    ax.set_xlabel("Pre-COVID Baseline OTP")
    ax.set_ylabel("OTP Change (Current - Baseline)")
    ax.set_title("Regression to the Mean Test")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "regression_to_mean.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'regression_to_mean.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 14: COVID Recovery Trajectories")
    print("=" * 60)

    print("\nLoading data...")
    df, current_start, current_end = load_data()
    print(f"  {len(df)} routes with both pre-COVID and current data")
    print(f"  Pre-COVID period: {PRE_COVID_START} to {PRE_COVID_END}")
    print(f"  Current period:   {current_start} to {current_end}")

    print("\nAnalyzing recovery...")
    results = analyze(df)
    print(f"  Improved: {results['n_improved']} routes")
    print(f"  Declined: {results['n_declined']} routes")
    print(f"  Median delta: {results['median_delta']:+.1%}")
    print(f"  Mean delta:   {results['mean_delta']:+.1%}")
    if "stops_recovery_r" in results:
        print(f"  Stop count vs recovery (bus): r = {results['stops_recovery_r']:.4f} "
              f"(p = {results['stops_recovery_p']:.4f})")
    print(f"\n  Regression-to-the-mean test:")
    print(f"    Baseline vs delta: r = {results['rtm_r']:.4f} (p = {results['rtm_p']:.4f})")
    if results['rtm_p'] < 0.05:
        print(f"    WARNING: Significant RTM detected -- routes with extreme baselines regress toward the mean.")
    else:
        print(f"    No significant RTM detected.")
    if "kruskal_h" in results:
        print(f"  Kruskal-Wallis test across subtypes: H = {results['kruskal_h']:.3f}, "
              f"p = {results['kruskal_p']:.4f}")

    # Top/bottom routes
    print("\nMost improved:")
    top = df.sort("recovery_delta", descending=True).head(5)
    for row in top.iter_rows(named=True):
        print(f"  {row['route_id']:>5s} - {row['route_name']:<30s} "
              f"Baseline={row['baseline_otp']:.1%} -> Current={row['current_otp']:.1%} "
              f"({row['recovery_delta']:+.1%})")

    print("\nMost declined:")
    bottom = df.sort("recovery_delta").head(5)
    for row in bottom.iter_rows(named=True):
        print(f"  {row['route_id']:>5s} - {row['route_name']:<30s} "
              f"Baseline={row['baseline_otp']:.1%} -> Current={row['current_otp']:.1%} "
              f"({row['recovery_delta']:+.1%})")

    print("\nSaving CSV...")
    df.write_csv(OUT / "covid_recovery.csv")
    print(f"  Saved to {OUT / 'covid_recovery.csv'}")

    print("\nGenerating charts...")
    make_charts(df, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
