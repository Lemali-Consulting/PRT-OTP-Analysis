"""Compare 2019-to-2024 ridership recovery across the 150 largest US transit agencies; rank PRT."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import PRE_COVID_BASELINE_YEAR, get_db, output_dir, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

PRT_NTD_ID = 30022
MIN_MONTHS = 10  # require at least 10 months of data per year
TOP_N = 150


def load_agency_totals(conn) -> pl.DataFrame:
    """Sum UPT by agency for 2019 and 2024, requiring MIN_MONTHS months each."""
    rows = conn.execute("""
        SELECT
            ntd_id,
            SUBSTR(month, 1, 4) AS year,
            SUM(upt) AS total_upt,
            COUNT(CASE WHEN upt IS NOT NULL THEN 1 END) AS n_months
        FROM ntd_ridership
        WHERE SUBSTR(month, 1, 4) IN (?, '2024')
        GROUP BY ntd_id, SUBSTR(month, 1, 4)
    """, (PRE_COVID_BASELINE_YEAR,)).fetchall()

    df = pl.DataFrame([dict(r) for r in rows])

    # Require minimum months in both years
    df = df.filter(pl.col("n_months") >= MIN_MONTHS)

    # Pivot to wide: one row per agency with upt_2019 and upt_2024
    wide = df.pivot(on="year", index="ntd_id", values="total_upt")
    wide = wide.rename({"2019": "upt_2019", "2024": "upt_2024"})

    # Keep only agencies with data in both years
    wide = wide.filter(
        pl.col("upt_2019").is_not_null() & pl.col("upt_2024").is_not_null()
    )

    return wide


def main():
    plt = setup_plotting()
    conn = get_db()

    print("=" * 60)
    print("Analysis 36: National Ridership Growth (2019 vs 2024)")
    print("=" * 60)

    # Load data
    print("\n1. Loading agency totals...")
    wide = load_agency_totals(conn)
    print(f"   {len(wide)} agencies with valid data in both 2019 and 2024")

    # Rank by 2019 UPT and take top N
    wide = wide.sort("upt_2019", descending=True).head(TOP_N)
    print(f"   Top {TOP_N} by 2019 ridership selected")

    # Compute percent change
    wide = wide.with_columns(
        pct_change=((pl.col("upt_2024") - pl.col("upt_2019")) / pl.col("upt_2019") * 100)
    )

    # Rank by pct_change (best recovery = rank 1)
    wide = wide.sort("pct_change", descending=True).with_row_index("rank", offset=1)
    wide = wide.with_columns(pl.col("rank").cast(pl.Int64))

    # Join agency names
    name_rows = conn.execute(
        "SELECT DISTINCT ntd_id, agency_name FROM ntd_agency"
    ).fetchall()
    names = pl.DataFrame([dict(r) for r in name_rows])
    result = wide.join(names, on="ntd_id", how="left")
    result = result.select("rank", "ntd_id", "agency_name", "upt_2019", "upt_2024", "pct_change")

    conn.close()

    # Summary statistics
    pct = result["pct_change"]
    median_pct = pct.median()
    mean_pct = pct.mean()
    q25 = pct.quantile(0.25)
    q75 = pct.quantile(0.75)
    recovered = result.filter(pl.col("pct_change") >= 0)

    print("\n2. Summary statistics:")
    print(f"   Median change: {median_pct:.1f}%")
    print(f"   Mean change:   {mean_pct:.1f}%")
    print(f"   IQR:           {q25:.1f}% to {q75:.1f}%")
    print(f"   Recovered to 2019 levels: {len(recovered)} / {TOP_N} ({len(recovered)/TOP_N*100:.0f}%)")

    # PRT results
    prt = result.filter(pl.col("ntd_id") == PRT_NTD_ID)
    if len(prt) > 0:
        prt_row = prt.row(0, named=True)
        print(f"\n   PRT: rank {prt_row['rank']}/{TOP_N}, "
              f"{prt_row['pct_change']:+.1f}% change "
              f"({prt_row['upt_2019']:,.0f} → {prt_row['upt_2024']:,.0f})")
    else:
        print("\n   WARNING: PRT not found in top 150")

    # Save CSV
    csv_path = OUT / "ridership_growth_data.csv"
    result.write_csv(csv_path)
    print(f"\n3. Saved {csv_path}")

    # --- Chart 1: Histogram ---
    print("\n4. Generating histogram...")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.hist(pct.to_list(), bins=30, color="#4878CF", edgecolor="white", alpha=0.8)
    ax.axvline(median_pct, color="#333333", linestyle="--", linewidth=1.5, label=f"Median: {median_pct:.1f}%")
    ax.axvline(0, color="#999999", linestyle=":", linewidth=1)
    if len(prt) > 0:
        prt_pct = prt_row["pct_change"]
        ax.axvline(prt_pct, color="#E24A33", linestyle="-", linewidth=2.5,
                   label=f"PRT: {prt_pct:+.1f}%")
    ax.set_xlabel("Ridership Change 2019 → 2024 (%)")
    ax.set_ylabel("Number of Agencies")
    ax.set_title(f"Ridership Recovery Distribution — Top {TOP_N} US Transit Agencies")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "ridership_growth_distribution.png")
    plt.close(fig)
    print(f"   Saved ridership_growth_distribution.png")

    # --- Chart 2: Horizontal bar ranking ---
    print("\n5. Generating ranking bar chart...")
    sorted_df = result.sort("pct_change")
    agencies = sorted_df["agency_name"].to_list()
    changes = sorted_df["pct_change"].to_list()
    ntd_ids = sorted_df["ntd_id"].to_list()
    colors = ["#E24A33" if nid == PRT_NTD_ID else "#4878CF" for nid in ntd_ids]

    fig, ax = plt.subplots(figsize=(14, max(30, TOP_N * 0.22)))
    bars = ax.barh(range(len(agencies)), changes, color=colors, height=0.8)
    ax.set_yticks(range(len(agencies)))
    ax.set_yticklabels(agencies, fontsize=6)
    ax.set_xlabel("Ridership Change 2019 → 2024 (%)")
    ax.set_title(f"Ridership Recovery Ranking — Top {TOP_N} US Transit Agencies")
    ax.axvline(0, color="#999999", linestyle=":", linewidth=1)

    # Highlight PRT label
    if len(prt) > 0:
        prt_idx = [i for i, nid in enumerate(ntd_ids) if nid == PRT_NTD_ID]
        if prt_idx:
            ax.get_yticklabels()[prt_idx[0]].set_color("#E24A33")
            ax.get_yticklabels()[prt_idx[0]].set_fontweight("bold")
            ax.get_yticklabels()[prt_idx[0]].set_fontsize(7)

    fig.tight_layout()
    fig.savefig(OUT / "ridership_growth_ranking.png")
    plt.close(fig)
    print(f"   Saved ridership_growth_ranking.png")

    # Top and bottom 10
    print("\n6. Top 10 recoveries:")
    for row in result.head(10).iter_rows(named=True):
        print(f"   {row['rank']:>3d}. {row['agency_name']:<50s} {row['pct_change']:>+7.1f}%")

    print("\n   Bottom 10:")
    for row in result.tail(10).iter_rows(named=True):
        print(f"   {row['rank']:>3d}. {row['agency_name']:<50s} {row['pct_change']:>+7.1f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
