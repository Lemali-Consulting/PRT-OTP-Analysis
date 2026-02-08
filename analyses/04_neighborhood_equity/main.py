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
    """Compute per-neighborhood OTP and per-quintile time series."""
    # Per-neighborhood overall weighted OTP
    hood_summary = (
        df.group_by(["hood", "muni", "county"])
        .agg(
            mean_otp=(pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum(),
            route_count=pl.col("route_id").n_unique(),
            stop_count=pl.col("stop_id").n_unique(),
            total_trips_7d=pl.col("trips_7d").sum(),
        )
        .sort("mean_otp")
    )

    # Quintile assignment based on overall OTP
    hood_ranks = hood_summary.with_columns(
        quintile=((pl.col("mean_otp").rank() - 1) / pl.len() * 5).cast(pl.Int32).clip(0, 4) + 1,
    ).select("hood", "quintile")

    # Per-neighborhood-month weighted OTP, then aggregate by quintile
    hood_month = (
        df.group_by(["hood", "month"])
        .agg(
            weighted_otp=(pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum(),
        )
    )

    hood_month_q = hood_month.join(hood_ranks, on="hood")
    quintile_ts = (
        hood_month_q.group_by(["quintile", "month"])
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
    bottom = hood_summary.sort("mean_otp").head(n_show)
    top = hood_summary.sort("mean_otp", descending=True).head(n_show).sort("mean_otp")
    combined = pl.concat([bottom, top])

    labels = combined["hood"].to_list()
    values = combined["mean_otp"].to_list()
    colors = ["#ef4444" if v < combined["mean_otp"].median() else "#22c55e" for v in values]

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

    best = hood_summary.sort("mean_otp", descending=True).head(3)
    worst = hood_summary.sort("mean_otp").head(3)
    print("\n  Top 3 neighborhoods:")
    for row in best.iter_rows(named=True):
        print(f"    {row['hood']} ({row['muni']}): {row['mean_otp']:.1%}")
    print("  Bottom 3 neighborhoods:")
    for row in worst.iter_rows(named=True):
        print(f"    {row['hood']} ({row['muni']}): {row['mean_otp']:.1%}")

    print("\nSaving CSV...")
    hood_summary.write_csv(OUT / "neighborhood_otp.csv")
    print(f"  Saved to {OUT / 'neighborhood_otp.csv'}")

    print("\nGenerating chart...")
    make_chart(hood_summary, quintile_ts)

    print("\nDone.")


if __name__ == "__main__":
    main()
