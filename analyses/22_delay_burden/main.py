"""Analysis 22: Estimate late rider-trips per route per month to identify where the most total human impact occurs."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load paired OTP and weekday ridership with day counts."""
    df = query_to_polars("""
        SELECT o.route_id, rt.route_name, o.month, o.otp,
               r.avg_riders, r.day_count
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        JOIN routes rt ON o.route_id = rt.route_id
    """)

    # Compute late rider-trips: riders * weekdays * (1 - OTP)
    df = df.with_columns(
        late_rider_trips=(pl.col("avg_riders") * pl.col("day_count") * (1.0 - pl.col("otp"))),
        total_rider_trips=(pl.col("avg_riders") * pl.col("day_count")),
    )

    return df


def route_ranking(df: pl.DataFrame) -> pl.DataFrame:
    """Rank routes by cumulative and average monthly late rider-trips."""
    ranking = (
        df.group_by("route_id", "route_name")
        .agg(
            total_late=pl.col("late_rider_trips").sum(),
            avg_monthly_late=pl.col("late_rider_trips").mean(),
            total_trips=pl.col("total_rider_trips").sum(),
            avg_otp=pl.col("otp").mean(),
            avg_riders=pl.col("avg_riders").mean(),
            n_months=pl.col("month").count(),
        )
        .with_columns(
            effective_otp=(1.0 - pl.col("total_late") / pl.col("total_trips")),
        )
        .sort("total_late", descending=True)
    )

    # Add ranks
    ranking = ranking.with_row_index("burden_rank", offset=1)
    otp_rank = (
        ranking.sort("avg_otp")
        .with_row_index("otp_rank", offset=1)
        .select("route_id", "otp_rank")
    )
    ranking = ranking.join(otp_rank, on="route_id")

    return ranking


def monthly_system(df: pl.DataFrame) -> pl.DataFrame:
    """Compute system-wide monthly late rider-trips."""
    return (
        df.group_by("month")
        .agg(
            system_late=pl.col("late_rider_trips").sum(),
            system_total=pl.col("total_rider_trips").sum(),
            system_otp=(
                (pl.col("otp") * pl.col("avg_riders")).sum() / pl.col("avg_riders").sum()
            ),
            route_count=pl.col("route_id").n_unique(),
        )
        .sort("month")
    )


def make_trend_chart(monthly: pl.DataFrame) -> None:
    """System-wide monthly late rider-trips trend."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(14, 6))

    months = monthly["month"].to_list()
    late = [v / 1000 for v in monthly["system_late"].to_list()]  # thousands
    x = range(len(months))
    tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
    tick_labels = [months[i][:4] for i in tick_positions]

    ax.fill_between(x, late, alpha=0.3, color="#e11d48")
    ax.plot(x, late, color="#e11d48", linewidth=1.5)

    if "2020-03" in months:
        covid_idx = months.index("2020-03")
        ax.axvline(covid_idx, color="#ef4444", linestyle=":", alpha=0.7)
        ax.text(covid_idx + 0.5, max(late) * 0.95, "COVID",
                color="#ef4444", fontsize=8, va="top")

    ax.set_ylabel("Late Rider-Trips (thousands)")
    ax.set_xlabel("Month")
    ax.set_title("System-Wide Monthly Delay Burden (Weekday Late Rider-Trips)")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels)

    fig.tight_layout()
    fig.savefig(OUT / "delay_burden_trend.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'delay_burden_trend.png'}")


def make_top10_chart(ranking: pl.DataFrame) -> None:
    """Horizontal bar chart of top 10 routes by cumulative late rider-trips."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 6))

    top10 = ranking.head(10).sort("total_late")
    labels = [f"{r['route_id']} - {r['route_name']}" for r in top10.iter_rows(named=True)]
    values = [v / 1_000_000 for v in top10["total_late"].to_list()]  # millions
    otp_vals = top10["avg_otp"].to_list()

    colors = ["#e11d48" if o < 0.65 else "#f59e0b" if o < 0.70 else "#3b82f6" for o in otp_vals]
    bars = ax.barh(range(len(labels)), values, color=colors, edgecolor="white", alpha=0.8)

    # Annotate with OTP
    for i, (v, o) in enumerate(zip(values, otp_vals)):
        ax.text(v + max(values) * 0.01, i, f"OTP: {o:.0%}", va="center", fontsize=8)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("Cumulative Late Rider-Trips (millions, Jan 2019 - Oct 2024)")
    ax.set_title("Top 10 Routes by Delay Burden")

    fig.tight_layout()
    fig.savefig(OUT / "top10_burden.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'top10_burden.png'}")


