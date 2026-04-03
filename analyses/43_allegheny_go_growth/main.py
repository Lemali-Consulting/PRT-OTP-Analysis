"""Analysis 43: track Allegheny Go program growth and overlay on system OTP."""

import polars as pl
from scipy import stats

from prt_otp_analysis.common import (
    COLOR_PRIMARY,
    DATA_DIR,
    analysis_dir,
    phase,
    query_to_polars,
    run_analysis,
    save_chart,
    save_csv,
    setup_plotting,
)

OUT = analysis_dir(__file__)
AG_DIR = DATA_DIR / "allegheny-go"

ENROLLMENT_COLORS: dict[str, str] = {
    "Ready2Ride": "#3b82f6",
    "ConnectCard Pickup": "#22c55e",
    "ConnectCard Mail": "#f59e0b",
}


def load_ridership_monthly() -> pl.DataFrame:
    """Load weekly ridership from DB and aggregate to monthly."""
    weekly_df = query_to_polars(
        "SELECT week_start, rides, riders FROM allegheny_go_weekly ORDER BY week_start"
    )
    return (
        weekly_df.with_columns(
            month=pl.col("week_start").str.slice(0, 7),
        )
        .group_by("month")
        .agg(
            total_rides=pl.col("rides").sum(),
            avg_weekly_riders=pl.col("riders").mean(),
            max_riders=pl.col("riders").max(),
            n_weeks=pl.len(),
        )
        .sort("month")
    )


def load_system_otp() -> pl.DataFrame:
    """Compute unweighted system-average OTP per month."""
    return query_to_polars("""
        SELECT month, AVG(otp) AS system_otp, COUNT(*) AS n_routes
        FROM otp_monthly
        GROUP BY month
        ORDER BY month
    """)


def load_enrollments_monthly() -> pl.DataFrame:
    """Load weekly enrollments and aggregate to monthly by type."""
    enroll_df = pl.read_csv(AG_DIR / "enrollments_weekly.csv")
    return (
        enroll_df.with_columns(
            month=pl.col("week_start").str.slice(0, 7),
        )
        .group_by("month", "enrollment_type")
        .agg(total=pl.col("count").sum())
        .sort("month", "enrollment_type")
    )


def make_ridership_otp_overlay(monthly_df: pl.DataFrame) -> None:
    """Dual-axis chart: monthly rides (bars) and system OTP (line)."""
    plt = setup_plotting()
    fig, ax1 = plt.subplots(figsize=(12, 6))

    months = monthly_df["month"].to_list()
    rides = monthly_df["total_rides"].to_list()
    otp = monthly_df["system_otp"].to_list()
    x = range(len(months))

    # Rides as bars (left axis)
    ax1.bar(x, rides, color=COLOR_PRIMARY, alpha=0.7, label="Monthly rides")
    ax1.set_ylabel("Total Monthly Rides", color=COLOR_PRIMARY)
    ax1.tick_params(axis="y", labelcolor=COLOR_PRIMARY)
    ax1.set_xticks(list(x)[::2])
    ax1.set_xticklabels([months[i] for i in list(x)[::2]], rotation=45, ha="right", fontsize=8)

    # OTP as line (right axis)
    ax2 = ax1.twinx()
    valid_otp = [(i, v) for i, v in zip(x, otp) if v is not None]
    if valid_otp:
        ax2.plot(
            [i for i, _ in valid_otp],
            [v for _, v in valid_otp],
            color="#ef4444", linewidth=2, marker="o", markersize=4,
            label="System avg OTP",
        )
    ax2.set_ylabel("System Average OTP", color="#ef4444")
    ax2.tick_params(axis="y", labelcolor="#ef4444")
    ax2.set_ylim(0.55, 0.85)

    ax1.set_title("Allegheny Go Ridership vs System On-Time Performance")
    ax1.set_xlabel("Month")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    fig.tight_layout()
    save_chart(fig, OUT / "ridership_otp_overlay.png")


