"""Tract-level equity analysis: OTP aggregated by ACS census tract.

Replaces the fuzzy `stops.hood` field (NULL for ~58% of stops, only 89 hand-curated
neighborhoods) with point-in-polygon assignment to TIGER 2022 census tracts. Adds
income/vehicle/race demographic context per tract.
"""

import polars as pl

from prt_otp_analysis.common import (
    analysis_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
    weighted_mean,
)
from prt_otp_analysis.stop_tracts import assign_stops_to_tracts

OUT = analysis_dir(__file__)

MIN_MONTHS = 12  # minimum months of OTP data per route
MIN_ROUTES = 2   # tract-level estimates from a single route are too noisy to rank


def load_route_otp() -> pl.DataFrame:
    """Route-level mean OTP, restricted to routes with >= MIN_MONTHS observations."""
    return query_to_polars(f"""
        SELECT route_id, AVG(otp) AS avg_otp
        FROM otp_monthly
        GROUP BY route_id
        HAVING COUNT(*) >= {MIN_MONTHS}
    """)


def load_route_stops() -> pl.DataFrame:
    """route_stops with non-null trips_7d for trip weighting."""
    return query_to_polars(
        "SELECT route_id, stop_id, trips_7d FROM route_stops WHERE trips_7d IS NOT NULL"
    )


def load_stop_muni() -> pl.DataFrame:
    """muni/county from stops table for tract-label readability."""
    return query_to_polars("SELECT stop_id, muni, county FROM stops")


def load_route_modes() -> pl.DataFrame:
    return query_to_polars("SELECT route_id, mode FROM routes")


def load_monthly_route() -> pl.DataFrame:
    """Monthly OTP for routes meeting MIN_MONTHS, for the quintile time series."""
    return query_to_polars(f"""
        SELECT route_id, month, otp
        FROM otp_monthly
        WHERE route_id IN (
            SELECT route_id FROM otp_monthly GROUP BY route_id HAVING COUNT(*) >= {MIN_MONTHS}
        )
    """)


def build_route_stop_tract(
    route_otp_df: pl.DataFrame,
    route_stops_df: pl.DataFrame,
    stop_tract_df: pl.DataFrame,
) -> pl.DataFrame:
    """Join route-level OTP, route_stops weights, and stop→tract assignment."""
    return (
        route_stops_df.join(route_otp_df, on="route_id")
        .join(stop_tract_df, on="stop_id")
    )


def primary_muni_per_tract(stop_tract_df: pl.DataFrame, stop_muni_df: pl.DataFrame) -> pl.DataFrame:
    """Pick the most-common (muni, county) among the stops in each tract for human-readable labels."""
    joined = stop_tract_df.select("stop_id", "geoid").join(stop_muni_df, on="stop_id")
    counts = (
        joined.filter(pl.col("muni").is_not_null() & (pl.col("muni") != "0"))
        .group_by(["geoid", "muni", "county"])
        .agg(n=pl.len())
    )
    return (
        counts.sort(["geoid", "n"], descending=[False, True])
        .group_by("geoid", maintain_order=True)
        .agg(primary_muni=pl.col("muni").first(), primary_county=pl.col("county").first())
    )


def tract_label(geoid: str, muni: str | None) -> str:
    """Human-readable tract label: 'Pittsburgh 020100' or just '020100' if no muni."""
    code = geoid[-6:].lstrip("0") or geoid[-6:]
    return f"{muni} {code}" if muni else f"Tract {code}"


def analyze(
    rst_df: pl.DataFrame,
    muni_df: pl.DataFrame,
    tract_demo_df: pl.DataFrame,
) -> pl.DataFrame:
    """Compute per-tract weighted/unweighted OTP, demographics, and a readable label."""
    tract_summary = (
        rst_df.group_by("geoid")
        .agg(
            weighted_otp=weighted_mean("avg_otp", "trips_7d"),
            route_count=pl.col("route_id").n_unique(),
            stop_count=pl.col("stop_id").n_unique(),
            total_trips_7d=pl.col("trips_7d").sum(),
        )
    )

    route_tract = (
        rst_df.group_by(["geoid", "route_id"])
        .agg(avg_otp=pl.col("avg_otp").first())
    )
    tract_unweighted = (
        route_tract.group_by("geoid")
        .agg(unweighted_otp=pl.col("avg_otp").mean())
    )

    out = (
        tract_summary
        .join(tract_unweighted, on="geoid", how="left")
        .join(muni_df, on="geoid", how="left")
        .join(tract_demo_df, on="geoid", how="left")
        .with_columns(
            otp_gap=pl.col("weighted_otp") - pl.col("unweighted_otp"),
            pct_zero_vehicle=(
                pl.col("households_zero_vehicle") / pl.col("households_total")
            ),
            pct_nonwhite=(
                1.0 - (pl.col("pop_white_nh") / pl.col("population"))
            ),
        )
        .with_columns(
            label=pl.struct("geoid", "primary_muni").map_elements(
                lambda r: tract_label(r["geoid"], r["primary_muni"]),
                return_dtype=pl.Utf8,
            ),
        )
        .filter(pl.col("route_count") >= MIN_ROUTES)
        .sort("weighted_otp")
    )
    return out


