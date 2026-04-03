"""Decompose PRT's operating cost premium and correlate with fleet age."""

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

# Cost category display names and colors
COST_CATS = {
    "opexp_vo": ("Vehicle Ops", "#4878CF"),
    "opexp_vm": ("Vehicle Maint", "#E24A33"),
    "opexp_nvm": ("Non-Veh Maint", "#6ACC65"),
    "opexp_ga": ("Gen Admin", "#B47CC7"),
}


def load_cost_data(conn) -> pl.DataFrame:
    """Load OpExp sub-categories and UPT for peers across all years."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, year, upt, opexp, opexp_vo, opexp_vm, opexp_nvm, opexp_ga
        FROM ntd_annual_service
        WHERE ntd_id IN ({id_list})
          AND year BETWEEN {BASELINE_YEAR} AND {COMPARE_YEAR}
    """).fetchall()
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    df = pl.DataFrame([dict(r) for r in rows])
    df = df.join(peer_map, on="ntd_id", how="left")

    # Compute per-trip costs
    for cat in COST_CATS:
        df = df.with_columns((pl.col(cat) / pl.col("upt")).alias(f"{cat}_pt"))
    df = df.with_columns((pl.col("opexp") / pl.col("upt")).alias("cost_per_trip"))
    return df.sort("city", "year")


def load_fleet_age(conn) -> pl.DataFrame:
    """Load 2024 fleet age data for peer cities."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, vehicle_type, total_vehicles, avg_age, avg_miles
        FROM ntd_fleet_age
        WHERE ntd_id IN ({id_list})
          AND year = {COMPARE_YEAR}
    """).fetchall()
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    df = pl.DataFrame([dict(r) for r in rows])
    return df.join(peer_map, on="ntd_id", how="left")


