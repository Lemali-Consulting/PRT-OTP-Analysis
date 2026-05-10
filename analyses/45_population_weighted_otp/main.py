"""Analysis 45: Population-Weighted System OTP.

Compute the OTP experienced by the average resident by weighting each route's
monthly OTP by its walkshed population (Analysis 44 construction), then compare
to trip-weighted (Analysis 19) and unweighted system OTP.
"""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    output_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
    weighted_mean,
)
from prt_otp_analysis.walksheds import route_population_served

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12


def load_otp_with_weights() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return (long OTP+weights df, per-route weights df).

    Long df has one row per (route, month) with otp, population_served, trips_7d.
    Restricted to routes with >= MIN_MONTHS of OTP observations.
    """
    pop_df = route_population_served()
    trips_df = query_to_polars(
        "SELECT route_id, SUM(trips_7d) AS trips_7d FROM route_stops GROUP BY route_id"
    )
    otp_df = query_to_polars(
        "SELECT route_id, month, otp FROM otp_monthly WHERE otp IS NOT NULL"
    )

    weights_df = (
        pop_df.join(trips_df, on="route_id", how="left")
        .with_columns(trips_7d=pl.col("trips_7d").fill_null(0))
    )

    df = otp_df.join(weights_df, on="route_id", how="inner")

    route_counts = df.group_by("route_id").agg(pl.col("month").count().alias("n"))
    keep = route_counts.filter(pl.col("n") >= MIN_MONTHS)["route_id"].to_list()
    df = df.filter(pl.col("route_id").is_in(keep))
    weights_df = weights_df.filter(pl.col("route_id").is_in(keep))
    return df, weights_df


def compute_monthly(df: pl.DataFrame) -> pl.DataFrame:
    """Three monthly OTP series: unweighted, trip-weighted, population-weighted."""
    return (
        df.group_by("month")
        .agg(
            unweighted_otp=pl.col("otp").mean(),
            trip_weighted_otp=weighted_mean("otp", "trips_7d", safe=True),
            population_weighted_otp=weighted_mean("otp", "population_served", safe=True),
            route_count=pl.col("route_id").n_unique(),
            total_population_served=pl.col("population_served").sum(),
        )
        .sort("month")
    )


def compute_summary(monthly: pl.DataFrame) -> pl.DataFrame:
    """Summary statistics for each weighting scheme."""
    rows = []
    for col in ["unweighted_otp", "trip_weighted_otp", "population_weighted_otp"]:
        s = monthly[col]
        rows.append({
            "weighting": col.replace("_otp", ""),
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(),
            "min": s.min(),
            "max": s.max(),
        })
    return pl.DataFrame(rows)


def statistical_test(monthly: pl.DataFrame) -> dict:
    """Test whether population-weighted OTP differs from trip-weighted OTP."""
    trip = monthly["trip_weighted_otp"].to_numpy()
    pop = monthly["population_weighted_otp"].to_numpy()
    t_stat, t_p = stats.ttest_rel(trip, pop)
    w_stat, w_p = stats.wilcoxon(trip, pop)
    return {
        "mean_difference": float((pop - trip).mean()),
        "paired_t_stat": float(t_stat),
        "paired_t_p": float(t_p),
        "wilcoxon_stat": float(w_stat),
        "wilcoxon_p": float(w_p),
        "n_months": int(len(trip)),
    }


def make_chart(monthly: pl.DataFrame) -> None:
    """Plot three OTP series over time."""
    plt = setup_plotting()

    months = monthly["month"].to_list()
    x = list(range(len(months)))
    tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
    tick_labels = [months[i][:4] for i in tick_positions]

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(x, monthly["unweighted_otp"].to_list(),
            color="#9ca3af", linewidth=1, linestyle="--",
            label="Unweighted (all routes equal)")
    ax.plot(x, monthly["trip_weighted_otp"].to_list(),
            color="#2563eb", linewidth=1.5,
            label="Trip-weighted (scheduled frequency)")
    ax.plot(x, monthly["population_weighted_otp"].to_list(),
            color="#059669", linewidth=1.5,
            label="Population-weighted (walkshed residents)")

    trip = monthly["trip_weighted_otp"].to_list()
    pop = monthly["population_weighted_otp"].to_list()
    ax.fill_between(x, trip, pop, alpha=0.15, color="#059669",
                    label="Trip vs population gap")

    if "2020-03" in months:
        covid_idx = months.index("2020-03")
        ax.axvline(covid_idx, color="#ef4444", linestyle=":", alpha=0.7)
        ax.text(covid_idx + 0.5, ax.get_ylim()[1] * 0.98, "COVID",
                color="#ef4444", fontsize=8, va="top")

    ax.set_ylabel("On-Time Performance")
    ax.set_xlabel("Month")
    ax.set_title("PRT System OTP: Population vs Trips vs Unweighted")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(0.5, 0.85)

    save_chart(fig, OUT / "population_weighted_otp_trend.png")


@run_analysis(45, "Population-Weighted System OTP")
def main() -> None:
    with phase("Loading OTP and route weights"):
        df, weights_df = load_otp_with_weights()
        n_routes = df["route_id"].n_unique()
        print(f"  {len(df):,} route-month observations ({n_routes} routes "
              f">= {MIN_MONTHS} months OTP)")
        print(f"  population_served sum across cohort: "
              f"{weights_df['population_served'].sum():,}")

    with phase("Computing monthly OTP series"):
        monthly = compute_monthly(df)
        print(f"  {len(monthly)} months computed")

    with phase("Summary statistics"):
        summary = compute_summary(monthly)
        for row in summary.iter_rows(named=True):
            print(f"  {row['weighting']:25s}  mean={row['mean']:.3%}  "
                  f"median={row['median']:.3%}  std={row['std']:.3%}")

    with phase("Statistical test (population-weighted vs trip-weighted)"):
        test = statistical_test(monthly)
        print(f"  Mean difference: {test['mean_difference']:+.4%}")
        print(f"  Paired t-test:   t={test['paired_t_stat']:.3f}, p={test['paired_t_p']:.4f}")
        print(f"  Wilcoxon test:   W={test['wilcoxon_stat']:.0f}, p={test['wilcoxon_p']:.4f}")
        print(f"  N months:        {test['n_months']}")

    with phase("Saving CSVs"):
        save_csv(monthly, OUT / "weighting_comparison.csv")
        save_csv(summary, OUT / "summary_stats.csv")
        save_csv(
            weights_df.sort("population_served", descending=True),
            OUT / "route_weights.csv",
        )

    with phase("Generating chart"):
        make_chart(monthly)


if __name__ == "__main__":
    main()
