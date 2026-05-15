"""Analysis 48: tracks PRT service productivity (passengers per vehicle revenue
hour) from 1991 to 2024 and benchmarks it against peer cities."""

import math

import polars as pl

from prt_otp_analysis.common import (
    COLOR_GRAY,
    COLOR_PRIMARY,
    PEERS,
    analysis_dir,
    get_db,
    phase,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)
from prt_otp_analysis.common.schemas import NTD_ANNUAL_SERVICE, validate

OUT = analysis_dir(__file__)

PRT_NTD_ID = 30022
START_YEAR = 1991
COVID_YEAR = 2020
BASELINE_YEAR = 2019
COMPARE_YEAR = 2024

# Allegheny County resident population -- PRT's service area. Decennial U.S.
# Census counts (1990-2020) plus the Census Bureau's Vintage 2024 Population
# Estimates Program figure (2020 census base of 1,250,578 less the reported
# 18,769 decline over 2020-2024). Used to normalize ridership per resident.
COUNTY_POPULATION = {
    1990: 1_336_449,
    2000: 1_281_666,
    2010: 1_223_348,
    2020: 1_250_578,
    2024: 1_231_809,
}
# The productivity record starts in 1991; the nearest decennial count is the
# 1990 census, used as the 1991 population anchor (a ~9-month offset).
POP_ANCHOR_YEARS = {1991: 1990, 2000: 2000, 2010: 2010, 2020: 2020, 2024: 2024}


def load_peer_productivity() -> pl.DataFrame:
    """Load annual UPT and VRH for all peer cities and derive productivity.

    Productivity is unlinked passenger trips per vehicle revenue hour
    (UPT / VRH) -- how many riders each hour of service carried.
    """
    id_list = ",".join(str(i) for i in PEERS)
    df = query_ntd(f"""
        SELECT ntd_id, year, upt, vrh
        FROM ntd_annual_service
        WHERE ntd_id IN ({id_list})
        ORDER BY ntd_id, year
    """)
    peer_map = pl.DataFrame({
        "ntd_id": list(PEERS.keys()),
        "city": list(PEERS.values()),
    })
    df = df.join(peer_map, on="ntd_id", how="left")
    return df.with_columns(productivity=(pl.col("upt") / pl.col("vrh")))


def query_ntd(sql: str) -> pl.DataFrame:
    """Run a query against ntd_annual_service and validate the result schema."""
    conn = get_db()
    try:
        rows = conn.execute(sql).fetchall()
    finally:
        conn.close()
    df = pl.DataFrame(
        [dict(r) for r in rows],
        schema={"ntd_id": pl.Int64, "year": pl.Int64,
                "upt": pl.Float64, "vrh": pl.Float64},
    )
    return validate(df, NTD_ANNUAL_SERVICE, subset=True)


def chart_prt_trend(plt, prt_df: pl.DataFrame) -> None:
    """Line chart of PRT productivity across the full 1991-2024 record."""
    fig, ax = plt.subplots(figsize=(12, 6))
    years = prt_df["year"].to_list()
    vals = prt_df["productivity"].to_list()

    ax.plot(years, vals, color=COLOR_PRIMARY, linewidth=2.5, marker="o", markersize=4)
    ax.axvline(COVID_YEAR, color=COLOR_GRAY, linestyle="--", linewidth=1)
    ax.text(COVID_YEAR + 0.3, max(vals) * 0.97, "COVID-19", fontsize=9, color="#555555")

    first, last = vals[0], vals[-1]
    ax.annotate(f"{first:.1f}", (years[0], first), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=9, fontweight="bold")
    ax.annotate(f"{last:.1f}", (years[-1], last), textcoords="offset points",
                xytext=(0, 10), ha="center", fontsize=9, fontweight="bold")

    ax.set_ylabel("Passengers per Vehicle Revenue Hour")
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    ax.set_title("PRT Service Productivity, 1991–2024")
    save_chart(fig, OUT / "prt_productivity_trend.png")