def make_enrollment_chart(enroll_monthly_df: pl.DataFrame) -> None:
    """Stacked area chart of enrollment types over time."""
    plt = setup_plotting()

    pivoted_df = enroll_monthly_df.pivot(
        on="enrollment_type", index="month", values="total"
    ).sort("month").fill_null(0)

    months = pivoted_df["month"].to_list()
    x = range(len(months))

    fig, ax = plt.subplots(figsize=(12, 6))

    bottom = [0] * len(months)
    for etype, color in ENROLLMENT_COLORS.items():
        if etype in pivoted_df.columns:
            vals = pivoted_df[etype].to_list()
            ax.bar(x, vals, bottom=bottom, color=color, label=etype, alpha=0.8)
            bottom = [b + v for b, v in zip(bottom, vals)]

    ax.set_xticks(list(x)[::2])
    ax.set_xticklabels([months[i] for i in list(x)[::2]], rotation=45, ha="right", fontsize=8)
    ax.set_title("Weekly Enrollments by Type (Monthly Total)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Enrollments")
    ax.legend(fontsize=9)
    fig.tight_layout()
    save_chart(fig, OUT / "enrollment_by_type.png")


def make_utilization_chart(monthly_df: pl.DataFrame) -> None:
    """Rides-per-rider utilization over time."""
    plt = setup_plotting()
    fig, ax = plt.subplots(figsize=(10, 5))

    months = monthly_df["month"].to_list()
    util = monthly_df["rides_per_rider"].to_list()

    ax.plot(range(len(months)), util, color=COLOR_PRIMARY, linewidth=2, marker="o", markersize=5)
    ax.set_xticks(range(0, len(months), 2))
    ax.set_xticklabels([months[i] for i in range(0, len(months), 2)], rotation=45, ha="right", fontsize=8)
    ax.set_title("Allegheny Go: Average Rides per Rider per Week")
    ax.set_xlabel("Month")
    ax.set_ylabel("Rides / Rider (weekly avg)")
    fig.tight_layout()
    save_chart(fig, OUT / "utilization_trend.png")


@run_analysis(43, "Allegheny Go Program Growth")
def main() -> None:
    """Entry point: analyze Allegheny Go growth and overlay on system OTP."""
    with phase("Loading data"):
        ride_monthly_df = load_ridership_monthly()
        otp_monthly_df = load_system_otp()
        enroll_monthly_df = load_enrollments_monthly()
        print(f"  Ridership months: {len(ride_monthly_df)}")
        print(f"  OTP months: {len(otp_monthly_df)}")
        print(f"  Enrollment rows: {len(enroll_monthly_df)}")

    with phase("Computing metrics"):
        # Add rides-per-rider
        ride_monthly_df = ride_monthly_df.with_columns(
            rides_per_rider=(
                pl.col("total_rides") / pl.col("avg_weekly_riders") / pl.col("n_weeks")
            ),
        )

        # Join ridership to system OTP
        merged_df = ride_monthly_df.join(otp_monthly_df, on="month", how="left")

        # Overlap period stats
        overlap_df = merged_df.filter(pl.col("system_otp").is_not_null())
        print(f"  Overlap months: {len(overlap_df)}")

        if len(overlap_df) >= 5:
            r, p = stats.pearsonr(
                overlap_df["total_rides"].to_list(),
                overlap_df["system_otp"].to_list(),
            )
            print(f"  Pearson r (rides vs OTP): {r:.3f} (p = {p:.3f}, n = {len(overlap_df)})")
        else:
            r, p = None, None
            print("  Insufficient overlap for correlation")

        # Summary stats
        total_rides = ride_monthly_df["total_rides"].sum()
        latest_riders = ride_monthly_df.sort("month").tail(1)["max_riders"][0]
        print(f"  Total rides: {total_rides:,}")
        print(f"  Latest month max riders: {latest_riders:,}")

        save_csv(
            merged_df.select(
                "month", "total_rides", "max_riders", "rides_per_rider",
                "n_weeks", "system_otp",
            ),
            OUT / "growth_vs_otp.csv",
        )

    with phase("Generating charts"):
        make_ridership_otp_overlay(merged_df)
        make_enrollment_chart(enroll_monthly_df)
        make_utilization_chart(ride_monthly_df)


if __name__ == "__main__":
    main()
