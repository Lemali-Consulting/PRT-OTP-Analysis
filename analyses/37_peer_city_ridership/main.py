"""Compare Pittsburgh's ridership trajectory to 7 peer cities using NTD monthly data."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import PEERS, PRE_COVID_BASELINE_MONTH, PRE_COVID_BASELINE_YEAR, get_db, output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

# NTD mode codes for bus vs rail breakdown
BUS_MODES = {"MB", "CB", "RB", "TB"}  # motorbus, commuter bus, rapid bus, trolleybus
RAIL_MODES = {"LR", "HR", "CR", "SR", "MG", "YR"}  # light/heavy/commuter/streetcar rail


def load_monthly(conn) -> pl.DataFrame:
    """Load monthly UPT for peer agencies, Jan 2019–Dec 2025."""
    id_list = ",".join(str(i) for i in PEERS)
    rows = conn.execute(f"""
        SELECT ntd_id, mode, month, SUM(upt) AS upt
        FROM ntd_ridership
        WHERE ntd_id IN ({id_list})
          AND month >= '{PRE_COVID_BASELINE_MONTH}' AND month <= '2025-12'
        GROUP BY ntd_id, mode, month
    """).fetchall()
    return pl.DataFrame([dict(r) for r in rows])


def main():
    plt = setup_plotting()
    conn = get_db()

    print("=" * 60)
    print("Analysis 37: Peer City Ridership Comparison")
    print("=" * 60)

    # Load data
    print("\n1. Loading monthly data for peer agencies...")
    monthly = load_monthly(conn)
    conn.close()
    print(f"   {len(monthly)} rows loaded")

    # Add city label
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    monthly = monthly.join(peer_map, on="ntd_id", how="left")

    # --- All-mode totals ---
    print("\n2. Computing indexed ridership...")
    totals = (
        monthly.group_by("ntd_id", "city", "month")
        .agg(upt=pl.col("upt").sum())
        .sort("ntd_id", "month")
    )

    # Compute 2019 monthly average per agency
    baseline = (
        totals.filter(pl.col("month").str.starts_with(PRE_COVID_BASELINE_YEAR))
        .group_by("ntd_id")
        .agg(avg_2019=pl.col("upt").mean())
    )
    indexed = totals.join(baseline, on="ntd_id", how="left")
    indexed = indexed.with_columns(
        index=(pl.col("upt") / pl.col("avg_2019") * 100)
    )

    # Save CSV
    csv_data = indexed.select("city", "month", "upt", "index").sort("city", "month")
    csv_data.write_csv(OUT / "peer_ridership_data.csv")
    print(f"   Saved peer_ridership_data.csv")

    # Recovery summary: 2024 average vs 2019 average
    print("\n3. Computing recovery metrics...")
    recovery = (
        totals.filter(pl.col("month").str.starts_with("2024"))
        .group_by("ntd_id", "city")
        .agg(avg_2024=pl.col("upt").mean())
        .join(baseline, on="ntd_id", how="left")
        .with_columns(
            recovery_pct=(pl.col("avg_2024") / pl.col("avg_2019") * 100)
        )
        .sort("recovery_pct", descending=True)
    )
    recovery.select("city", "avg_2019", "avg_2024", "recovery_pct").write_csv(
        OUT / "peer_recovery_summary.csv"
    )
    print(f"   Saved peer_recovery_summary.csv")

    for row in recovery.iter_rows(named=True):
        marker = " <<<" if row["ntd_id"] == 30022 else ""
        print(f"   {row['city']:<15s} {row['recovery_pct']:>6.1f}%{marker}")

    # --- Chart 1: Indexed time series ---
    print("\n4. Generating indexed ridership chart...")
    fig, ax = plt.subplots(figsize=(14, 7))

    # Define color cycle — PRT gets a distinct color
    colors = {
        "Pittsburgh": "#E24A33",
        "Baltimore": "#4878CF",
        "Cleveland": "#6ACC65",
        "Denver": "#D65F5F",
        "St. Louis": "#B47CC7",
        "Buffalo": "#C4AD66",
        "Portland": "#77BEDB",
        "Minneapolis": "#FFB347",
    }

    for city in sorted(PEERS.values()):
        city_data = indexed.filter(pl.col("city") == city).sort("month")
        months = city_data["month"].to_list()
        vals = city_data["index"].to_list()
        lw = 2.5 if city == "Pittsburgh" else 1.2
        alpha = 1.0 if city == "Pittsburgh" else 0.7
        ax.plot(range(len(months)), vals, label=city, color=colors[city],
                linewidth=lw, alpha=alpha)

    # X-axis: show Jan of each year
    all_months = sorted(indexed["month"].unique().to_list())
    jan_ticks = [i for i, m in enumerate(all_months) if m.endswith("-01")]
    jan_labels = [all_months[i][:4] for i in jan_ticks]
    ax.set_xticks(jan_ticks)
    ax.set_xticklabels(jan_labels)

    ax.axhline(100, color="#999999", linestyle=":", linewidth=1)
    ax.set_ylabel("Indexed Ridership (2019 avg = 100)")
    ax.set_title("Peer City Ridership Trajectories (2019–2025)")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "peer_ridership_indexed.png")
    plt.close(fig)
    print(f"   Saved peer_ridership_indexed.png")

    # --- Chart 2: Recovery bar chart ---
    print("\n5. Generating recovery bar chart...")
    fig, ax = plt.subplots(figsize=(10, 6))
    rec_sorted = recovery.sort("recovery_pct", descending=True)
    cities = rec_sorted["city"].to_list()
    pcts = rec_sorted["recovery_pct"].to_list()
    bar_colors = ["#E24A33" if c == "Pittsburgh" else "#4878CF" for c in cities]

    bars = ax.bar(range(len(cities)), pcts, color=bar_colors, edgecolor="white")
    ax.set_xticks(range(len(cities)))
    ax.set_xticklabels(cities, rotation=35, ha="right")
    ax.axhline(100, color="#999999", linestyle=":", linewidth=1, label="2019 level")
    ax.set_ylabel("Recovery (% of 2019 avg)")
    ax.set_title("2024 Ridership Recovery vs 2019 — Peer Cities")
    for i, (city, pct) in enumerate(zip(cities, pcts)):
        ax.text(i, pct + 1, f"{pct:.0f}%", ha="center", va="bottom", fontsize=9)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "peer_recovery_bar.png")
    plt.close(fig)
    print(f"   Saved peer_recovery_bar.png")

    # --- Chart 3: Mode breakdown (bus vs rail) ---
    print("\n6. Generating mode breakdown chart...")

    # Classify modes and compute recovery per peer per mode-group
    monthly_classified = monthly.with_columns(
        mode_group=pl.when(pl.col("mode").is_in(BUS_MODES)).then(pl.lit("Bus"))
        .when(pl.col("mode").is_in(RAIL_MODES)).then(pl.lit("Rail"))
        .otherwise(pl.lit("Other"))
    )

    mode_totals = (
        monthly_classified
        .filter(pl.col("mode_group").is_in(["Bus", "Rail"]))
        .group_by("ntd_id", "city", "mode_group", "month")
        .agg(upt=pl.col("upt").sum())
    )

    mode_2019 = (
        mode_totals.filter(pl.col("month").str.starts_with(PRE_COVID_BASELINE_YEAR))
        .group_by("ntd_id", "city", "mode_group")
        .agg(avg_2019=pl.col("upt").mean())
    )
    mode_2024 = (
        mode_totals.filter(pl.col("month").str.starts_with("2024"))
        .group_by("ntd_id", "city", "mode_group")
        .agg(avg_2024=pl.col("upt").mean())
    )
    mode_recovery = (
        mode_2019.join(mode_2024, on=["ntd_id", "city", "mode_group"], how="inner")
        .with_columns(recovery_pct=(pl.col("avg_2024") / pl.col("avg_2019") * 100))
        .sort("city", "mode_group")
    )

    # Only keep cities with both bus and rail
    cities_both = (
        mode_recovery.group_by("city")
        .agg(n_modes=pl.col("mode_group").n_unique())
        .filter(pl.col("n_modes") == 2)["city"]
        .to_list()
    )

    if cities_both:
        mode_plot = mode_recovery.filter(pl.col("city").is_in(cities_both))

        fig, ax = plt.subplots(figsize=(10, 6))
        cities_order = sorted(cities_both)
        x = range(len(cities_order))
        width = 0.35

        bus_vals = []
        rail_vals = []
        for city in cities_order:
            city_data = mode_plot.filter(pl.col("city") == city)
            bus_row = city_data.filter(pl.col("mode_group") == "Bus")
            rail_row = city_data.filter(pl.col("mode_group") == "Rail")
            bus_vals.append(bus_row["recovery_pct"][0] if len(bus_row) > 0 else 0)
            rail_vals.append(rail_row["recovery_pct"][0] if len(rail_row) > 0 else 0)

        ax.bar([i - width / 2 for i in x], bus_vals, width, label="Bus", color="#4878CF")
        ax.bar([i + width / 2 for i in x], rail_vals, width, label="Rail", color="#E24A33")
        ax.set_xticks(list(x))
        ax.set_xticklabels(cities_order, rotation=35, ha="right")
        ax.axhline(100, color="#999999", linestyle=":", linewidth=1)
        ax.set_ylabel("Recovery (% of 2019 avg)")
        ax.set_title("2024 Bus vs Rail Recovery — Peer Cities")
        ax.legend()

        for i, (b, r) in enumerate(zip(bus_vals, rail_vals)):
            ax.text(i - width / 2, b + 1, f"{b:.0f}%", ha="center", va="bottom", fontsize=8)
            ax.text(i + width / 2, r + 1, f"{r:.0f}%", ha="center", va="bottom", fontsize=8)

        fig.tight_layout()
        fig.savefig(OUT / "peer_mode_breakdown.png")
        plt.close(fig)
        print(f"   Saved peer_mode_breakdown.png")
        print(f"   Cities with bus+rail: {cities_both}")
    else:
        print("   No cities with both bus and rail data — skipping mode breakdown chart")

    # Print mode recovery details
    print("\n   Mode recovery details:")
    for row in mode_recovery.iter_rows(named=True):
        marker = " <<<" if row["ntd_id"] == 30022 else ""
        print(f"   {row['city']:<15s} {row['mode_group']:<6s} {row['recovery_pct']:>6.1f}%{marker}")

    print("\nDone.")


if __name__ == "__main__":
    main()
