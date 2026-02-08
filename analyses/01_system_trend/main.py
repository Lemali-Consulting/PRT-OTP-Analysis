"""System-wide OTP trend analysis: weighted and unweighted monthly averages."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def load_data() -> pl.DataFrame:
    """Load OTP data with per-route trip weights from the database."""
    return query_to_polars("""
        SELECT o.route_id, o.month, o.otp,
               COALESCE(rs_agg.trips_7d, 0) AS trips_7d
        FROM otp_monthly o
        LEFT JOIN (
            SELECT route_id, SUM(trips_7d) AS trips_7d
            FROM route_stops
            GROUP BY route_id
        ) rs_agg ON o.route_id = rs_agg.route_id
    """)


def analyze(df: pl.DataFrame) -> pl.DataFrame:
    """Compute weighted and unweighted monthly system OTP with year-over-year change."""
    monthly = (
        df.group_by("month")
        .agg(
            weighted_otp=pl.when(pl.col("trips_7d").sum() > 0)
            .then((pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum())
            .otherwise(pl.col("otp").mean()),
            unweighted_otp=pl.col("otp").mean(),
            route_count=pl.col("route_id").n_unique(),
        )
        .sort("month")
    )
    # Year-over-year change (current month minus same month 12 periods ago)
    monthly = monthly.with_columns(
        yoy_change=pl.col("weighted_otp") - pl.col("weighted_otp").shift(12),
    )
    return monthly


def make_chart(df: pl.DataFrame) -> None:
    """Generate the system trend time series chart."""
    plt = setup_plotting()

    months = df["month"].to_list()
    weighted = df["weighted_otp"].to_list()
    unweighted = df["unweighted_otp"].to_list()

    x = range(len(months))
    tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
    tick_labels = [months[i][:4] for i in tick_positions]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), height_ratios=[3, 1])

    # Top panel: OTP time series
    ax1.plot(x, weighted, color="#2563eb", linewidth=1.5, label="Weighted (by trips)")
    ax1.plot(
        x, unweighted, color="#9ca3af", linewidth=1, linestyle="--", label="Unweighted"
    )

    # COVID annotation
    if "2020-03" in months:
        covid_idx = months.index("2020-03")
        ax1.axvline(covid_idx, color="#ef4444", linestyle=":", alpha=0.7)
        ax1.text(
            covid_idx + 0.5, ax1.get_ylim()[1] * 0.98, "COVID",
            color="#ef4444", fontsize=8, va="top",
        )

    ax1.set_ylabel("On-Time Performance")
    ax1.set_title("PRT System-Wide On-Time Performance (2019\u20132025)")
    ax1.set_xticks(tick_positions)
    ax1.set_xticklabels(tick_labels)
    ax1.legend(loc="lower left")
    ax1.set_ylim(0, 1)

    # Bottom panel: Year-over-year change
    yoy = df["yoy_change"].to_list()
    colors = ["#22c55e" if v is not None and v >= 0 else "#ef4444" for v in yoy]
    yoy_clean = [v if v is not None else 0 for v in yoy]
    ax2.bar(x, yoy_clean, color=colors, width=1.0, alpha=0.7)
    ax2.axhline(0, color="black", linewidth=0.5)
    ax2.set_ylabel("YoY Change")
    ax2.set_xlabel("Month")
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels)

    fig.tight_layout()
    fig.savefig(OUT / "system_trend.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'system_trend.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 01: System-Wide OTP Trend")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} OTP observations loaded")

    print("\nAnalyzing...")
    result = analyze(df)
    print(f"  {len(result)} months computed")

    # Print summary
    latest = result.tail(1)
    earliest = result.head(1)
    print(f"  Period: {earliest['month'][0]} to {latest['month'][0]}")
    print(f"  Latest weighted OTP: {latest['weighted_otp'][0]:.1%}")

    print("\nSaving CSV...")
    result.write_csv(OUT / "system_trend.csv")
    print(f"  Saved to {OUT / 'system_trend.csv'}")

    print("\nGenerating chart...")
    make_chart(result)

    print("\nDone.")


if __name__ == "__main__":
    main()
