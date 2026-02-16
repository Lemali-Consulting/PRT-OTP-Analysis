"""Map the spatial pattern of stop-level ridership loss and recovery during the pandemic."""

import math
from pathlib import Path

import numpy as np
import polars as pl

from prt_otp_analysis.common import output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"

# Downtown Pittsburgh centroid
DT_LAT, DT_LON = 40.4406, -79.9959


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def classify_zone(lat: float, lon: float) -> str:
    """Classify a stop into downtown core, inner ring, or outer ring."""
    d = haversine_km(lat, lon, DT_LAT, DT_LON)
    if d < 2:
        return "Downtown (< 2 km)"
    elif d < 8:
        return "Inner ring (2-8 km)"
    else:
        return "Outer ring (> 8 km)"


def load_data() -> pl.DataFrame:
    """Load and compute pre/post pandemic usage per physical stop."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])

    # Weekday only
    df = df.filter(pl.col("serviceday") == "Weekday")

    # Tag period
    df = df.with_columns(
        pl.when(pl.col("time_period") == "Pre-pandemic")
        .then(pl.lit("pre"))
        .otherwise(pl.lit("post"))
        .alias("period")
    )

    # Aggregate: per stop, per period -- sum across routes, mean across datekeys
    per_stop_dk = (
        df.group_by(["stop_id", "period", "datekey"])
        .agg(
            pl.col("avg_ons").sum(),
            pl.col("avg_offs").sum(),
            pl.col("stop_name").first(),
            pl.col("latitude").first().alias("lat"),
            pl.col("longitude").first().alias("lon"),
            pl.col("mode").first(),
        )
    )

    per_stop_period = (
        per_stop_dk.group_by(["stop_id", "period"])
        .agg(
            pl.col("avg_ons").mean(),
            pl.col("avg_offs").mean(),
            pl.col("stop_name").first(),
            pl.col("lat").first(),
            pl.col("lon").first(),
            pl.col("mode").first(),
        )
        .with_columns(
            (pl.col("avg_ons") + pl.col("avg_offs")).alias("avg_daily_usage")
        )
    )

    # Pivot to wide: one row per stop with pre and post columns
    pre = (
        per_stop_period.filter(pl.col("period") == "pre")
        .select("stop_id", "stop_name", "lat", "lon", "mode",
                pl.col("avg_daily_usage").alias("pre_usage"))
    )
    post = (
        per_stop_period.filter(pl.col("period") == "post")
        .select("stop_id", pl.col("avg_daily_usage").alias("post_usage"))
    )

    merged = pre.join(post, on="stop_id", how="inner")

    # Compute changes
    merged = merged.with_columns(
        (pl.col("post_usage") - pl.col("pre_usage")).alias("abs_change"),
        pl.when(pl.col("pre_usage") > 0)
        .then((pl.col("post_usage") - pl.col("pre_usage")) / pl.col("pre_usage") * 100)
        .otherwise(None)
        .alias("pct_change"),
    )

    # Classify zones
    zones = [
        classify_zone(lat, lon)
        for lat, lon in zip(merged["lat"].to_list(), merged["lon"].to_list())
    ]
    merged = merged.with_columns(pl.Series("zone", zones))

    # Distance from downtown
    dists = [
        haversine_km(lat, lon, DT_LAT, DT_LON)
        for lat, lon in zip(merged["lat"].to_list(), merged["lon"].to_list())
    ]
    merged = merged.with_columns(pl.Series("dist_from_dt_km", dists))

    return merged


def make_charts(df: pl.DataFrame) -> None:
    """Generate geographic map and zone summary charts."""
    plt = setup_plotting()

    # Filter to stops with pre-pandemic usage > 0 for pct_change
    valid = df.filter(pl.col("pre_usage") > 0)

    # --- Geographic scatter map ---
    fig, ax = plt.subplots(figsize=(10, 10))

    pct = np.array(valid["pct_change"].to_list())
    # Clip for color scale
    pct_clipped = np.clip(pct, -100, 50)

    sc = ax.scatter(
        valid["lon"].to_list(), valid["lat"].to_list(),
        c=pct_clipped, cmap="RdYlGn", s=8, alpha=0.6,
        vmin=-100, vmax=50, edgecolors="none",
    )
    cbar = plt.colorbar(sc, ax=ax, label="% Change in Weekday Usage", shrink=0.6)
    cbar.set_ticks([-100, -75, -50, -25, 0, 25, 50])

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Pandemic Ridership Change by Stop (Pre-pandemic -> Pandemic)")
    fig.tight_layout()
    fig.savefig(OUT / "ridership_change_map.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'ridership_change_map.png'}")

    # --- Zone summary + histogram ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Bar chart by zone
    zone_order = ["Downtown (< 2 km)", "Inner ring (2-8 km)", "Outer ring (> 8 km)"]
    zone_stats = []
    for z in zone_order:
        sub = valid.filter(pl.col("zone") == z)
        zone_stats.append({
            "zone": z,
            "median_pct": sub["pct_change"].median(),
            "mean_pct": sub["pct_change"].mean(),
            "n": len(sub),
        })

    colors = ["#ef4444", "#f59e0b", "#22c55e"]
    medians = [s["median_pct"] for s in zone_stats]
    labels = [f"{s['zone']}\n(n={s['n']:,})" for s in zone_stats]
    bars = axes[0].bar(labels, medians, color=colors, edgecolor="white")
    for bar, val in zip(bars, medians):
        axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 2,
                     f"{val:.0f}%", ha="center", va="top", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Median % Change in Weekday Usage")
    axes[0].set_title("Ridership Change by Distance from Downtown")
    axes[0].axhline(0, color="black", linewidth=0.5)

    # Histogram of % changes
    axes[1].hist(pct, bins=50, range=(-100, 100), color="#3b82f6", edgecolor="white", alpha=0.8)
    axes[1].axvline(np.median(pct), color="#ef4444", linewidth=2, linestyle="--",
                    label=f"Median: {np.median(pct):.0f}%")
    axes[1].set_xlabel("% Change in Weekday Usage")
    axes[1].set_ylabel("Number of Stops")
    axes[1].set_title("Distribution of Stop-Level Ridership Changes")
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(OUT / "change_by_zone.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'change_by_zone.png'}")


def main() -> None:
    """Entry point: load data, analyze pandemic ridership geography."""
    print("=" * 60)
    print("Analysis 33: Pandemic Ridership Geography")
    print("=" * 60)

    print("\nLoading and computing stop-level pandemic changes...")
    df = load_data()
    valid = df.filter(pl.col("pre_usage") > 0)
    print(f"  {len(df):,} stops with both pre and post data")
    print(f"  {len(valid):,} stops with pre-pandemic usage > 0")

    print("\nSystem-wide summary:")
    med_pct = valid["pct_change"].median()
    mean_pct = valid["pct_change"].mean()
    total_pre = df["pre_usage"].sum()
    total_post = df["post_usage"].sum()
    sys_pct = (total_post - total_pre) / total_pre * 100
    print(f"  Median stop-level change: {med_pct:.1f}%")
    print(f"  Mean stop-level change: {mean_pct:.1f}%")
    print(f"  System total: {total_pre:,.0f} -> {total_post:,.0f} ({sys_pct:+.1f}%)")

    print("\nBy zone:")
    for z in ["Downtown (< 2 km)", "Inner ring (2-8 km)", "Outer ring (> 8 km)"]:
        sub = valid.filter(pl.col("zone") == z)
        pre_sum = sub["pre_usage"].sum()
        post_sum = sub["post_usage"].sum()
        z_pct = (post_sum - pre_sum) / pre_sum * 100 if pre_sum > 0 else 0
        print(f"  {z}: median {sub['pct_change'].median():+.0f}%, "
              f"aggregate {z_pct:+.1f}%, n={len(sub):,}")

    print("\nBy mode:")
    for mode in valid["mode"].unique().drop_nulls().sort().to_list():
        sub = valid.filter(pl.col("mode") == mode)
        print(f"  {mode:12s}: median {sub['pct_change'].median():+.0f}%, n={len(sub):,}")

    print("\nTop 10 stops with largest absolute loss:")
    biggest_loss = valid.sort("abs_change").head(10)
    for row in biggest_loss.iter_rows(named=True):
        print(f"  {row['stop_name'][:40]:40s} {row['pre_usage']:8.0f} -> {row['post_usage']:8.0f} ({row['pct_change']:+.0f}%)")

    print("\nSaving CSV...")
    df.write_csv(OUT / "pandemic_change_by_stop.csv")
    print(f"  Saved {OUT / 'pandemic_change_by_stop.csv'}")

    print("\nGenerating charts...")
    make_charts(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