def chart_cost_breakdown(plt, cost_df: pl.DataFrame) -> None:
    """Stacked bar: per-trip cost breakdown by category (2024)."""
    df_2024 = cost_df.filter(pl.col("year") == COMPARE_YEAR).sort("cost_per_trip", descending=True)
    cities = df_2024["city"].to_list()
    x = np.arange(len(cities))

    fig, ax = plt.subplots(figsize=(12, 7))
    bottom = np.zeros(len(cities))

    for cat, (label, color) in COST_CATS.items():
        vals = df_2024[f"{cat}_pt"].to_list()
        ax.bar(x, vals, bottom=bottom, label=label, color=color, edgecolor="white", linewidth=0.5)
        bottom += np.array(vals)

    # Label totals on top
    for i, total in enumerate(df_2024["cost_per_trip"].to_list()):
        ax.text(i, total + 0.15, f"${total:.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    labels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for label in labels:
        if label.get_text() == "Pittsburgh":
            label.set_fontweight("bold")

    ax.set_ylabel("Cost per Trip ($)")
    ax.set_title(f"Operating Cost per Trip by Category \u2014 Peer Cities ({COMPARE_YEAR})")
    ax.legend(loc="upper right")
    save_chart(fig, OUT / "cost_breakdown.png")


def chart_cost_change(plt, cost_df: pl.DataFrame) -> None:
    """Grouped bar: per-trip cost by category, 2019 vs 2024, all peers."""
    df_base = cost_df.filter(pl.col("year") == BASELINE_YEAR).sort("city")
    df_comp = cost_df.filter(pl.col("year") == COMPARE_YEAR).sort("city")
    cities = df_comp["city"].to_list()
    x = np.arange(len(cities))

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    for idx, (cat, (label, color)) in enumerate(COST_CATS.items()):
        ax = axes[idx // 2, idx % 2]
        vals_base = df_base[f"{cat}_pt"].to_list()
        vals_comp = df_comp[f"{cat}_pt"].to_list()
        width = 0.35

        ax.bar(x - width / 2, vals_base, width, label=str(BASELINE_YEAR), color="#4878CF", alpha=0.8)
        ax.bar(x + width / 2, vals_comp, width, label=str(COMPARE_YEAR), color="#E24A33", alpha=0.8)
        ax.set_xticks(x)
        xlabels = ax.set_xticklabels(cities, rotation=35, ha="right", fontsize=8)
        for xl in xlabels:
            if xl.get_text() == "Pittsburgh":
                xl.set_fontweight("bold")
        ax.set_ylabel("$/Trip")
        ax.set_title(label)
        ax.legend(fontsize=8)

    fig.suptitle(f"Cost per Trip by Category \u2014 {BASELINE_YEAR} vs {COMPARE_YEAR}",
                 fontsize=14, fontweight="bold", y=0.98)
    save_chart(fig, OUT / "cost_change.png")


def chart_fleet_age_vs_maintenance(plt, cost_df: pl.DataFrame, fleet_df: pl.DataFrame) -> None:
    """Scatter: bus fleet age vs vehicle maintenance cost/trip."""
    bus_age_df = fleet_df.filter(pl.col("vehicle_type") == "Bus").select("ntd_id", "city", "avg_age")
    maint_df = cost_df.filter(pl.col("year") == COMPARE_YEAR).select("ntd_id", "city", "opexp_vm_pt")
    merged_df = maint_df.join(bus_age_df, on=["ntd_id", "city"], how="inner")

    fig, ax = plt.subplots(figsize=(10, 7))
    for row in merged_df.iter_rows(named=True):
        city = row["city"]
        color = COLORS[city]
        size = 120 if city == "Pittsburgh" else 80
        zorder = 10 if city == "Pittsburgh" else 1
        ax.scatter(row["avg_age"], row["opexp_vm_pt"], color=color, s=size,
                   zorder=zorder, edgecolors="white", linewidth=1)
        offset_y = 0.08 if city != "Baltimore" else -0.12
        ax.annotate(city, (row["avg_age"], row["opexp_vm_pt"]),
                    textcoords="offset points", xytext=(8, offset_y * 50),
                    fontsize=9, fontweight="bold" if city == "Pittsburgh" else "normal")

    # Trendline
    ages = merged_df["avg_age"].to_list()
    costs = merged_df["opexp_vm_pt"].to_list()
    z = np.polyfit(ages, costs, 1)
    p = np.poly1d(z)
    age_range = np.linspace(min(ages) - 0.5, max(ages) + 0.5, 50)
    ax.plot(age_range, p(age_range), "--", color="#999999", linewidth=1, alpha=0.7)

    # Correlation
    corr = np.corrcoef(ages, costs)[0, 1]
    ax.text(0.05, 0.95, f"r = {corr:.2f}", transform=ax.transAxes,
            fontsize=11, verticalalignment="top", color="#666666")

    ax.set_xlabel("Average Bus Fleet Age (years)")
    ax.set_ylabel("Vehicle Maintenance Cost per Trip ($)")
    ax.set_title(f"Bus Fleet Age vs Vehicle Maintenance Cost \u2014 Peer Cities ({COMPARE_YEAR})")
    save_chart(fig, OUT / "fleet_age_vs_maintenance.png")


def chart_fleet_age_comparison(plt, fleet_df: pl.DataFrame) -> None:
    """Bar chart: average bus and light rail age per peer."""
    bus_df = (fleet_df.filter(pl.col("vehicle_type") == "Bus")
              .select("city", "avg_age").rename({"avg_age": "bus_age"}).sort("city"))
    lrv_df = (fleet_df.filter(pl.col("vehicle_type") == "Light Rail Vehicle")
              .select("city", "avg_age").rename({"avg_age": "lrv_age"}).sort("city"))

    # Only cities with bus data (all should have it)
    cities = bus_df["city"].to_list()
    bus_ages = bus_df["bus_age"].to_list()

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(cities))
    width = 0.35

    ax.bar(x - width / 2, bus_ages, width, label="Bus", color="#4878CF")

    # Add LRV bars where available
    lrv_ages = []
    for city in cities:
        lrv_row = lrv_df.filter(pl.col("city") == city)
        lrv_ages.append(lrv_row["lrv_age"][0] if len(lrv_row) > 0 else 0)
    ax.bar(x + width / 2, lrv_ages, width, label="Light Rail", color="#E24A33")

    for i, (ba, la) in enumerate(zip(bus_ages, lrv_ages)):
        ax.text(i - width / 2, ba + 0.3, f"{ba:.1f}", ha="center", va="bottom", fontsize=8)
        if la > 0:
            ax.text(i + width / 2, la + 0.3, f"{la:.1f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    xlabels = ax.set_xticklabels(cities, rotation=35, ha="right")
    for xl in xlabels:
        if xl.get_text() == "Pittsburgh":
            xl.set_fontweight("bold")

    ax.set_ylabel("Average Fleet Age (years)")
    ax.set_title(f"Revenue Vehicle Fleet Age \u2014 Peer Cities ({COMPARE_YEAR})")
    ax.legend()
    save_chart(fig, OUT / "fleet_age_comparison.png")


def chart_cost_trends(plt, cost_df: pl.DataFrame) -> None:
    """2×2 line chart: per-trip cost trajectories by category."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    for idx, (cat, (label, _)) in enumerate(COST_CATS.items()):
        ax = axes[idx // 2, idx % 2]
        for city in sorted(PEERS.values()):
            city_df = cost_df.filter(pl.col("city") == city).sort("year")
            years = city_df["year"].to_list()
            vals = city_df[f"{cat}_pt"].to_list()
            lw = 2.5 if city == "Pittsburgh" else 1.2
            alpha = 1.0 if city == "Pittsburgh" else 0.6
            zorder = 10 if city == "Pittsburgh" else 1
            ax.plot(years, vals, label=city, color=COLORS[city],
                    linewidth=lw, alpha=alpha, zorder=zorder, marker="o", markersize=3)
        ax.set_ylabel("$/Trip")
        ax.set_title(label)
        ax.set_xticks(list(range(BASELINE_YEAR, COMPARE_YEAR + 1)))

    axes[0, 0].legend(loc="upper left", fontsize=7)
    fig.suptitle(f"Cost per Trip Trends \u2014 Pittsburgh vs 7 Peers ({BASELINE_YEAR}\u2013{COMPARE_YEAR})",
                 fontsize=14, fontweight="bold", y=0.98)
    save_chart(fig, OUT / "cost_trends.png")


@run_analysis(41, "Operating Cost Drivers")
def main():
    plt = setup_plotting()
    conn = get_db()

    with phase("Loading cost data"):
        cost_df = load_cost_data(conn)
        print(f"   {len(cost_df)} rows ({BASELINE_YEAR}-{COMPARE_YEAR})")

    with phase("Loading fleet age data"):
        fleet_df = load_fleet_age(conn)
        conn.close()
        print(f"   {len(fleet_df)} vehicle type rows")

    # Print summary table
    with phase("Cost per trip breakdown (2024)"):
        df_2024 = cost_df.filter(pl.col("year") == COMPARE_YEAR).sort("cost_per_trip", descending=True)
        print(f"\n   {'City':<15s} {'Veh Ops':>8s} {'Veh Maint':>10s} {'Non-Veh':>8s} {'Gen Adm':>8s} {'Total':>8s}")
        for row in df_2024.iter_rows(named=True):
            marker = " <<<" if row["ntd_id"] == PRT_NTD_ID else ""
            print("   %-15s $%6.2f    $%6.2f  $%6.2f  $%6.2f  $%6.2f%s" % (
                row["city"], row["opexp_vo_pt"], row["opexp_vm_pt"],
                row["opexp_nvm_pt"], row["opexp_ga_pt"], row["cost_per_trip"], marker))

    with phase("Fleet age summary (2024)"):
        bus_df = fleet_df.filter(pl.col("vehicle_type") == "Bus").sort("avg_age", descending=True)
        print(f"\n   {'City':<15s} {'Buses':>6s} {'Avg Age':>8s}")
        for row in bus_df.iter_rows(named=True):
            marker = " <<<" if row["ntd_id"] == PRT_NTD_ID else ""
            age = f"{row['avg_age']:.1f}" if row["avg_age"] else "N/A"
            print(f"   {row['city']:<15s} {row['total_vehicles']:>6d} {age:>8s}{marker}")

    # Save CSV
    with phase("Saving data"):
        csv_df = df_2024.select(
            "city", "cost_per_trip", "opexp_vo_pt", "opexp_vm_pt", "opexp_nvm_pt", "opexp_ga_pt",
        )
        # Join fleet age
        bus_age_for_csv = (fleet_df.filter(pl.col("vehicle_type") == "Bus")
                           .select("city", avg_bus_age=pl.col("avg_age")))
        lrv_age_for_csv = (fleet_df.filter(pl.col("vehicle_type") == "Light Rail Vehicle")
                           .select("city", avg_lrv_age=pl.col("avg_age")))
        csv_df = csv_df.join(bus_age_for_csv, on="city", how="left")
        csv_df = csv_df.join(lrv_age_for_csv, on="city", how="left")
        save_csv(csv_df, OUT / "cost_breakdown.csv")

    # Charts
    with phase("Generating cost breakdown chart"):
        chart_cost_breakdown(plt, cost_df)

    with phase("Generating cost change chart"):
        chart_cost_change(plt, cost_df)

    with phase("Generating fleet age vs maintenance chart"):
        chart_fleet_age_vs_maintenance(plt, cost_df, fleet_df)

    with phase("Generating fleet age comparison chart"):
        chart_fleet_age_comparison(plt, fleet_df)

    with phase("Generating cost trend lines"):
        chart_cost_trends(plt, cost_df)


if __name__ == "__main__":
    main()
