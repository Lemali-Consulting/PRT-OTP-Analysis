"""Neighborhood equity analysis: OTP aggregated by geography."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load OTP joined with route-stop-neighborhood data."""
    return query_to_polars("""
        SELECT rs.route_id, rs.stop_id, rs.trips_7d,
               s.hood, s.muni, s.county,
               o.month, o.otp
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        JOIN otp_monthly o ON rs.route_id = o.route_id
        WHERE s.hood IS NOT NULL
          AND s.hood != '0'
          AND s.hood != ''
    """)


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Compute per-neighborhood OTP and rolling-quintile time series."""
    # Per-neighborhood overall weighted OTP (for bar chart)
    hood_summary = (
        df.group_by(["hood", "muni", "county"])
        .agg(
            weighted_otp=(pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum(),
            route_count=pl.col("route_id").n_unique(),
            stop_count=pl.col("stop_id").n_unique(),
            total_trips_7d=pl.col("trips_7d").sum(),
        )
        .sort("weighted_otp")
    )

    # Unweighted OTP: deduplicate by (hood, route_id, month) since a route's
    # OTP is the same across all stops, then simple-average across routes.
    hood_unweighted = (
        df.group_by(["hood", "route_id", "month"])
        .agg(otp=pl.col("otp").first())
        .group_by("hood")
        .agg(unweighted_otp=pl.col("otp").mean())
    )

    hood_summary = hood_summary.join(hood_unweighted, on="hood", how="left")
    hood_summary = hood_summary.with_columns(
        otp_gap=(pl.col("weighted_otp") - pl.col("unweighted_otp")),
    ).sort("weighted_otp")

    # Per-neighborhood-month weighted OTP
    hood_month = (
        df.group_by(["hood", "month"])
        .agg(
            weighted_otp=(pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum(),
        )
    )

    # Rolling 12-month OTP per neighborhood for quintile assignment
    hood_month = hood_month.sort(["hood", "month"])
    hood_month = hood_month.with_columns(
        rolling_otp=pl.col("weighted_otp")
        .rolling_mean(window_size=12, min_samples=6)
        .over("hood"),
    )

    # Assign quintiles per month based on trailing performance (avoids look-ahead bias)
    hood_month_ranked = hood_month.filter(pl.col("rolling_otp").is_not_null())
    hood_month_ranked = hood_month_ranked.with_columns(
        quintile=(
            ((pl.col("rolling_otp").rank().over("month") - 1)
             / pl.col("rolling_otp").count().over("month") * 5)
            .cast(pl.Int32).clip(0, 4) + 1
        ),
    )

    quintile_ts = (
        hood_month_ranked.group_by(["quintile", "month"])
        .agg(avg_otp=pl.col("weighted_otp").mean())
        .sort(["quintile", "month"])
    )

    return hood_summary, quintile_ts


def make_chart(hood_summary: pl.DataFrame, quintile_ts: pl.DataFrame) -> None:
    """Generate neighborhood equity charts."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Top: Best and worst 15 neighborhoods
    n_show = 15
    bottom = hood_summary.sort("weighted_otp").head(n_show)
    top = hood_summary.sort("weighted_otp", descending=True).head(n_show).sort("weighted_otp")
    combined = pl.concat([bottom, top])

    labels = combined["hood"].to_list()
    values = combined["weighted_otp"].to_list()
    colors = ["#ef4444" if v < combined["weighted_otp"].median() else "#22c55e" for v in values]

    y_pos = range(len(labels))
    ax1.barh(y_pos, values, color=colors)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=7)
    ax1.set_xlabel("Weighted Average OTP")
    ax1.set_title(f"Bottom {n_show} & Top {n_show} Neighborhoods by OTP")
    ax1.set_xlim(0, 1)

    # Bottom: All quintile time series (shows spread, not just the gap)
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

    # Shade between Q1 and Q5
    q1_data = quintile_ts.filter(pl.col("quintile") == 1).sort("month")
    q5_data = quintile_ts.filter(pl.col("quintile") == 5).sort("month")
    shared = q1_data.select("month").join(q5_data.select("month"), on="month")
    shared_months = shared["month"].to_list()
    q1_vals = q1_data.filter(pl.col("month").is_in(shared_months)).sort("month")["avg_otp"].to_list()
    q5_vals = q5_data.filter(pl.col("month").is_in(shared_months)).sort("month")["avg_otp"].to_list()
    shared_x = [months_all.index(m) for m in shared_months]
    ax2.fill_between(shared_x, q1_vals, q5_vals, alpha=0.1, color="#7c3aed")

    ax2.set_ylabel("Average OTP")
    ax2.set_title("OTP by Neighborhood Quintile Over Time")
    ax2.set_xticks(tick_pos)
    ax2.set_xticklabels(tick_lbl)
    ax2.set_xlabel("Month")
    ax2.legend(fontsize=8, loc="lower left")
    ax2.set_ylim(0, 1)

    fig.tight_layout()
    fig.savefig(OUT / "neighborhood_equity.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'neighborhood_equity.png'}")