def chart_decomposition(plt, prt_df: pl.DataFrame) -> None:
    """Index ridership, service hours, and productivity to 1991 = 100.

    Separates the two halves of the productivity ratio: if VRH (supply) holds
    flat while UPT (demand) collapses, the decline is empty buses, not a
    deliberate right-sizing of service.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    years = prt_df["year"].to_list()

    for col, label, color, lw in [
        ("vrh", "Service hours (VRH)", "#6ACC65", 2.0),
        ("upt", "Ridership (UPT)", "#4878CF", 2.0),
        ("productivity", "Productivity (UPT/VRH)", COLOR_PRIMARY, 2.8),
    ]:
        vals = prt_df[col].to_list()
        base = vals[0]
        ax.plot(years, [v / base * 100 for v in vals], label=label,
                color=color, linewidth=lw, marker="o", markersize=3)

    ax.axhline(100, color=COLOR_GRAY, linestyle=":", linewidth=0.8)
    ax.set_ylabel("Indexed to 1991 = 100")
    ax.set_xlabel("Year")
    ax.set_title("PRT Ridership vs. Service Hours — Why Productivity Fell")
    ax.legend()
    save_chart(fig, OUT / "supply_vs_demand_decomposition.png")


def chart_peer_2024(plt, peer_df: pl.DataFrame) -> None:
    """Bar chart ranking peer cities by 2024 productivity, PRT highlighted."""
    fig, ax = plt.subplots(figsize=(10, 6))
    snap_df = peer_df.filter(pl.col("year") == COMPARE_YEAR).sort("productivity")
    cities = snap_df["city"].to_list()
    vals = snap_df["productivity"].to_list()
    colors = [COLOR_PRIMARY if c == "Pittsburgh" else COLOR_GRAY for c in cities]

    ax.barh(cities, vals, color=colors, edgecolor="white")
    for i, v in enumerate(vals):
        ax.text(v + 0.3, i, f"{v:.1f}", va="center", fontsize=9)

    ax.set_xlabel("Passengers per Vehicle Revenue Hour")
    ax.set_title(f"Service Productivity by Peer City, {COMPARE_YEAR}")
    save_chart(fig, OUT / "peer_productivity_2024.png")


def chart_peer_trends(plt, peer_df: pl.DataFrame) -> None:
    """Line chart of productivity 1991-2024 for all peers, PRT highlighted."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for city in sorted(PEERS.values()):
        city_df = peer_df.filter(pl.col("city") == city).sort("year")
        is_prt = city == "Pittsburgh"
        ax.plot(
            city_df["year"].to_list(), city_df["productivity"].to_list(),
            label=city,
            color=COLOR_PRIMARY if is_prt else None,
            linewidth=2.8 if is_prt else 1.2,
            alpha=1.0 if is_prt else 0.6,
            zorder=10 if is_prt else 1,
        )
    ax.set_ylabel("Passengers per Vehicle Revenue Hour")
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    ax.set_title("Service Productivity — Pittsburgh vs. 7 Peer Cities, 1991–2024")
    ax.legend(fontsize=8, ncol=2)
    save_chart(fig, OUT / "peer_productivity_trends.png")


def peer_change_table(peer_df: pl.DataFrame) -> pl.DataFrame:
    """Wide table of productivity at 1991, 2019, and 2024 with percent changes."""
    keep = peer_df.filter(pl.col("year").is_in([START_YEAR, BASELINE_YEAR, COMPARE_YEAR]))
    wide = keep.pivot(values="productivity", index="city", on="year")
    wide = wide.rename({str(START_YEAR): "prod_1991",
                        str(BASELINE_YEAR): "prod_2019",
                        str(COMPARE_YEAR): "prod_2024"})
    return wide.with_columns(
        pct_change_1991_2024=((pl.col("prod_2024") - pl.col("prod_1991"))
                              / pl.col("prod_1991") * 100),
        pct_change_2019_2024=((pl.col("prod_2024") - pl.col("prod_2019"))
                              / pl.col("prod_2019") * 100),
    ).sort("prod_2024", descending=True)


def per_capita_decomposition(prt_df: pl.DataFrame) -> pl.DataFrame:
    """Normalize PRT ridership by Allegheny County population.

    Pairs each census/estimate year with the matching year in the NTD
    productivity record and derives ridership per resident (UPT / population).
    This splits the ridership decline into a population component (fewer
    residents) and a per-capita-usage component (each resident riding less).
    """
    rows = []
    for ntd_year, pop_year in POP_ANCHOR_YEARS.items():
        r = prt_df.filter(pl.col("year") == ntd_year).row(0, named=True)
        pop = COUNTY_POPULATION[pop_year]
        rows.append({
            "year": ntd_year,
            "population": pop,
            "upt": r["upt"],
            "vrh": r["vrh"],
            "productivity": r["productivity"],
            "trips_per_capita": r["upt"] / pop,
        })
    return pl.DataFrame(rows)