def make_rate_vs_burden_chart(ranking: pl.DataFrame) -> None:
    """Scatter plot comparing OTP rank with delay burden rank."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(8, 8))

    n = len(ranking)
    ax.scatter(
        ranking["otp_rank"].to_list(),
        ranking["burden_rank"].to_list(),
        s=30, alpha=0.6, color="#3b82f6", edgecolors="white", linewidths=0.5,
    )

    # Diagonal (perfect agreement)
    ax.plot([1, n], [1, n], color="#9ca3af", linestyle="--", linewidth=1, label="Perfect agreement")

    # Label routes that shifted most
    ranking_with_diff = ranking.with_columns(
        rank_shift=(pl.col("otp_rank").cast(pl.Int64) - pl.col("burden_rank").cast(pl.Int64)).abs(),
    )
    outliers = ranking_with_diff.sort("rank_shift", descending=True).head(8)
    for row in outliers.iter_rows(named=True):
        ax.annotate(
            row["route_id"],
            (row["otp_rank"], row["burden_rank"]),
            fontsize=7, alpha=0.8,
            xytext=(5, 5), textcoords="offset points",
        )

    # Spearman rank correlation
    r_s, p_s = stats.spearmanr(ranking["otp_rank"].to_list(), ranking["burden_rank"].to_list())
    ax.text(0.05, 0.95, f"Spearman r = {r_s:.3f}\np = {p_s:.4f}",
            transform=ax.transAxes, fontsize=9, va="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    ax.set_xlabel("OTP Rank (1 = worst OTP)")
    ax.set_ylabel("Burden Rank (1 = most late rider-trips)")
    ax.set_title("Rate vs Burden: How Ridership Shifts Priorities")
    ax.invert_xaxis()
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(OUT / "rate_vs_burden.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'rate_vs_burden.png'}")


def main() -> None:
    """Entry point: load, compute burden, rank, chart, and save."""
    print("=" * 60)
    print("Analysis 22: Passenger-Weighted Delay Burden")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    n_routes = df["route_id"].n_unique()
    print(f"  {len(df):,} route-month observations ({n_routes} routes)")

    print("\nRanking routes by delay burden...")
    ranking = route_ranking(df)

    print("\n  Top 10 routes by cumulative late rider-trips:")
    print(f"  {'Rank':>4} {'Route':<8} {'Name':<32} {'Late trips':>12} {'Avg OTP':>8} {'OTP Rank':>9}")
    for row in ranking.head(10).iter_rows(named=True):
        print(f"  {row['burden_rank']:>4} {row['route_id']:<8} {row['route_name']:<32} "
              f"{row['total_late']:>12,.0f} {row['avg_otp']:>8.1%} {row['otp_rank']:>9}")

    # Routes that shift most between rankings
    ranking_annotated = ranking.with_columns(
        rank_shift=(pl.col("otp_rank").cast(pl.Int64) - pl.col("burden_rank").cast(pl.Int64)),
    )

    print("\n  Biggest rank shifts (burden rank - OTP rank):")
    print("  Positive = higher burden than OTP rank suggests (high-ridership route)")
    print("  Negative = lower burden than OTP rank suggests (low-ridership route)")
    shifted = ranking_annotated.sort("rank_shift", descending=True)
    print(f"\n  {'Route':<8} {'Name':<32} {'OTP Rank':>9} {'Burden Rank':>12} {'Shift':>6}")
    for row in shifted.head(5).iter_rows(named=True):
        print(f"  {row['route_id']:<8} {row['route_name']:<32} "
              f"{row['otp_rank']:>9} {row['burden_rank']:>12} {row['rank_shift']:>+6}")
    print("  ...")
    for row in shifted.tail(5).iter_rows(named=True):
        print(f"  {row['route_id']:<8} {row['route_name']:<32} "
              f"{row['otp_rank']:>9} {row['burden_rank']:>12} {row['rank_shift']:>+6}")

    print("\nComputing system-wide monthly trend...")
    monthly = monthly_system(df)
    total_late = monthly["system_late"].sum()
    total_trips = monthly["system_total"].sum()
    print(f"  Total late rider-trips (all time): {total_late:,.0f}")
    print(f"  Total rider-trips (all time):      {total_trips:,.0f}")
    print(f"  System late rate:                  {total_late / total_trips:.1%}")

    # Top 10 share of system burden
    top10_late = ranking.head(10)["total_late"].sum()
    print(f"\n  Top 10 routes account for {top10_late / total_late:.1%} of all late rider-trips")

    print("\nSaving CSVs...")
    ranking.write_csv(OUT / "delay_burden_ranking.csv")
    print(f"  {OUT / 'delay_burden_ranking.csv'}")
    monthly.write_csv(OUT / "delay_burden_monthly.csv")
    print(f"  {OUT / 'delay_burden_monthly.csv'}")

    print("\nGenerating charts...")
    make_trend_chart(monthly)
    make_top10_chart(ranking)
    make_rate_vs_burden_chart(ranking)

    print("\nDone.")


if __name__ == "__main__":
    main()
