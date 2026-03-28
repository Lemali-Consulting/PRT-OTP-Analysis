"""Analysis 19: Compare system OTP under three weighting schemes -- unweighted, trip-weighted, and ridership-weighted."""

import polars as pl
from scipy import stats

from prt_otp_analysis.common import analysis_dir, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting, weighted_mean

OUT = analysis_dir(__file__)

MIN_MONTHS = 12


def load_data() -> pl.DataFrame:
    """Load OTP joined with weekday ridership and trip weights, restricted to the overlap period."""
    df = query_to_polars("""
        SELECT o.route_id, o.month, o.otp,
               r.avg_riders,
               COALESCE(rs.trips_7d, 0) AS trips_7d
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        LEFT JOIN (
            SELECT route_id, SUM(trips_7d) AS trips_7d
            FROM route_stops
            GROUP BY route_id
        ) rs ON o.route_id = rs.route_id
    """)

    # Filter to routes with at least MIN_MONTHS of paired data
    route_counts = df.group_by("route_id").agg(pl.col("month").count().alias("n"))
    keep = route_counts.filter(pl.col("n") >= MIN_MONTHS)["route_id"].to_list()
    df = df.filter(pl.col("route_id").is_in(keep))

    return df


def compute_monthly(df: pl.DataFrame) -> pl.DataFrame:
    """Compute three monthly OTP series: unweighted, trip-weighted, ridership-weighted."""
    monthly = (
        df.group_by("month")
        .agg(
            unweighted_otp=pl.col("otp").mean(),
            trip_weighted_otp=weighted_mean("otp", "trips_7d", safe=True),
            ridership_weighted_otp=weighted_mean("otp", "avg_riders"),
            route_count=pl.col("route_id").n_unique(),
            total_riders=pl.col("avg_riders").sum(),
        )
        .sort("month")
    )
    return monthly


def compute_summary(monthly: pl.DataFrame) -> pl.DataFrame:
    """Compute summary statistics for each weighting scheme."""
    rows = []
    for col in ["unweighted_otp", "trip_weighted_otp", "ridership_weighted_otp"]:
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
    """Test whether ridership-weighted OTP differs from trip-weighted OTP."""
    trip = monthly["trip_weighted_otp"].to_numpy()
    rider = monthly["ridership_weighted_otp"].to_numpy()

    # Paired t-test
    t_stat, t_p = stats.ttest_rel(trip, rider)

    # Wilcoxon signed-rank (non-parametric)
    w_stat, w_p = stats.wilcoxon(trip, rider)

    mean_diff = (rider - trip).mean()

    return {
        "mean_difference": mean_diff,
        "paired_t_stat": t_stat,
        "paired_t_p": t_p,
        "wilcoxon_stat": w_stat,
        "wilcoxon_p": w_p,
        "n_months": len(trip),
    }


def make_chart(monthly: pl.DataFrame) -> None:
    """Plot three OTP series over time."""
    plt = setup_plotting()

    months = monthly["month"].to_list()
    x = range(len(months))
    tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
    tick_labels = [months[i][:4] for i in tick_positions]

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(x, monthly["unweighted_otp"].to_list(),
            color="#9ca3af", linewidth=1, linestyle="--", label="Unweighted (all routes equal)")
    ax.plot(x, monthly["trip_weighted_otp"].to_list(),
            color="#2563eb", linewidth=1.5, label="Trip-weighted (scheduled frequency)")
    ax.plot(x, monthly["ridership_weighted_otp"].to_list(),
            color="#e11d48", linewidth=1.5, label="Ridership-weighted (avg daily riders)")

    # Shade gap between trip-weighted and ridership-weighted
    trip = monthly["trip_weighted_otp"].to_list()
    rider = monthly["ridership_weighted_otp"].to_list()
    ax.fill_between(x, trip, rider, alpha=0.15, color="#e11d48", label="Trip vs ridership gap")

    # COVID marker
    if "2020-03" in months:
        covid_idx = months.index("2020-03")
        ax.axvline(covid_idx, color="#ef4444", linestyle=":", alpha=0.7)
        ax.text(covid_idx + 0.5, ax.get_ylim()[1] * 0.98, "COVID",
                color="#ef4444", fontsize=8, va="top")

    ax.set_ylabel("On-Time Performance")
    ax.set_xlabel("Month")
    ax.set_title("PRT System OTP: Three Weighting Schemes (2019\u20132024)")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)
    ax.legend(loc="lower left", fontsize=8)
    ax.set_ylim(0.5, 0.85)

    save_chart(fig, OUT / "ridership_weighted_otp_trend.png")


@run_analysis(19, "Ridership-Weighted OTP")
def main() -> None:
    """Entry point: load data, compute weighted OTP series, test, chart, and save."""
    print("\nLoading data...")
    df = load_data()
    n_routes = df["route_id"].n_unique()
    print(f"  {len(df):,} route-month observations ({n_routes} routes)")

    print("\nComputing monthly OTP series...")
    monthly = compute_monthly(df)
    print(f"  {len(monthly)} months computed")

    print("\nSummary statistics:")
    summary = compute_summary(monthly)
    for row in summary.iter_rows(named=True):
        print(f"  {row['weighting']:30s}  mean={row['mean']:.3%}  "
              f"median={row['median']:.3%}  std={row['std']:.3%}")

    print("\nStatistical test (ridership-weighted vs trip-weighted):")
    test = statistical_test(monthly)
    print(f"  Mean difference: {test['mean_difference']:+.4%}")
    print(f"  Paired t-test:   t={test['paired_t_stat']:.3f}, p={test['paired_t_p']:.4f}")
    print(f"  Wilcoxon test:   W={test['wilcoxon_stat']:.0f}, p={test['wilcoxon_p']:.4f}")
    print(f"  N months:        {test['n_months']}")

    print("\nSaving CSVs...")
    save_csv(monthly, OUT / "weighting_comparison.csv")
    save_csv(summary, OUT / "summary_stats.csv")

    print("\nGenerating chart...")
    make_chart(monthly)


if __name__ == "__main__":
    main()