def make_comparison_chart(hood_summary: pl.DataFrame) -> None:
    """Generate weighted vs unweighted OTP comparison chart."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    weighted = hood_summary["weighted_otp"].to_list()
    unweighted = hood_summary["unweighted_otp"].to_list()
    trips = hood_summary["total_trips_7d"].to_list()

    # Left: scatter of weighted vs unweighted, sized by total trips
    max_trips = max(trips)
    sizes = [20 + 80 * (t / max_trips) for t in trips]
    ax1.scatter(unweighted, weighted, s=sizes, alpha=0.5, c="#6366f1", edgecolors="white", linewidths=0.3)

    # Diagonal reference line
    ax1.plot([0, 1], [0, 1], color="#9ca3af", linestyle="--", linewidth=1, zorder=0)
    ax1.set_xlabel("Unweighted OTP (equal weight per route)")
    ax1.set_ylabel("Weighted OTP (weighted by trip frequency)")
    ax1.set_title("Weighted vs Unweighted OTP by Neighborhood")
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_aspect("equal")

    # Annotate the 5 neighborhoods with largest absolute gap
    sorted_by_gap = hood_summary.with_columns(abs_gap=pl.col("otp_gap").abs()).sort("abs_gap", descending=True)
    for row in sorted_by_gap.head(5).iter_rows(named=True):
        ax1.annotate(
            row["hood"], (row["unweighted_otp"], row["weighted_otp"]),
            fontsize=6, alpha=0.8,
            xytext=(4, 4), textcoords="offset points",
        )

    # Right: top/bottom 15 neighborhoods by gap (weighted - unweighted)
    n_show = 15
    biggest_positive = hood_summary.sort("otp_gap", descending=True).head(n_show)
    biggest_negative = hood_summary.sort("otp_gap").head(n_show)
    combined = pl.concat([biggest_negative, biggest_positive.sort("otp_gap")])

    gap_labels = combined["hood"].to_list()
    gap_vals = combined["otp_gap"].to_list()
    gap_colors = ["#ef4444" if g < 0 else "#22c55e" for g in gap_vals]

    y_pos = range(len(gap_labels))
    ax2.barh(y_pos, gap_vals, color=gap_colors)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(gap_labels, fontsize=6)
    ax2.set_xlabel("OTP Gap (weighted - unweighted)")
    ax2.set_title("Frequency Weighting Effect by Neighborhood")
    ax2.axvline(0, color="#9ca3af", linewidth=0.8)

    fig.tight_layout()
    fig.savefig(OUT / "weighted_vs_unweighted_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'weighted_vs_unweighted_otp.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 04: Neighborhood Equity")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} route-stop-month records loaded")
    print(f"  {df['hood'].n_unique()} neighborhoods represented")

    # Check how many stops lack neighborhood data
    total_stops = query_to_polars("SELECT COUNT(*) AS n FROM stops")["n"][0]
    hood_stops = query_to_polars(
        "SELECT COUNT(*) AS n FROM stops WHERE hood IS NOT NULL AND hood != '0' AND hood != ''"
    )["n"][0]
    print(f"  {total_stops - hood_stops} of {total_stops} stops excluded (missing/invalid neighborhood)")

    print("\nAnalyzing...")
    hood_summary, quintile_ts = analyze(df)
    print(f"  {len(hood_summary)} neighborhoods ranked")

    best = hood_summary.sort("weighted_otp", descending=True).head(3)
    worst = hood_summary.sort("weighted_otp").head(3)
    print("\n  Top 3 neighborhoods (weighted):")
    for row in best.iter_rows(named=True):
        print(f"    {row['hood']} ({row['muni']}): {row['weighted_otp']:.1%}")
    print("  Bottom 3 neighborhoods (weighted):")
    for row in worst.iter_rows(named=True):
        print(f"    {row['hood']} ({row['muni']}): {row['weighted_otp']:.1%}")

    # Frequency-weighting effect summary
    gaps = hood_summary["otp_gap"]
    print(f"\n  Frequency-weighting effect (weighted - unweighted):")
    print(f"    Mean gap:   {gaps.mean():+.2%}")
    print(f"    Median gap: {gaps.median():+.2%}")
    print(f"    Range:      {gaps.min():+.2%} to {gaps.max():+.2%}")
    biggest = hood_summary.with_columns(abs_gap=pl.col("otp_gap").abs()).sort("abs_gap", descending=True).head(3)
    print("  Largest divergences:")
    for row in biggest.iter_rows(named=True):
        print(f"    {row['hood']}: weighted={row['weighted_otp']:.1%}, "
              f"unweighted={row['unweighted_otp']:.1%}, gap={row['otp_gap']:+.2%}")

    print("\nSaving CSV...")
    hood_summary.write_csv(OUT / "neighborhood_otp.csv")
    print(f"  Saved to {OUT / 'neighborhood_otp.csv'}")

    print("\nGenerating charts...")
    make_chart(hood_summary, quintile_ts)
    make_comparison_chart(hood_summary)

    print("\nDone.")


if __name__ == "__main__":
    main()
