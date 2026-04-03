"""Compare PRT to 7 peer cities across ridership, service hours, and fare burden."""

import numpy as np
import polars as pl

from prt_otp_analysis.common import (
    PEERS,
    analysis_dir,
    get_db,
    phase,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)

OUT = analysis_dir(__file__)

PRT_NTD_ID = 30022

# Consistent color scheme — Pittsburgh highlighted
COLORS = {
    "Pittsburgh": "#E24A33",
    "Baltimore": "#4878CF",
    "Cleveland": "#6ACC65",
    "Denver": "#D65F5F",
    "St. Louis": "#B47CC7",
    "Buffalo": "#C4AD66",
    "Portland": "#77BEDB",
    "Minneapolis": "#FFB347",
}


def load_peer_data(conn) -> pl.DataFrame:
    """Load 2019 and 2023 annual metrics for all peer cities."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, year, upt, vrh, fares, opexp
        FROM ntd_annual_service
        WHERE ntd_id IN ({id_list})
          AND year IN (2019, 2023)
    """).fetchall()
    return pl.DataFrame(
        [dict(r) for r in rows],
        schema={"ntd_id": pl.Int64, "year": pl.Int64, "upt": pl.Float64,
                "vrh": pl.Float64, "fares": pl.Float64, "opexp": pl.Float64},
    )


def compute_metrics(raw_df: pl.DataFrame) -> pl.DataFrame:
    """Compute derived metrics and percent changes for each peer city."""
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    df = raw_df.join(peer_map, on="ntd_id", how="left")

    # Derived metrics
    df = df.with_columns(
        fare_per_trip=(pl.col("fares") / pl.col("upt")),
        farebox_recovery=(pl.col("fares") / pl.col("opexp") * 100),
        cost_per_trip=(pl.col("opexp") / pl.col("upt")),
    )

    # Pivot to wide: one row per city with 2019 and 2023 values
    y2019 = df.filter(pl.col("year") == 2019).drop("year")
    y2023 = df.filter(pl.col("year") == 2023).drop("year")

    metrics = y2019.join(y2023, on=["ntd_id", "city"], suffix="_2023")

    # Rename base columns to _2019
    value_cols = ["upt", "vrh", "fares", "opexp", "fare_per_trip", "farebox_recovery", "cost_per_trip"]
    rename_map = {c: f"{c}_2019" for c in value_cols}
    metrics = metrics.rename(rename_map)

    # Percent changes
    for col in ["upt", "vrh", "fares"]:
        metrics = metrics.with_columns(
            ((pl.col(f"{col}_2023") - pl.col(f"{col}_2019")) / pl.col(f"{col}_2019") * 100)
            .alias(f"{col}_pct_change")
        )

    return metrics.sort("city")


def _bar_colors(cities: list[str]) -> list[str]:
    """Return bar colors with Pittsburgh highlighted."""
    return [COLORS.get(c, "#9ca3af") for c in cities]


def chart_indexed_change(plt, metrics_df: pl.DataFrame) -> None:
    """Grouped bar chart: % change in ridership, service hours, and fare revenue."""
    fig, ax = plt.subplots(figsize=(12, 6))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    width = 0.25

    upt_pct = metrics_df["upt_pct_change"].to_list()
    vrh_pct = metrics_df["vrh_pct_change"].to_list()
    fares_pct = metrics_df["fares_pct_change"].to_list()

    ax.bar(x - width, upt_pct, width, label="Ridership", color="#4878CF")
    ax.bar(x, vrh_pct, width, label="Service Hours", color="#6ACC65")
    ax.bar(x + width, fares_pct, width, label="Fare Revenue", color="#D65F5F")

    # Highlight Pittsburgh labels
    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    ax.axhline(0, color="#999999", linestyle="-", linewidth=0.8)
    ax.set_ylabel("% Change (2019 → 2023)")
    ax.set_title("Ridership, Service, and Fare Revenue Change — Peer Cities (2019 → 2023)")
    ax.legend()
    save_chart(fig, OUT / "indexed_change.png")