def chart_per_capita(plt, norm_df: pl.DataFrame) -> None:
    """Index population, total ridership, and per-capita ridership to 1991 = 100.

    Shows that PRT's ridership collapse is overwhelmingly fewer trips per
    resident, not fewer residents: county population barely moved while
    ridership per resident roughly halved.
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    years = norm_df["year"].to_list()

    for col, label, color, lw in [
        ("population", "Allegheny County population", "#6ACC65", 2.0),
        ("upt", "Total ridership (UPT)", "#4878CF", 2.0),
        ("trips_per_capita", "Ridership per resident", COLOR_PRIMARY, 2.8),
    ]:
        vals = norm_df[col].to_list()
        base = vals[0]
        ax.plot(years, [v / base * 100 for v in vals], label=label,
                color=color, linewidth=lw, marker="o", markersize=6)

    ax.axhline(100, color=COLOR_GRAY, linestyle=":", linewidth=0.8)
    ax.set_ylabel("Indexed to 1991 = 100")
    ax.set_xlabel("Year")
    ax.set_ylim(bottom=0)
    ax.set_title("PRT Ridership per Resident vs. Population — Allegheny County")
    ax.legend()
    save_chart(fig, OUT / "per_capita_normalization.png")


@run_analysis(48, "Service Productivity")
def main():
    plt = setup_plotting()

    with phase("Loading NTD productivity data"):
        peer_df = load_peer_productivity()
        prt_df = peer_df.filter(pl.col("ntd_id") == PRT_NTD_ID).sort("year")
        print(f"   {len(peer_df)} city-years across {peer_df['city'].n_unique()} agencies")
        print(f"   PRT record: {prt_df['year'].min()}–{prt_df['year'].max()}")

    with phase("Summarizing PRT trajectory"):
        first = prt_df.row(0, named=True)
        last = prt_df.row(-1, named=True)
        drop = (last["productivity"] - first["productivity"]) / first["productivity"] * 100
        print(f"   {first['year']}: {first['productivity']:.1f} pax/VRH")
        print(f"   {last['year']}: {last['productivity']:.1f} pax/VRH  ({drop:+.0f}%)")
        vrh_chg = (last["vrh"] - first["vrh"]) / first["vrh"] * 100
        upt_chg = (last["upt"] - first["upt"]) / first["upt"] * 100
        print(f"   over the period: VRH {vrh_chg:+.0f}%, UPT {upt_chg:+.0f}%")

    with phase("Computing peer change table"):
        change_df = peer_change_table(peer_df)
        print(f"\n   {'City':<14s} {'1991':>7s} {'2019':>7s} {'2024':>7s} "
              f"{'91→24':>9s} {'19→24':>9s}")
        for r in change_df.iter_rows(named=True):
            mark = " <<<" if r["city"] == "Pittsburgh" else ""
            print("   %-14s %7.1f %7.1f %7.1f %+8.0f%% %+8.0f%%%s" % (
                r["city"], r["prod_1991"], r["prod_2019"], r["prod_2024"],
                r["pct_change_1991_2024"], r["pct_change_2019_2024"], mark))

    with phase("Normalizing ridership by population"):
        norm_df = per_capita_decomposition(prt_df)
        base = norm_df.row(0, named=True)
        end = norm_df.row(-1, named=True)
        pop_ratio = end["population"] / base["population"]
        upt_ratio = end["upt"] / base["upt"]
        pc_ratio = end["trips_per_capita"] / base["trips_per_capita"]
        # Multiplicative decomposition: UPT = population x trips-per-capita.
        # Log shares partition the ridership decline between the two factors.
        pop_share = math.log(pop_ratio) / math.log(upt_ratio)
        pc_share = math.log(pc_ratio) / math.log(upt_ratio)
        print(f"   Allegheny County population {base['year']}: "
              f"{base['population']:,} (1990 census)")
        print(f"   Allegheny County population {end['year']}: "
              f"{end['population']:,}  ({(pop_ratio - 1) * 100:+.0f}%)")
        print(f"   ridership per resident: {base['trips_per_capita']:.1f} → "
              f"{end['trips_per_capita']:.1f} trips/resident/yr  "
              f"({(pc_ratio - 1) * 100:+.0f}%)")
        print(f"   share of ridership decline from population loss: "
              f"{pop_share * 100:.0f}%")
        print(f"   share of ridership decline from lower per-capita use: "
              f"{pc_share * 100:.0f}%")

    with phase("Saving data"):
        save_csv(prt_df.select("year", "upt", "vrh", "productivity"),
                 OUT / "prt_productivity_by_year.csv")
        save_csv(change_df, OUT / "peer_productivity.csv")
        save_csv(norm_df, OUT / "per_capita_decomposition.csv")

    with phase("Generating charts"):
        chart_prt_trend(plt, prt_df)
        chart_decomposition(plt, prt_df)
        chart_peer_2024(plt, peer_df)
        chart_peer_trends(plt, peer_df)
        chart_per_capita(plt, norm_df)


if __name__ == "__main__":
    main()