def analyze_bus_only(
    rst_df: pl.DataFrame,
    route_modes_df: pl.DataFrame,
) -> pl.DataFrame:
    bus = (
        rst_df.join(route_modes_df, on="route_id")
        .filter(pl.col("mode") == "BUS")
    )
    return (
        bus.group_by("geoid")
        .agg(
            bus_weighted_otp=weighted_mean("avg_otp", "trips_7d"),
            bus_route_count=pl.col("route_id").n_unique(),
        )
    )


def analyze_quintile_ts(
    monthly_df: pl.DataFrame,
    route_stops_df: pl.DataFrame,
    stop_tract_df: pl.DataFrame,
) -> pl.DataFrame:
    """Tract-month weighted OTP, then trailing-12-month rolling quintiles."""
    rs_tract = route_stops_df.join(stop_tract_df.select("stop_id", "geoid"), on="stop_id")

    rsm = (
        rs_tract.join(monthly_df, on="route_id")
        .group_by(["geoid", "month"])
        .agg(weighted_otp=weighted_mean("otp", "trips_7d"))
        .sort(["geoid", "month"])
    )
    rsm = rsm.with_columns(
        rolling_otp=pl.col("weighted_otp")
        .rolling_mean(window_size=12, min_samples=6)
        .over("geoid"),
    ).filter(pl.col("rolling_otp").is_not_null())

    rsm = rsm.with_columns(
        quintile=(
            ((pl.col("rolling_otp").rank().over("month") - 1)
             / pl.col("rolling_otp").count().over("month") * 5)
            .cast(pl.Int32).clip(0, 4) + 1
        ),
    )
    return (
        rsm.group_by(["quintile", "month"])
        .agg(avg_otp=pl.col("weighted_otp").mean())
        .sort(["quintile", "month"])
    )


def analyze_income_gradient(tract_summary: pl.DataFrame) -> pl.DataFrame:
    """Bin tracts by trip-weighted-population income quintile, report mean OTP per bin."""
    df = tract_summary.filter(
        pl.col("median_household_income").is_not_null()
        & pl.col("weighted_otp").is_not_null()
    )
    if len(df) < 5:
        return pl.DataFrame()
    df = df.with_columns(
        income_quintile=(
            ((pl.col("median_household_income").rank() - 1)
             / pl.len() * 5)
            .cast(pl.Int32).clip(0, 4) + 1
        ),
    )
    return (
        df.group_by("income_quintile")
        .agg(
            mean_otp=pl.col("weighted_otp").mean(),
            mean_income=pl.col("median_household_income").mean(),
            n_tracts=pl.len(),
            total_trips_7d=pl.col("total_trips_7d").sum(),
            trip_weighted_otp=weighted_mean("weighted_otp", "total_trips_7d"),
        )
        .sort("income_quintile")
    )


