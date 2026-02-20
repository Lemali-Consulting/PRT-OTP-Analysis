"""Analysis 29: Do schedule changes (pick period transitions) correlate with OTP shifts?"""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

WINDOW = 3  # months before/after a schedule change to average


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load scheduled trips (WEEKDAY) and OTP for the overlap period."""
    sched = query_to_polars("""
        SELECT route_id, month, daily_trips, pick_id
        FROM scheduled_trips_monthly
        WHERE day_type = 'WEEKDAY'
        ORDER BY route_id, month
    """)
    otp = query_to_polars("""
        SELECT route_id, month, otp
        FROM otp_monthly
        ORDER BY route_id, month
    """)
    return sched, otp


def detect_change_events(sched: pl.DataFrame) -> pl.DataFrame:
    """Find months where a route's pick_id changes from the prior month."""
    df = sched.sort(["route_id", "month"])

    df = df.with_columns(
        prev_pick=pl.col("pick_id").shift(1).over("route_id"),
        prev_trips=pl.col("daily_trips").shift(1).over("route_id"),
        prev_month=pl.col("month").shift(1).over("route_id"),
    )

    # A change event occurs when pick_id differs from the previous month
    events = df.filter(
        pl.col("prev_pick").is_not_null() & (pl.col("pick_id") != pl.col("prev_pick"))
    ).select(
        "route_id",
        pl.col("month").alias("change_month"),
        pl.col("prev_pick").alias("old_pick"),
        pl.col("pick_id").alias("new_pick"),
        pl.col("prev_trips").alias("trips_before"),
        pl.col("daily_trips").alias("trips_after"),
    )

    events = events.with_columns(
        trip_delta=(pl.col("trips_after") - pl.col("trips_before")),
    )

    return events


def compute_otp_deltas(events: pl.DataFrame, otp: pl.DataFrame) -> pl.DataFrame:
    """For each change event, compute mean OTP in the window before/after."""
    all_months = sorted(otp["month"].unique().to_list())
    month_idx = {m: i for i, m in enumerate(all_months)}

    results = []
    for row in events.iter_rows(named=True):
        route = row["route_id"]
        change_m = row["change_month"]
        if change_m not in month_idx:
            continue

        ci = month_idx[change_m]

        # Months before (excluding the change month itself)
        before_months = [all_months[j] for j in range(max(0, ci - WINDOW), ci)]
        # Months after (including the change month)
        after_months = [all_months[j] for j in range(ci, min(len(all_months), ci + WINDOW))]

        route_otp = otp.filter(pl.col("route_id") == route)

        otp_before = route_otp.filter(pl.col("month").is_in(before_months))["otp"]
        otp_after = route_otp.filter(pl.col("month").is_in(after_months))["otp"]

        if len(otp_before) < 2 or len(otp_after) < 2:
            continue

        results.append({
            **row,
            "otp_before": otp_before.mean(),
            "otp_after": otp_after.mean(),
            "otp_delta": otp_after.mean() - otp_before.mean(),
            "n_before": len(otp_before),
            "n_after": len(otp_after),
        })

    return pl.DataFrame(results)


def classify_events(df: pl.DataFrame) -> pl.DataFrame:
    """Classify events as increase, cut, or neutral based on trip delta."""
    return df.with_columns(
        event_type=pl.when(pl.col("trip_delta") > 0).then(pl.lit("increase"))
        .when(pl.col("trip_delta") < 0).then(pl.lit("cut"))
        .otherwise(pl.lit("neutral")),
        is_covid=pl.col("change_month").is_in(["2020-03", "2020-04"]),
    )


