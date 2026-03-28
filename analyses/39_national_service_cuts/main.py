"""Compare 2019-to-2023 service changes (VRH) across 150 largest US transit agencies; rank PRT."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import PEERS, PRE_COVID_BASELINE_YEAR, get_db, output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

PRT_NTD_ID = 30022
TOP_N = 150


def load_service_data(conn) -> pl.DataFrame:
    """Load VRH and UPT for 2019 and 2023, pivot to wide format."""
    rows = conn.execute("""
        SELECT ntd_id, agency_name, city, state, year, vrh, upt
        FROM ntd_annual_service
        WHERE year IN (?, 2023)
          AND vrh IS NOT NULL
    """, (int(PRE_COVID_BASELINE_YEAR),)).fetchall()
    df = pl.DataFrame([dict(r) for r in rows])

    # Pivot to one row per agency with vrh_2019, vrh_2023, upt_2019, upt_2023
    vrh_wide = (
        df.select("ntd_id", "agency_name", "city", "state", "year", "vrh")
        .pivot(on="year", index=["ntd_id", "agency_name", "city", "state"], values="vrh")
        .rename({"2019": "vrh_2019", "2023": "vrh_2023"})
    )
    upt_wide = (
        df.select("ntd_id", "year", "upt")
        .pivot(on="year", index="ntd_id", values="upt")
        .rename({"2019": "upt_2019", "2023": "upt_2023"})
    )

    wide = vrh_wide.join(upt_wide, on="ntd_id", how="left")

    # Keep only agencies with VRH data in both years
    wide = wide.filter(
        pl.col("vrh_2019").is_not_null() & pl.col("vrh_2023").is_not_null()
    )

    return wide


def main():
    plt = setup_plotting()
    conn = get_db()

    print("=" * 60)
    print("Analysis 39: National Service Cuts (2019 vs 2023)")
    print("=" * 60)

    # Load data
    print("\n1. Loading service data...")
    wide = load_service_data(conn)
    conn.close()
    print(f"   {len(wide)} agencies with VRH data in both 2019 and 2023")

    # Rank by 2019 VRH and take top N
    wide = wide.sort("vrh_2019", descending=True).head(TOP_N)
    print(f"   Top {TOP_N} by 2019 VRH selected")

    # Compute percent changes
    wide = wide.with_columns(
        vrh_pct_change=((pl.col("vrh_2023") - pl.col("vrh_2019")) / pl.col("vrh_2019") * 100),
        upt_pct_change=((pl.col("upt_2023") - pl.col("upt_2019")) / pl.col("upt_2019") * 100),
    )

    # Rank by VRH change (best recovery = rank 1)
    wide = wide.sort("vrh_pct_change", descending=True).with_row_index("rank", offset=1)
    wide = wide.with_columns(pl.col("rank").cast(pl.Int64))

    result = wide.select(
        "rank", "ntd_id", "agency_name", "city", "state",
        "vrh_2019", "vrh_2023", "vrh_pct_change",
        "upt_2019", "upt_2023", "upt_pct_change",
    )

    # Summary statistics
    vrh_pct = result["vrh_pct_change"]
    median_vrh = vrh_pct.median()
    mean_vrh = vrh_pct.mean()
    q25 = vrh_pct.quantile(0.25)
    q75 = vrh_pct.quantile(0.75)
    recovered = result.filter(pl.col("vrh_pct_change") >= 0)

    print("\n2. VRH change summary:")
    print(f"   Median change: {median_vrh:.1f}%")
    print(f"   Mean change:   {mean_vrh:.1f}%")
    print(f"   IQR:           {q25:.1f}% to {q75:.1f}%")
    print(f"   Recovered to 2019 levels: {len(recovered)} / {TOP_N}")

    # PRT results
    prt = result.filter(pl.col("ntd_id") == PRT_NTD_ID)
    if len(prt) > 0:
        prt_row = prt.row(0, named=True)
        print(f"\n   PRT: rank {prt_row['rank']}/{TOP_N}, "
              f"VRH {prt_row['vrh_pct_change']:+.1f}%, "
              f"UPT {prt_row['upt_pct_change']:+.1f}%")
        print(f"   VRH: {prt_row['vrh_2019']:,.0f} → {prt_row['vrh_2023']:,.0f}")
        print(f"   UPT: {prt_row['upt_2019']:,.0f} → {prt_row['upt_2023']:,.0f}")
    else:
        print("\n   WARNING: PRT not found in top 150")
        prt_row = None

    # Save CSV
    csv_path = OUT / "service_cuts_data.csv"
    result.write_csv(csv_path)
    print(f"\n3. Saved {csv_path}")

    # --- Chart 1: VRH change histogram ---
    print("\n4. Generating VRH change histogram...")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(vrh_pct.to_list(), bins=30, color="#4878CF", edgecolor="white", alpha=0.8)
    ax.axvline(median_vrh, color="#333333", linestyle="--", linewidth=1.5,
               label=f"Median: {median_vrh:.1f}%")
    ax.axvline(0, color="#999999", linestyle=":", linewidth=1)
    if prt_row:
        prt_vrh_pct = prt_row["vrh_pct_change"]
        ax.axvline(prt_vrh_pct, color="#E24A33", linestyle="-", linewidth=2.5,
                   label=f"PRT: {prt_vrh_pct:+.1f}%")
    ax.set_xlabel("Vehicle Revenue Hours Change 2019 → 2023 (%)")
    ax.set_ylabel("Number of Agencies")
    ax.set_title(f"Service Change Distribution — Top {TOP_N} US Transit Agencies")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "service_cuts_distribution.png")
    plt.close(fig)
    print("   Saved service_cuts_distribution.png")

    # --- Chart 2: Ranking bar chart ---
    print("\n5. Generating ranking bar chart...")
    sorted_df = result.sort("vrh_pct_change")
    agencies = sorted_df["agency_name"].to_list()
    changes = sorted_df["vrh_pct_change"].to_list()
    ntd_ids = sorted_df["ntd_id"].to_list()
    colors = ["#E24A33" if nid == PRT_NTD_ID else "#4878CF" for nid in ntd_ids]

    fig, ax = plt.subplots(figsize=(14, max(30, TOP_N * 0.22)))
    ax.barh(range(len(agencies)), changes, color=colors, height=0.8)
    ax.set_yticks(range(len(agencies)))
    ax.set_yticklabels(agencies, fontsize=6)
    ax.set_xlabel("Vehicle Revenue Hours Change 2019 → 2023 (%)")
    ax.set_title(f"Service Change Ranking — Top {TOP_N} US Transit Agencies")
    ax.axvline(0, color="#999999", linestyle=":", linewidth=1)

    if prt_row:
        prt_idx = [i for i, nid in enumerate(ntd_ids) if nid == PRT_NTD_ID]
        if prt_idx:
            ax.get_yticklabels()[prt_idx[0]].set_color("#E24A33")
            ax.get_yticklabels()[prt_idx[0]].set_fontweight("bold")
            ax.get_yticklabels()[prt_idx[0]].set_fontsize(7)

    fig.tight_layout()
    fig.savefig(OUT / "service_cuts_ranking.png")
    plt.close(fig)
    print("   Saved service_cuts_ranking.png")

    # --- Chart 3: Peer city VRH vs UPT change ---
    print("\n6. Generating peer city comparison...")
    peer_ids = list(PEERS.keys())
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city_label": list(PEERS.values()),
    })
    peer_data = result.filter(pl.col("ntd_id").is_in(peer_ids))
    peer_data = peer_data.join(peer_map, on="ntd_id", how="left")
    peer_data = peer_data.sort("vrh_pct_change", descending=True)

    if len(peer_data) > 0:
        cities = peer_data["city_label"].to_list()
        vrh_changes = peer_data["vrh_pct_change"].to_list()
        upt_changes = peer_data["upt_pct_change"].to_list()

        fig, ax = plt.subplots(figsize=(12, 7))
        x = range(len(cities))
        width = 0.35

        bars_vrh = ax.bar([i - width / 2 for i in x], vrh_changes, width,
                          label="VRH (Service)", color="#4878CF")
        bars_upt = ax.bar([i + width / 2 for i in x], upt_changes, width,
                          label="UPT (Ridership)", color="#E24A33")

        ax.set_xticks(list(x))
        ax.set_xticklabels(cities, rotation=35, ha="right")
        ax.axhline(0, color="#999999", linestyle=":", linewidth=1)
        ax.set_ylabel("Change 2019 → 2023 (%)")
        ax.set_title("Service Cuts vs Ridership Loss — Peer Cities")
        ax.legend()

        for i, (v, u) in enumerate(zip(vrh_changes, upt_changes)):
            ax.text(i - width / 2, v - 2 if v < 0 else v + 1,
                    f"{v:+.0f}%", ha="center", va="top" if v < 0 else "bottom", fontsize=8)
            ax.text(i + width / 2, u - 2 if u < 0 else u + 1,
                    f"{u:+.0f}%", ha="center", va="top" if u < 0 else "bottom", fontsize=8)

        fig.tight_layout()
        fig.savefig(OUT / "peer_service_vs_ridership.png")
        plt.close(fig)
        print("   Saved peer_service_vs_ridership.png")

        print("\n   Peer city details:")
        for row in peer_data.iter_rows(named=True):
            marker = " <<<" if row["ntd_id"] == PRT_NTD_ID else ""
            gap = row["vrh_pct_change"] - row["upt_pct_change"]
            print(f"   {row['city_label']:<15s} VRH: {row['vrh_pct_change']:>+6.1f}%  "
                  f"UPT: {row['upt_pct_change']:>+6.1f}%  "
                  f"gap: {gap:>+6.1f} pp{marker}")
    else:
        print("   WARNING: No peer cities found in top 150")

    # --- Chart 4: Supply vs demand scatter ---
    print("\n7. Generating supply vs demand scatter...")
    scatter_data = result.filter(
        pl.col("vrh_pct_change").is_not_null() & pl.col("upt_pct_change").is_not_null()
    )

    fig, ax = plt.subplots(figsize=(10, 10))

    # All agencies
    vrh_vals = scatter_data["vrh_pct_change"].to_list()
    upt_vals = scatter_data["upt_pct_change"].to_list()
    ax.scatter(vrh_vals, upt_vals, color="#4878CF", alpha=0.4, s=30, zorder=2)

    # Diagonal y=x line
    lim_min = min(min(vrh_vals), min(upt_vals)) - 5
    lim_max = max(max(vrh_vals), max(upt_vals)) + 5
    ax.plot([lim_min, lim_max], [lim_min, lim_max], color="#999999", linestyle="--",
            linewidth=1, zorder=1, label="VRH = UPT change")

    # Highlight peer cities
    peer_colors = {
        "Pittsburgh": "#E24A33",
        "Baltimore": "#4878CF",
        "Cleveland": "#6ACC65",
        "Denver": "#D65F5F",
        "St. Louis": "#B47CC7",
        "Buffalo": "#C4AD66",
        "Portland": "#77BEDB",
        "Minneapolis": "#FFB347",
    }
    for row in peer_data.iter_rows(named=True):
        label = row["city_label"]
        color = peer_colors.get(label, "#333333")
        marker_size = 120 if row["ntd_id"] == PRT_NTD_ID else 80
        marker_shape = "D" if row["ntd_id"] == PRT_NTD_ID else "o"
        ax.scatter(row["vrh_pct_change"], row["upt_pct_change"],
                   color=color, s=marker_size, marker=marker_shape,
                   edgecolors="black", linewidths=1, zorder=3)
        ax.annotate(label,
                    (row["vrh_pct_change"], row["upt_pct_change"]),
                    textcoords="offset points", xytext=(8, 8), fontsize=8,
                    fontweight="bold" if row["ntd_id"] == PRT_NTD_ID else "normal")

    # Quadrant labels
    ax.text(0.02, 0.02, "Cut service +\nLost riders",
            transform=ax.transAxes, fontsize=9, color="#888888", va="bottom")
    ax.text(0.98, 0.02, "Grew service +\nLost riders",
            transform=ax.transAxes, fontsize=9, color="#888888", va="bottom", ha="right")
    ax.text(0.02, 0.98, "Cut service +\nGrew riders",
            transform=ax.transAxes, fontsize=9, color="#888888", va="top")
    ax.text(0.98, 0.98, "Grew service +\nGrew riders",
            transform=ax.transAxes, fontsize=9, color="#888888", va="top", ha="right")

    ax.axhline(0, color="#CCCCCC", linestyle=":", linewidth=0.8)
    ax.axvline(0, color="#CCCCCC", linestyle=":", linewidth=0.8)
    ax.set_xlabel("Vehicle Revenue Hours Change 2019 → 2023 (%)")
    ax.set_ylabel("Ridership (UPT) Change 2019 → 2023 (%)")
    ax.set_title("Supply vs Demand: Service Cuts vs Ridership Loss")
    ax.legend(loc="upper left")
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()
    fig.savefig(OUT / "supply_vs_demand_scatter.png")
    plt.close(fig)
    print("   Saved supply_vs_demand_scatter.png")

    # Quadrant summary
    above_diag = scatter_data.filter(
        pl.col("upt_pct_change") > pl.col("vrh_pct_change")
    )
    below_diag = scatter_data.filter(
        pl.col("upt_pct_change") <= pl.col("vrh_pct_change")
    )
    print(f"\n   Above diagonal (ridership outpaced service): {len(above_diag)}")
    print(f"   Below diagonal (service outpaced ridership): {len(below_diag)}")

    # Top and bottom 10
    print("\n8. Top 10 service recoveries:")
    for row in result.head(10).iter_rows(named=True):
        print(f"   {row['rank']:>3d}. {row['agency_name']:<50s} VRH: {row['vrh_pct_change']:>+7.1f}%")

    print("\n   Bottom 10:")
    for row in result.tail(10).iter_rows(named=True):
        print(f"   {row['rank']:>3d}. {row['agency_name']:<50s} VRH: {row['vrh_pct_change']:>+7.1f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
