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
BASELINE_YEAR = 2019
COMPARE_YEAR = 2024

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

# Column name helpers
BY = str(BASELINE_YEAR)
CY = str(COMPARE_YEAR)


def load_peer_data(conn) -> pl.DataFrame:
    """Load baseline and comparison year annual metrics for all peer cities."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, year, upt, vrh, fares, opexp
        FROM ntd_annual_service
        WHERE ntd_id IN ({id_list})
          AND year IN ({BASELINE_YEAR}, {COMPARE_YEAR})
    """).fetchall()
    return pl.DataFrame(
        [dict(r) for r in rows],
        schema={"ntd_id": pl.Int64, "year": pl.Int64, "upt": pl.Float64,
                "vrh": pl.Float64, "fares": pl.Float64, "opexp": pl.Float64},
    )


def load_peer_timeseries(conn) -> pl.DataFrame:
    """Load annual metrics for all peer cities across the full year range."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, year, upt, vrh, fares, opexp
        FROM ntd_annual_service
        WHERE ntd_id IN ({id_list})
          AND year BETWEEN {BASELINE_YEAR} AND {COMPARE_YEAR}
    """).fetchall()
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    df = pl.DataFrame(
        [dict(r) for r in rows],
        schema={"ntd_id": pl.Int64, "year": pl.Int64, "upt": pl.Float64,
                "vrh": pl.Float64, "fares": pl.Float64, "opexp": pl.Float64},
    )
    df = df.join(peer_map, on="ntd_id", how="left")
    # Compute derived metrics
    df = df.with_columns(
        fare_per_trip=(pl.col("fares") / pl.col("upt")),
        farebox_recovery=(pl.col("fares") / pl.col("opexp") * 100),
    )
    return df.sort("city", "year")


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

    # Pivot to wide: one row per city with baseline and comparison year values
    y_base = df.filter(pl.col("year") == BASELINE_YEAR).drop("year")
    y_comp = df.filter(pl.col("year") == COMPARE_YEAR).drop("year")

    suffix = f"_{CY}"
    metrics = y_base.join(y_comp, on=["ntd_id", "city"], suffix=suffix)

    # Rename base columns to _<BASELINE_YEAR>
    value_cols = ["upt", "vrh", "fares", "opexp", "fare_per_trip", "farebox_recovery", "cost_per_trip"]
    rename_map = {c: f"{c}_{BY}" for c in value_cols}
    metrics = metrics.rename(rename_map)

    # Percent changes
    for col in ["upt", "vrh", "fares"]:
        metrics = metrics.with_columns(
            ((pl.col(f"{col}_{CY}") - pl.col(f"{col}_{BY}"))
             / pl.col(f"{col}_{BY}") * 100)
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
    ax.set_ylabel(f"% Change ({BY} \u2192 {CY})")
    ax.set_title(f"Ridership, Service, and Fare Revenue Change \u2014 Peer Cities ({BY} \u2192 {CY})")
    ax.legend()
    save_chart(fig, OUT / "indexed_change.png")


def chart_fare_per_trip(plt, metrics_df: pl.DataFrame) -> None:
    """Paired bars showing fare per trip in baseline vs comparison year."""
    fig, ax = plt.subplots(figsize=(10, 6))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    width = 0.35

    vals_base = metrics_df[f"fare_per_trip_{BY}"].to_list()
    vals_comp = metrics_df[f"fare_per_trip_{CY}"].to_list()

    ax.bar(x - width / 2, vals_base, width, label=BY, color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vals_comp, width, label=CY, color="#E24A33", alpha=0.8)

    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    for i, (vb, vc) in enumerate(zip(vals_base, vals_comp)):
        ax.text(i - width / 2, vb + 0.02, f"${vb:.2f}", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, vc + 0.02, f"${vc:.2f}", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Fare Revenue per Trip ($)")
    ax.set_title(f"Fare Revenue per Trip \u2014 Peer Cities ({BY} vs {CY})")
    ax.legend()
    save_chart(fig, OUT / "fare_per_trip.png")


def chart_farebox_recovery(plt, metrics_df: pl.DataFrame) -> None:
    """Paired bars showing farebox recovery ratio in baseline vs comparison year."""
    fig, ax = plt.subplots(figsize=(10, 6))

    cities = metrics_df["city"].to_list()
    x = np.arange(len(cities))
    width = 0.35

    vals_base = metrics_df[f"farebox_recovery_{BY}"].to_list()
    vals_comp = metrics_df[f"farebox_recovery_{CY}"].to_list()

    ax.bar(x - width / 2, vals_base, width, label=BY, color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vals_comp, width, label=CY, color="#E24A33", alpha=0.8)

    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    for i, (vb, vc) in enumerate(zip(vals_base, vals_comp)):
        ax.text(i - width / 2, vb + 0.3, f"{vb:.1f}%", ha="center", va="bottom", fontsize=8)
        ax.text(i + width / 2, vc + 0.3, f"{vc:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.set_ylabel("Farebox Recovery Ratio (%)")
    ax.set_title(f"Farebox Recovery Ratio \u2014 Peer Cities ({BY} vs {CY})")
    ax.legend()
    save_chart(fig, OUT / "farebox_recovery.png")


def chart_dashboard(plt, metrics_df: pl.DataFrame) -> None:
    """2x2 multi-panel dashboard combining key views."""
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
    ax.set_title(f"Ridership Change ({BY} \u2192 {CY})")
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
    ax.set_title(f"Service Hours Change ({BY} \u2192 {CY})")
    for i, v in enumerate(vals):
        ax.text(i, v + (1 if v >= 0 else -2.5), f"{v:.0f}%", ha="center", fontsize=8)

    # Panel 3: Fare per trip
    ax = axes[1, 0]
    width = 0.35
    vb = metrics_df[f"fare_per_trip_{BY}"].to_list()
    vc = metrics_df[f"fare_per_trip_{CY}"].to_list()
    ax.bar(x - width / 2, vb, width, label=BY, color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vc, width, label=CY, color="#E24A33", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("$/Trip")
    ax.set_title("Fare Revenue per Trip")
    ax.legend(fontsize=8)

    # Panel 4: Farebox recovery
    ax = axes[1, 1]
    vb = metrics_df[f"farebox_recovery_{BY}"].to_list()
    vc = metrics_df[f"farebox_recovery_{CY}"].to_list()
    ax.bar(x - width / 2, vb, width, label=BY, color="#4878CF", alpha=0.8)
    ax.bar(x + width / 2, vc, width, label=CY, color="#E24A33", alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Recovery Ratio (%)")
    ax.set_title("Farebox Recovery Ratio")
    ax.legend(fontsize=8)

    fig.suptitle(f"Peer City Dashboard \u2014 Pittsburgh vs 7 Peers ({BY} \u2192 {CY})",
                 fontsize=14, fontweight="bold", y=0.98)
    save_chart(fig, OUT / "peer_dashboard.png")


def _plot_trend_line(ax, ts_df: pl.DataFrame, metric: str, ylabel: str,
                     title: str, fmt: str = ".1f", indexed: bool = False) -> None:
    """Plot one trend line per city on the given axes."""
    for city in sorted(PEERS.values()):
        city_df = ts_df.filter(pl.col("city") == city).sort("year")
        years = city_df["year"].to_list()
        vals = city_df[metric].to_list()
        if indexed:
            base = vals[0] if vals[0] else 1
            vals = [v / base * 100 for v in vals]
        lw = 2.5 if city == "Pittsburgh" else 1.2
        alpha = 1.0 if city == "Pittsburgh" else 0.6
        zorder = 10 if city == "Pittsburgh" else 1
        ax.plot(years, vals, label=city, color=COLORS[city],
                linewidth=lw, alpha=alpha, zorder=zorder, marker="o", markersize=3)
    if indexed:
        ax.axhline(100, color="#999999", linestyle=":", linewidth=0.8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(list(range(BASELINE_YEAR, COMPARE_YEAR + 1)))


def chart_trends(plt, ts_df: pl.DataFrame) -> None:
    """2x2 line chart panel showing annual trajectories for each metric."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    _plot_trend_line(axes[0, 0], ts_df, "upt", "Indexed (2019 = 100)",
                     "Ridership Trajectory", indexed=True)
    _plot_trend_line(axes[0, 1], ts_df, "vrh", "Indexed (2019 = 100)",
                     "Service Hours Trajectory", indexed=True)
    _plot_trend_line(axes[1, 0], ts_df, "fare_per_trip", "$/Trip",
                     "Fare Revenue per Trip")
    _plot_trend_line(axes[1, 1], ts_df, "farebox_recovery", "Recovery Ratio (%)",
                     "Farebox Recovery Ratio")

    axes[0, 0].legend(loc="lower right", fontsize=8)
    fig.suptitle(f"Peer City Trends \u2014 Pittsburgh vs 7 Peers ({BY}\u2013{CY})",
                 fontsize=14, fontweight="bold", y=0.98)
    save_chart(fig, OUT / "peer_trends.png")


@run_analysis(40, "Peer City Dashboard")
def main():
    plt = setup_plotting()
    conn = get_db()

    with phase("Loading peer city data"):
        raw_df = load_peer_data(conn)
        ts_df = load_peer_timeseries(conn)
        conn.close()
        print(f"   {len(raw_df)} rows for endpoint comparison")
        print(f"   {len(ts_df)} rows for time series ({BASELINE_YEAR}-{COMPARE_YEAR})")

    with phase("Computing metrics"):
        metrics_df = compute_metrics(raw_df)

        # Print summary table
        print(f"\n   {'City':<15s} {'UPT%':>8s} {'VRH%':>8s} {'Fares%':>8s} "
              f"{'$/Trip'+BY:>8s} {'$/Trip'+CY:>8s} {'FBR%'+CY:>8s}")
        for row in metrics_df.iter_rows(named=True):
            marker = " <<<" if row["ntd_id"] == PRT_NTD_ID else ""
            print("   %-15s %+7.1f%% %+7.1f%% %+7.1f%% %8.2f %8.2f %7.1f%%%s" % (
                row["city"],
                row["upt_pct_change"],
                row["vrh_pct_change"],
                row["fares_pct_change"],
                row[f"fare_per_trip_{BY}"],
                row[f"fare_per_trip_{CY}"],
                row[f"farebox_recovery_{CY}"],
                marker,
            ))

    # Save CSV
    with phase("Saving comparison data"):
        csv_cols = [
            "city",
            f"upt_{BY}", f"upt_{CY}", "upt_pct_change",
            f"vrh_{BY}", f"vrh_{CY}", "vrh_pct_change",
            f"fares_{BY}", f"fares_{CY}", "fares_pct_change",
            f"fare_per_trip_{BY}", f"fare_per_trip_{CY}",
            f"farebox_recovery_{BY}", f"farebox_recovery_{CY}",
            f"cost_per_trip_{BY}", f"cost_per_trip_{CY}",
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

    with phase("Generating trend lines"):
        chart_trends(plt, ts_df)


if __name__ == "__main__":
    main()