def make_chart(tract_summary: pl.DataFrame, quintile_ts: pl.DataFrame) -> None:
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    n_show = 15
    bottom = tract_summary.sort("weighted_otp").head(n_show)
    top = tract_summary.sort("weighted_otp", descending=True).head(n_show).sort("weighted_otp")
    combined = pl.concat([bottom, top])

    labels = combined["label"].to_list()
    values = combined["weighted_otp"].to_list()
    median = combined["weighted_otp"].median()
    colors = ["#ef4444" if v < median else "#22c55e" for v in values]

    y_pos = range(len(labels))
    ax1.barh(y_pos, values, color=colors)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=7)
    ax1.set_xlabel("Trip-weighted average OTP")
    ax1.set_title(f"Bottom {n_show} & Top {n_show} census tracts by OTP "
                  f"(min {MIN_ROUTES} routes)")
    ax1.set_xlim(0, 1)

    quintile_colors = {1: "#ef4444", 2: "#f59e0b", 3: "#9ca3af", 4: "#60a5fa", 5: "#22c55e"}
    quintile_labels = {1: "Q1 (worst)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (best)"}

    months_all = sorted(quintile_ts["month"].unique().to_list())
    tick_pos = [i for i, m in enumerate(months_all) if m.endswith("-01")]
    tick_lbl = [months_all[i][:4] for i in tick_pos]

    for q in [1, 2, 3, 4, 5]:
        q_data = quintile_ts.filter(pl.col("quintile") == q).sort("month")
        months = q_data["month"].to_list()
        vals = q_data["avg_otp"].to_list()
        x = [months_all.index(m) for m in months]
        lw = 1.8 if q in (1, 5) else 0.8
        alpha = 1.0 if q in (1, 5) else 0.5
        ax2.plot(x, vals, color=quintile_colors[q], linewidth=lw, alpha=alpha,
                 label=quintile_labels[q])

    q1_data = quintile_ts.filter(pl.col("quintile") == 1).sort("month")
    q5_data = quintile_ts.filter(pl.col("quintile") == 5).sort("month")
    shared = q1_data.select("month").join(q5_data.select("month"), on="month")
    shared_months = shared["month"].to_list()
    q1_vals = q1_data.filter(pl.col("month").is_in(shared_months)).sort("month")["avg_otp"].to_list()
    q5_vals = q5_data.filter(pl.col("month").is_in(shared_months)).sort("month")["avg_otp"].to_list()
    shared_x = [months_all.index(m) for m in shared_months]
    ax2.fill_between(shared_x, q1_vals, q5_vals, alpha=0.1, color="#7c3aed")

    ax2.set_ylabel("Average OTP")
    ax2.set_title("OTP by tract quintile over time")
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_lbl)
    ax2.set_xlabel("Month")
    ax2.legend(fontsize=8, loc="lower left")
    ax2.set_ylim(0, 1)

    save_chart(fig, OUT / "tract_equity.png")


def make_comparison_chart(tract_summary: pl.DataFrame) -> None:
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    weighted = tract_summary["weighted_otp"].to_list()
    unweighted = tract_summary["unweighted_otp"].to_list()
    trips = tract_summary["total_trips_7d"].to_list()

    max_trips = max(trips)
    sizes = [20 + 80 * (t / max_trips) for t in trips]
    ax1.scatter(unweighted, weighted, s=sizes, alpha=0.5, c="#6366f1",
                edgecolors="white", linewidths=0.3)
    ax1.plot([0, 1], [0, 1], color="#9ca3af", linestyle="--", linewidth=1, zorder=0)
    ax1.set_xlabel("Unweighted OTP (equal weight per route)")
    ax1.set_ylabel("Weighted OTP (weighted by trip frequency)")
    ax1.set_title("Weighted vs unweighted OTP by tract")
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_aspect("equal")

    sorted_by_gap = tract_summary.with_columns(abs_gap=pl.col("otp_gap").abs()).sort(
        "abs_gap", descending=True
    )
    for row in sorted_by_gap.head(5).iter_rows(named=True):
        ax1.annotate(
            row["label"], (row["unweighted_otp"], row["weighted_otp"]),
            fontsize=6, alpha=0.8,
            xytext=(4, 4), textcoords="offset points",
        )

    n_show = 15
    biggest_positive = tract_summary.sort("otp_gap", descending=True).head(n_show)
    biggest_negative = tract_summary.sort("otp_gap").head(n_show)
    combined = pl.concat([biggest_negative, biggest_positive.sort("otp_gap")])
    gap_labels = combined["label"].to_list()
    gap_vals = combined["otp_gap"].to_list()
    gap_colors = ["#ef4444" if g < 0 else "#22c55e" for g in gap_vals]
    y_pos = range(len(gap_labels))
    ax2.barh(y_pos, gap_vals, color=gap_colors)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(gap_labels, fontsize=6)
    ax2.set_xlabel("OTP gap (weighted - unweighted)")
    ax2.set_title("Frequency-weighting effect by tract")
    ax2.axvline(0, color="#9ca3af", linewidth=0.8)

    save_chart(fig, OUT / "weighted_vs_unweighted_otp.png")


