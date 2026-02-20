"""Analyze net boarding-alighting flows by stop to identify trip generators and attractors."""

from pathlib import Path

import numpy as np
import polars as pl

from prt_otp_analysis.common import output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"


def load_stop_flows() -> pl.DataFrame:
    """Load pre-pandemic weekday boardings/alightings aggregated to physical-stop level."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])

    df = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )

    # Average across datekeys per stop-route, then sum across routes per physical stop
    per_stop_route = (
        df.group_by(["stop_id", "route_name"])
        .agg(
            pl.col("avg_ons").mean().alias("avg_ons"),
            pl.col("avg_offs").mean().alias("avg_offs"),
            pl.col("stop_name").first(),
            pl.col("latitude").first().alias("lat"),
            pl.col("longitude").first().alias("lon"),
            pl.col("direction").first(),
            pl.col("mode").first(),
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
            pl.col("direction").first(),
            pl.col("mode").first(),
        )
        .with_columns(
            (pl.col("avg_ons") - pl.col("avg_offs")).alias("net_flow"),
            (pl.col("avg_ons") + pl.col("avg_offs")).alias("total_usage"),
        )
        .with_columns(
            pl.when(pl.col("net_flow") > 0)
            .then(pl.lit("Generator"))
            .when(pl.col("net_flow") < 0)
            .then(pl.lit("Attractor"))
            .otherwise(pl.lit("Balanced"))
            .alias("flow_type"),
            pl.when(pl.col("avg_offs") > 0)
            .then(pl.col("avg_ons") / pl.col("avg_offs"))
            .otherwise(None)
            .alias("on_off_ratio"),
        )
    )
    return per_stop


def load_directional_flows() -> pl.DataFrame:
    """Load direction-level boarding/alighting summary."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])

    df = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
        & pl.col("direction").is_not_null()
    )

    return (
        df.group_by("direction")
        .agg(
            pl.col("avg_ons").sum().alias("total_ons"),
            pl.col("avg_offs").sum().alias("total_offs"),
            pl.len().alias("n_records"),
        )
        .with_columns(
            (pl.col("total_ons") - pl.col("total_offs")).alias("net_flow"),
            pl.when(pl.col("total_offs") > 0)
            .then(pl.col("total_ons") / pl.col("total_offs"))
            .otherwise(None)
            .alias("on_off_ratio"),
        )
    )


def make_charts(df: pl.DataFrame) -> None:
    """Generate net flow map and top generators/attractors bar chart."""
    plt = setup_plotting()

    # Filter to stops with meaningful usage
    active = df.filter(pl.col("total_usage") > 1)

    # --- Net flow geographic map ---
    fig, ax = plt.subplots(figsize=(10, 10))

    net = np.array(active["net_flow"].to_list())
    # Clamp for color scale
    net_clipped = np.clip(net, -200, 200)
    sizes = np.clip(np.abs(net) * 0.05, 3, 30)

    sc = ax.scatter(
        active["lon"].to_list(), active["lat"].to_list(),
        c=net_clipped, cmap="RdBu", s=sizes, alpha=0.6,
        vmin=-200, vmax=200, edgecolors="none",
    )
    cbar = plt.colorbar(sc, ax=ax, label="Net Flow (ons - offs)", shrink=0.6)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Stop Net Flow: Generators (blue) vs Attractors (red)")
    fig.tight_layout()
    fig.savefig(OUT / "net_flow_map.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'net_flow_map.png'}")

    # --- Top generators and attractors ---
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))

    # Top generators (highest net flow)
    top_gen = df.sort("net_flow", descending=True).head(15)
    names = [n[:35] for n in top_gen["stop_name"].to_list()]
    vals = top_gen["net_flow"].to_list()
    axes[0].barh(range(len(names)), vals, color="#3b82f6", edgecolor="white")
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels(names, fontsize=8)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Net Flow (avg daily ons - offs)")
    axes[0].set_title("Top 15 Trip Generators\n(more boardings than alightings)")
    for i, v in enumerate(vals):
        axes[0].text(v + 5, i, f"+{v:.0f}", va="center", fontsize=8)

    # Top attractors (lowest net flow)
    top_attr = df.sort("net_flow").head(15)
    names = [n[:35] for n in top_attr["stop_name"].to_list()]
    vals = top_attr["net_flow"].to_list()
    axes[1].barh(range(len(names)), [abs(v) for v in vals], color="#ef4444", edgecolor="white")
    axes[1].set_yticks(range(len(names)))
    axes[1].set_yticklabels(names, fontsize=8)
    axes[1].invert_yaxis()
    axes[1].set_xlabel("Net Flow magnitude (avg daily offs - ons)")
    axes[1].set_title("Top 15 Trip Attractors\n(more alightings than boardings)")
    for i, v in enumerate(vals):
        axes[1].text(abs(v) + 5, i, f"{v:.0f}", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT / "top_generators_attractors.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'top_generators_attractors.png'}")