def chart_fare_per_trip(plt, metrics_df: pl.DataFrame) -> None:
    """Paired bars showing fare per trip in 2019 vs 2023."""
    fig, ax = plt.subplots(figsize=(10, 6))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    width = 0.35

    vals_2019 = metrics_df["fare_per_trip_2019"].to_list()
    vals_2023 = metrics_df["fare_per_trip_2023"].to_list()

    ax.bar(x - width / 2, vals_2019, width, label="2019", color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vals_2023, width, label="2023", color="#E24A33", alpha=0.8)

    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    for i, (v19, v23) in enumerate(zip(vals_2019, vals_2023)):
        ax.text(i - width / 2, v19 + 0.02, f"${v19:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, v23 + 0.02, f"${v23:.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Fare Revenue per Trip ($)")
    ax.set_title("Fare Revenue per Trip — Peer Cities (2019 vs 2023)")
    ax.legend()
    save_chart(fig, OUT / "fare_per_trip.png")


def chart_farebox_recovery(plt, metrics_df: pl.DataFrame) -> None:
    """Paired bars showing farebox recovery ratio in 2019 vs 2023."""
    fig, ax = plt.subplots(figsize=(10, 6))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    width = 0.35

    vals_2019 = metrics_df["farebox_recovery_2019"].to_list()
    vals_2023 = metrics_df["farebox_recovery_2023"].to_list()

    ax.bar(x - width / 2, vals_2019, width, label="2019", color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vals_2023, width, label="2023", color="#E24A33", alpha=0.8)

    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    for i, (v19, v23) in enumerate(zip(vals_2019, vals_2023)):
        ax.text(i - width / 2, v19 + 0.3, f"{v19:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, v23 + 0.3, f"{v23:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Farebox Recovery Ratio (%)")
    ax.set_title("Farebox Recovery Ratio — Peer Cities (2019 vs 2023)")
    ax.legend()
    save_chart(fig, OUT / "farebox_recovery.png")


def chart_dashboard(plt, metrics_df: pl.DataFrame) -> None:
    """2×2 multi-panel dashboard combining key views."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    bar_cols = _bar_colors(cities)

    # Panel 1: Ridership change
    ax = axes[0, 0]
    vals = metrics_df["upt_pct_change"].to_list()
    ax.bar(x, vals, color=bar_cols, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.axhline(0, color="#999999", linestyle="-", linewidth=0.8)
    ax.set_ylabel("% Change")
    ax.set_title("Ridership Change (2019 → 2023)")
    for i, v in enumerate(vals):
        ax.text(i, v + (1 if v >= 0 else -2.5), f"{v:.0f}%", ha="center", fontsize=8)

    # Panel 2: Service hours change
    ax = axes[0, 1]
    vals = metrics_df["vrh_pct_change"].to_list()
    ax.bar(x, vals, color=bar_cols, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.axhline(0, color="#999999", linestyle="-", linewidth=0.8)
    ax.set_ylabel("% Change")
    ax.set_title("Service Hours Change (2019 → 2023)")
    for i, v in enumerate(vals):
        ax.text(i, v + (1 if v >= 0 else -2.5), f"{v:.0f}%", ha="center", fontsize=8)

    # Panel 3: Fare per trip (2019 vs 2023)
    ax = axes[1, 0]
    width = 0.35
    v19 = metrics_df["fare_per_trip_2019"].to_list()
    v23 = metrics_df["fare_per_trip_2023"].to_list()
    ax.bar(x - width / 2, v19, width, label="2019", color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, v23, width, label="2023", color="#E24A33", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("$/Trip")
    ax.set_title("Fare Revenue per Trip")
    ax.legend(fontsize=8)

    # Panel 4: Farebox recovery (2019 vs 2023)
    ax = axes[1, 1]
    v19 = metrics_df["farebox_recovery_2019"].to_list()
    v23 = metrics_df["farebox_recovery_2023"].to_list()
    ax.bar(x - width / 2, v19, width, label="2019", color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, v23, width, label="2023", color="#E24A33", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Recovery Ratio (%)")
    ax.set_title("Farebox Recovery Ratio")
    ax.legend(fontsize=8)

    fig.suptitle("Peer City Dashboard — Pittsburgh vs 7 Peers (2019 → 2023)",
                 fontsize=14, fontweight="bold", y=0.98)
    save_chart(fig, OUT / "peer_dashboard.png")


@run_analysis(40, "Peer City Dashboard")
def main():
    plt = setup_plotting()
    conn = get_db()

    with phase("Loading peer city data"):
        raw_df = load_peer_data(conn)
        conn.close()
        print(f"   {len(raw_df)} rows loaded ({len(raw_df) // 2} city-year pairs)")

    with phase("Computing metrics"):
        metrics_df = compute_metrics(raw_df)

        # Print summary table
        print("\n   %-15s %8s %8s %8s %8s %8s %8s" % (
            "City", "UPT%", "VRH%", "Fares%", "$/Trip19", "$/Trip23", "FBR%23"))
        for row in metrics_df.iter_rows(named=True):
            marker = " <<<" if row["ntd_id"] == PRT_NTD_ID else ""
            print("   %-15s %+7.1f%% %+7.1f%% %+7.1f%% %8.2f %8.2f %7.1f%%%s" % (
                row["city"],
                row["upt_pct_change"],
                row["vrh_pct_change"],
                row["fares_pct_change"],
                row["fare_per_trip_2019"],
                row["fare_per_trip_2023"],
                row["farebox_recovery_2023"],
                marker,
            ))

    # Save CSV
    with phase("Saving comparison data"):
        csv_cols = [
            "city", "upt_2019", "upt_2023", "upt_pct_change",
            "vrh_2019", "vrh_2023", "vrh_pct_change",
            "fares_2019", "fares_2023", "fares_pct_change",
            "fare_per_trip_2019", "fare_per_trip_2023",
            "farebox_recovery_2019", "farebox_recovery_2023",
            "cost_per_trip_2019", "cost_per_trip_2023",
        ]
        save_csv(metrics_df.select(csv_cols), OUT / "peer_comparison.csv")

    # Charts
    with phase("Generating indexed change chart"):
        chart_indexed_change(plt, metrics_df)

    with phase("Generating fare per trip chart"):
        chart_fare_per_trip(plt, metrics_df)

    with phase("Generating farebox recovery chart"):
        chart_farebox_recovery(plt, metrics_df)

    with phase("Generating dashboard"):
        chart_dashboard(plt, metrics_df)


if __name__ == "__main__":
    main()