def make_income_chart(tract_summary: pl.DataFrame, gradient_df: pl.DataFrame) -> None:
    """Scatter of tract OTP vs median household income, plus per-quintile means."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    df = tract_summary.filter(pl.col("median_household_income").is_not_null())
    incomes = df["median_household_income"].to_list()
    otps = df["weighted_otp"].to_list()
    trips = df["total_trips_7d"].to_list()
    max_trips = max(trips)
    sizes = [10 + 80 * (t / max_trips) for t in trips]
    ax1.scatter(incomes, otps, s=sizes, alpha=0.4, c="#6366f1",
                edgecolors="white", linewidths=0.3)
    ax1.set_xlabel("Median household income (tract, 2018-2022 ACS, $)")
    ax1.set_ylabel("Trip-weighted OTP")
    ax1.set_title("Tract OTP vs median household income")
    ax1.set_ylim(0.4, 1.0)
    ax1.xaxis.set_major_formatter(lambda x, _: f"${int(x/1000)}k")

    if len(gradient_df) > 0:
        quintiles = gradient_df["income_quintile"].to_list()
        bar_otp = gradient_df["trip_weighted_otp"].to_list()
        ax2.bar(quintiles, bar_otp, color="#3b82f6", edgecolor="white")
        ax2.set_xlabel("Tract income quintile (1 = lowest income)")
        ax2.set_ylabel("Trip-weighted OTP")
        ax2.set_title("OTP by tract income quintile")
        ax2.set_ylim(0.5, 0.85)
        for q, v in zip(quintiles, bar_otp):
            ax2.text(q, v + 0.005, f"{v:.1%}", ha="center", fontsize=10)

    save_chart(fig, OUT / "otp_by_income.png")


@run_analysis(4, "Tract Equity")
def main() -> None:
    with phase("Loading route-level OTP and stops"):
        route_otp_df = load_route_otp()
        route_stops_df = load_route_stops()
        stop_muni_df = load_stop_muni()
        print(f"  {len(route_otp_df)} routes with >= {MIN_MONTHS} months of OTP")
        print(f"  {len(route_stops_df):,} route-stop edges with non-null trips_7d")

    with phase("Assigning stops to census tracts"):
        stop_tract_df = assign_stops_to_tracts()
        print(f"  {len(stop_tract_df):,} stops mapped to "
              f"{stop_tract_df['geoid'].n_unique()} tracts "
              f"({stop_tract_df['geoid'].is_null().sum()} unmapped)")

    with phase("Building per-tract analysis"):
        rst_df = build_route_stop_tract(route_otp_df, route_stops_df, stop_tract_df)
        muni_df = primary_muni_per_tract(stop_tract_df, stop_muni_df)
        tract_demo_df = stop_tract_df.unique("geoid").select(
            "geoid", "population", "median_household_income",
            "households_total", "households_zero_vehicle",
            "pop_white_nh", "pop_black_nh", "pop_asian_nh", "pop_hispanic",
        )
        tract_summary = analyze(rst_df, muni_df, tract_demo_df)
        print(f"  {len(tract_summary)} tracts with >= {MIN_ROUTES} routes ranked")

        best = tract_summary.sort("weighted_otp", descending=True).head(3)
        worst = tract_summary.sort("weighted_otp").head(3)
        print("\n  Top 3 tracts (weighted):")
        for row in best.iter_rows(named=True):
            print(f"    {row['label']}: {row['weighted_otp']:.1%}")
        print("  Bottom 3 tracts (weighted):")
        for row in worst.iter_rows(named=True):
            print(f"    {row['label']}: {row['weighted_otp']:.1%}")

        spread = tract_summary["weighted_otp"].max() - tract_summary["weighted_otp"].min()
        print(f"\n  Spread (max - min): {spread:.1%}")

    with phase("Bus-only stratification"):
        route_modes_df = load_route_modes()
        bus_summary = analyze_bus_only(rst_df, route_modes_df)
        tract_summary = tract_summary.join(bus_summary, on="geoid", how="left")
        bus_count = tract_summary.filter(pl.col("bus_weighted_otp").is_not_null()).height
        print(f"  {bus_count} tracts with bus-mode service")

    with phase("Income-gradient analysis"):
        gradient_df = analyze_income_gradient(tract_summary)
        if len(gradient_df) > 0:
            for row in gradient_df.iter_rows(named=True):
                print(f"    Q{row['income_quintile']} (mean ${row['mean_income']:,.0f}, "
                      f"n={row['n_tracts']}): trip-weighted OTP {row['trip_weighted_otp']:.1%}")
            q1 = gradient_df.filter(pl.col("income_quintile") == 1)["trip_weighted_otp"][0]
            q5 = gradient_df.filter(pl.col("income_quintile") == 5)["trip_weighted_otp"][0]
            print(f"  Q5 - Q1 OTP gap: {(q5 - q1) * 100:+.2f} pp")

    with phase("Quintile time series"):
        monthly_df = load_monthly_route()
        quintile_ts = analyze_quintile_ts(monthly_df, route_stops_df, stop_tract_df)

    with phase("Saving CSVs"):
        save_csv(tract_summary, OUT / "tract_otp.csv")
        save_csv(bus_summary, OUT / "tract_otp_bus_only.csv")
        if len(gradient_df) > 0:
            save_csv(gradient_df, OUT / "otp_by_income_quintile.csv")

    with phase("Generating charts"):
        make_chart(tract_summary, quintile_ts)
        make_comparison_chart(tract_summary)
        make_income_chart(tract_summary, gradient_df)


if __name__ == "__main__":
    main()