def main() -> None:
    """Entry point: load data, analyze boarding/alighting flows, chart."""
    print("=" * 60)
    print("Analysis 35: Boarding/Alighting Flow Analysis")
    print("=" * 60)

    print("\nLoading stop-level flows (pre-pandemic weekday)...")
    df = load_stop_flows()
    print(f"  {len(df):,} unique physical stops")

    n_gen = len(df.filter(pl.col("flow_type") == "Generator"))
    n_attr = len(df.filter(pl.col("flow_type") == "Attractor"))
    n_bal = len(df.filter(pl.col("flow_type") == "Balanced"))
    print(f"\nFlow classification:")
    print(f"  Generators: {n_gen:,} ({n_gen / len(df) * 100:.0f}%)")
    print(f"  Attractors: {n_attr:,} ({n_attr / len(df) * 100:.0f}%)")
    print(f"  Balanced:   {n_bal:,} ({n_bal / len(df) * 100:.0f}%)")

    total_ons = df["avg_ons"].sum()
    total_offs = df["avg_offs"].sum()
    print(f"\nSystem totals:")
    print(f"  Total boardings: {total_ons:,.0f}/day")
    print(f"  Total alightings: {total_offs:,.0f}/day")
    print(f"  System on/off ratio: {total_ons / total_offs:.3f}")

    print("\nTop 10 generators (net boardings):")
    for row in df.sort("net_flow", descending=True).head(10).iter_rows(named=True):
        print(f"  {row['stop_name'][:40]:40s}  net +{row['net_flow']:,.0f}/day  (ons={row['avg_ons']:,.0f}, offs={row['avg_offs']:,.0f})")

    print("\nTop 10 attractors (net alightings):")
    for row in df.sort("net_flow").head(10).iter_rows(named=True):
        print(f"  {row['stop_name'][:40]:40s}  net {row['net_flow']:,.0f}/day  (ons={row['avg_ons']:,.0f}, offs={row['avg_offs']:,.0f})")

    print("\nDirectional analysis:")
    dir_flows = load_directional_flows()
    for row in dir_flows.sort("direction").iter_rows(named=True):
        print(f"  {row['direction']:10s}: ons={row['total_ons']:,.0f}, offs={row['total_offs']:,.0f}, "
              f"ratio={row['on_off_ratio']:.2f}, net={row['net_flow']:+,.0f}")

    print("\nOn/off ratio distribution:")
    valid_ratio = df.filter(pl.col("on_off_ratio").is_not_null() & pl.col("on_off_ratio").is_finite())
    print(f"  Median on/off ratio: {valid_ratio['on_off_ratio'].median():.2f}")
    print(f"  Mean on/off ratio: {valid_ratio['on_off_ratio'].mean():.2f}")
    pct_gen = len(valid_ratio.filter(pl.col("on_off_ratio") > 1.5)) / len(valid_ratio) * 100
    pct_attr = len(valid_ratio.filter(pl.col("on_off_ratio") < 0.67)) / len(valid_ratio) * 100
    print(f"  Strong generators (ratio > 1.5): {pct_gen:.1f}% of stops")
    print(f"  Strong attractors (ratio < 0.67): {pct_attr:.1f}% of stops")

    print("\nSaving CSV...")
    df.write_csv(OUT / "stop_net_flow.csv")
    print(f"  Saved {OUT / 'stop_net_flow.csv'}")

    print("\nGenerating charts...")
    make_charts(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
