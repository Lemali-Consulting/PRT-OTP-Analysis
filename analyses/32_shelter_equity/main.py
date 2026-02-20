"""Assess whether bus shelters are equitably placed relative to stop-level ridership."""

from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"


def load_stop_usage() -> pl.DataFrame:
    """Load pre-pandemic weekday usage aggregated to the physical-stop level."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])

    # Pre-pandemic weekday only
    df = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )

    # Aggregate to physical stop: sum usage across routes, average across datekeys
    stop_route = (
        df.group_by(["stop_id", "route_name", "datekey"])
        .agg(
            pl.col("avg_ons").first(),
            pl.col("avg_offs").first(),
            pl.col("stop_name").first(),
            pl.col("latitude").first().alias("lat"),
            pl.col("longitude").first().alias("lon"),
            pl.col("shelter").first(),
            pl.col("mode").first(),
            pl.col("stop_type").first(),
        )
    )

    # Average across datekeys, then sum across routes for each physical stop
    per_stop_route = (
        stop_route.group_by(["stop_id", "route_name"])
        .agg(
            pl.col("avg_ons").mean(),
            pl.col("avg_offs").mean(),
            pl.col("stop_name").first(),
            pl.col("lat").first(),
            pl.col("lon").first(),
            pl.col("shelter").first(),
            pl.col("mode").first(),
            pl.col("stop_type").first(),
        )
    )

    per_stop = (
        per_stop_route.group_by("stop_id")
        .agg(
            pl.col("avg_ons").sum(),
            pl.col("avg_offs").sum(),
            pl.col("stop_name").first(),
            pl.col("lat").first(),
            pl.col("lon").first(),
            pl.col("shelter").first(),
            pl.col("mode").first(),
            pl.col("stop_type").first(),
        )
        .with_columns(
            (pl.col("avg_ons") + pl.col("avg_offs")).alias("avg_daily_usage"),
            pl.when(pl.col("shelter").is_not_null() & (pl.col("shelter") != "No Shelter"))
            .then(True)
            .otherwise(False)
            .alias("has_shelter"),
        )
    )
    return per_stop


def analyze(df: pl.DataFrame) -> dict:
    """Compute shelter equity statistics."""
    results = {}

    sheltered = df.filter(pl.col("has_shelter"))
    unsheltered = df.filter(~pl.col("has_shelter"))

    results["n_stops"] = len(df)
    results["n_sheltered"] = len(sheltered)
    results["n_unsheltered"] = len(unsheltered)
    results["pct_sheltered"] = len(sheltered) / len(df) * 100

    results["sheltered_median_usage"] = sheltered["avg_daily_usage"].median()
    results["unsheltered_median_usage"] = unsheltered["avg_daily_usage"].median()
    results["sheltered_mean_usage"] = sheltered["avg_daily_usage"].mean()
    results["unsheltered_mean_usage"] = unsheltered["avg_daily_usage"].mean()

    # Share of total ridership at sheltered stops
    total_usage = df["avg_daily_usage"].sum()
    results["sheltered_ridership_share"] = sheltered["avg_daily_usage"].sum() / total_usage * 100

    # Mann-Whitney U test
    u_stat, p_val = stats.mannwhitneyu(
        sheltered["avg_daily_usage"].drop_nulls().to_list(),
        unsheltered["avg_daily_usage"].drop_nulls().to_list(),
        alternative="greater",
    )
    results["mannwhitney_u"] = u_stat
    results["mannwhitney_p"] = p_val

    return results


def shelter_by_mode(df: pl.DataFrame) -> pl.DataFrame:
    """Compute shelter coverage rate by mode."""
    return (
        df.filter(pl.col("mode").is_not_null())
        .group_by("mode")
        .agg(
            pl.len().alias("n_stops"),
            pl.col("has_shelter").sum().alias("n_sheltered"),
            pl.col("avg_daily_usage").mean().alias("mean_usage"),
        )
        .with_columns(
            (pl.col("n_sheltered") / pl.col("n_stops") * 100).alias("pct_sheltered")
        )
        .sort("pct_sheltered", descending=True)
    )


def shelter_by_owner(df: pl.DataFrame) -> pl.DataFrame:
    """Break down sheltered stops by owner."""
    return (
        df.filter(pl.col("has_shelter"))
        .group_by("shelter")
        .agg(
            pl.len().alias("n_stops"),
            pl.col("avg_daily_usage").sum().alias("total_usage"),
            pl.col("avg_daily_usage").mean().alias("mean_usage"),
        )
        .sort("n_stops", descending=True)
    )


def make_charts(df: pl.DataFrame, mode_df: pl.DataFrame, owner_df: pl.DataFrame) -> None:
    """Generate shelter equity charts."""
    plt = setup_plotting()

    # --- Box plot: ridership by shelter status ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sheltered_usage = df.filter(pl.col("has_shelter"))["avg_daily_usage"].drop_nulls().to_list()
    unsheltered_usage = df.filter(~pl.col("has_shelter"))["avg_daily_usage"].drop_nulls().to_list()

    bp = axes[0].boxplot(
        [unsheltered_usage, sheltered_usage],
        tick_labels=["No Shelter", "Has Shelter"],
        showfliers=False, patch_artist=True,
        medianprops=dict(color="black", linewidth=2),
    )
    bp["boxes"][0].set_facecolor("#f87171")
    bp["boxes"][1].set_facecolor("#34d399")
    axes[0].set_ylabel("Avg Daily Usage (ons + offs)")
    axes[0].set_title("Stop Usage by Shelter Status")

    # Overlay means
    means = [np.mean(unsheltered_usage), np.mean(sheltered_usage)]
    axes[0].scatter([1, 2], means, color="black", marker="D", s=50, zorder=3, label="Mean")
    axes[0].legend()

    # --- Bar chart: shelter coverage by mode ---
    modes = mode_df["mode"].to_list()
    pcts = mode_df["pct_sheltered"].to_list()
    colors = ["#3b82f6", "#22c55e", "#f59e0b", "#9ca3af"]
    bars = axes[1].bar(modes, pcts, color=colors[:len(modes)], edgecolor="white")
    axes[1].set_ylabel("% of Stops with Shelter")
    axes[1].set_title("Shelter Coverage by Mode")
    axes[1].set_ylim(0, 100)
    for bar, pct in zip(bars, pcts):
        axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                     f"{pct:.0f}%", ha="center", fontsize=10)

    fig.tight_layout()
    fig.savefig(OUT / "ridership_by_shelter.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'ridership_by_shelter.png'}")

    # --- Shelter owner breakdown ---
    fig, ax = plt.subplots(figsize=(10, 5))
    owners = owner_df["shelter"].to_list()
    counts = owner_df["n_stops"].to_list()
    mean_usages = owner_df["mean_usage"].to_list()
    ax.barh(range(len(owners)), counts, color="#3b82f6", edgecolor="white")
    ax.set_yticks(range(len(owners)))
    ax.set_yticklabels(owners)
    ax.invert_yaxis()
    ax.set_xlabel("Number of Sheltered Stops")
    ax.set_title("Shelter Count by Owner")
    for i, (cnt, mu) in enumerate(zip(counts, mean_usages)):
        ax.text(cnt + 1, i, f"avg {mu:.0f}/day", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "shelter_coverage_by_mode.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'shelter_coverage_by_mode.png'}")


def main() -> None:
    """Entry point: load data, analyze shelter equity, chart, and save."""
    print("=" * 60)
    print("Analysis 32: Shelter Equity")
    print("=" * 60)

    print("\nLoading stop-level usage (pre-pandemic weekday)...")
    df = load_stop_usage()
    print(f"  {len(df):,} unique physical stops")

    print("\nAnalyzing shelter equity...")
    results = analyze(df)
    print(f"  Sheltered: {results['n_sheltered']:,} ({results['pct_sheltered']:.1f}%)")
    print(f"  Unsheltered: {results['n_unsheltered']:,}")
    print(f"  Median usage -- sheltered: {results['sheltered_median_usage']:.1f}, unsheltered: {results['unsheltered_median_usage']:.1f}")
    print(f"  Mean usage -- sheltered: {results['sheltered_mean_usage']:.1f}, unsheltered: {results['unsheltered_mean_usage']:.1f}")
    print(f"  Sheltered stops serve {results['sheltered_ridership_share']:.1f}% of total ridership")
    print(f"  Mann-Whitney U p-value: {results['mannwhitney_p']:.2e}")

    print("\nShelter coverage by mode:")
    mode_df = shelter_by_mode(df)
    for row in mode_df.iter_rows(named=True):
        print(f"  {row['mode']:12s}: {row['pct_sheltered']:.0f}% sheltered ({row['n_stops']} stops)")

    print("\nShelter owner breakdown:")
    owner_df = shelter_by_owner(df)
    for row in owner_df.iter_rows(named=True):
        print(f"  {row['shelter']:25s}: {row['n_stops']:4d} stops, avg {row['mean_usage']:.0f}/day")

    print("\nTop 20 unsheltered stops by usage:")
    priority = (
        df.filter(~pl.col("has_shelter"))
        .sort("avg_daily_usage", descending=True)
        .head(20)
        .select("stop_id", "stop_name", "mode", "avg_daily_usage", "lat", "lon")
    )
    for row in priority.iter_rows(named=True):
        print(f"  {row['stop_id']:8s} {row['stop_name'][:40]:40s} {row['avg_daily_usage']:8.1f}/day")

    print("\nSaving CSVs...")
    df.write_csv(OUT / "shelter_equity_summary.csv")
    print(f"  Saved {OUT / 'shelter_equity_summary.csv'}")
    unsheltered_priority = (
        df.filter(~pl.col("has_shelter"))
        .sort("avg_daily_usage", descending=True)
        .select("stop_id", "stop_name", "mode", "stop_type", "avg_daily_usage", "avg_ons", "avg_offs", "lat", "lon")
    )
    unsheltered_priority.write_csv(OUT / "unsheltered_priority.csv")
    print(f"  Saved {OUT / 'unsheltered_priority.csv'}")

    print("\nGenerating charts...")
    make_charts(df, mode_df, owner_df)

    print("\nDone.")


if __name__ == "__main__":
    main()