def make_chart(df: pl.DataFrame) -> None:
    """Scatter plot: trip change vs OTP change, colored by COVID status."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 7))

    non_covid = df.filter(~pl.col("is_covid"))
    covid = df.filter(pl.col("is_covid"))

    ax.scatter(
        non_covid["trip_delta"].to_list(),
        non_covid["otp_delta"].to_list(),
        alpha=0.4, s=30, color="#2563eb", label=f"Non-COVID (n={len(non_covid)})",
    )
    if len(covid) > 0:
        ax.scatter(
            covid["trip_delta"].to_list(),
            covid["otp_delta"].to_list(),
            alpha=0.7, s=60, color="#ef4444", marker="x",
            label=f"COVID period (n={len(covid)})",
        )

    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.5)
    ax.set_xlabel("Change in Daily Trips")
    ax.set_ylabel("Change in OTP (3-month mean after - before)")
    ax.set_title("Service Change Impact on OTP")
    ax.legend(fontsize=9)

    fig.tight_layout()
    fig.savefig(OUT / "service_change_impact.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'service_change_impact.png'}")


def summarize(df: pl.DataFrame) -> pl.DataFrame:
    """Summary statistics by event type."""
    summary = (
        df.group_by("event_type")
        .agg(
            n=pl.col("otp_delta").count(),
            mean_otp_delta=pl.col("otp_delta").mean(),
            median_otp_delta=pl.col("otp_delta").median(),
            std_otp_delta=pl.col("otp_delta").std(),
            mean_trip_delta=pl.col("trip_delta").mean(),
        )
        .sort("event_type")
    )
    return summary


def main() -> None:
    """Entry point: detect schedule change events and measure OTP impact."""
    print("=" * 60)
    print("Analysis 29: Service Change Impact on OTP")
    print("=" * 60)

    print("\nLoading data...")
    sched, otp = load_data()
    print(f"  Scheduled trips: {len(sched):,} rows ({sched['route_id'].n_unique()} routes)")
    print(f"  OTP: {len(otp):,} rows")

    print("\nDetecting schedule change events...")
    events = detect_change_events(sched)
    print(f"  {len(events)} pick_id change events detected")
    print(f"  Across {events['route_id'].n_unique()} routes")

    print("\nComputing OTP deltas ({}-month window)...".format(WINDOW))
    df = compute_otp_deltas(events, otp)
    print(f"  {len(df)} events with sufficient OTP data")

    df = classify_events(df)

    # Overall stats
    otp_deltas = df["otp_delta"].to_list()
    t_stat, p_val = stats.ttest_1samp(otp_deltas, 0)
    print(f"\n  Overall OTP delta: mean={df['otp_delta'].mean():.4f}, median={df['otp_delta'].median():.4f}")
    print(f"  One-sample t-test (H0: delta=0): t={t_stat:.2f}, p={p_val:.4f}")

    # By event type
    summary = summarize(df)
    print("\n  By event type:")
    for row in summary.iter_rows(named=True):
        print(f"    {row['event_type']:>10s}: n={row['n']:3d}, mean_otp_delta={row['mean_otp_delta']:+.4f}, "
              f"mean_trip_delta={row['mean_trip_delta']:+.1f}")

    # Kruskal-Wallis across event types
    groups = []
    for et in ["cut", "increase", "neutral"]:
        g = df.filter(pl.col("event_type") == et)["otp_delta"].to_list()
        if len(g) >= 2:
            groups.append(g)
    if len(groups) >= 2:
        h_stat, kw_p = stats.kruskal(*groups)
        print(f"\n  Kruskal-Wallis (event types): H={h_stat:.2f}, p={kw_p:.4f}")

    # COVID vs non-COVID
    non_covid = df.filter(~pl.col("is_covid"))
    covid = df.filter(pl.col("is_covid"))
    print(f"\n  Non-COVID events: n={len(non_covid)}, mean delta={non_covid['otp_delta'].mean():.4f}")
    if len(covid) > 0:
        print(f"  COVID events: n={len(covid)}, mean delta={covid['otp_delta'].mean():.4f}")

    # Correlation: trip_delta vs otp_delta
    r, r_p = stats.pearsonr(df["trip_delta"].to_list(), otp_deltas)
    rho, rho_p = stats.spearmanr(df["trip_delta"].to_list(), otp_deltas)
    print(f"\n  Trip delta vs OTP delta: Pearson r={r:.3f} (p={r_p:.4f}), Spearman rho={rho:.3f} (p={rho_p:.4f})")

    print("\nSaving outputs...")
    df.write_csv(OUT / "service_change_events.csv")
    print(f"  Saved {OUT / 'service_change_events.csv'}")
    summary.write_csv(OUT / "service_change_summary.csv")
    print(f"  Saved {OUT / 'service_change_summary.csv'}")

    print("\nGenerating chart...")
    make_chart(df)

    print("\nDone.")


if __name__ == "__main__":
    main()
