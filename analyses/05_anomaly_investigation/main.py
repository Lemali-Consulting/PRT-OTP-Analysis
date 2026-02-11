"""Anomaly detection: flag and investigate sharp OTP deviations (both drops and spikes)."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

KNOWN_EVENTS = {
    "2020-03": "COVID-19 shutdown begins",
    "2020-04": "COVID-19 reduced service",
    "2020-05": "COVID-19 reduced service",
    "2020-06": "COVID-19 partial recovery",
}

Z_THRESHOLD = 2.0
ROLLING_WINDOW = 12
MIN_PERIODS = 6


def load_data() -> pl.DataFrame:
    """Load OTP data with route metadata, sorted for rolling calculations."""
    return query_to_polars("""
        SELECT o.route_id, o.month, o.otp, r.route_name, r.mode
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        ORDER BY o.route_id, o.month
    """)


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Flag anomaly months and return both the full data and flagged anomalies."""
    df = df.sort(["route_id", "month"])

    # Rolling stats per route (shifted by 1 so current month is excluded from baseline)
    df = df.with_columns(
        rolling_mean=pl.col("otp")
        .shift(1)
        .rolling_mean(window_size=ROLLING_WINDOW, min_samples=MIN_PERIODS)
        .over("route_id"),
        rolling_std=pl.col("otp")
        .shift(1)
        .rolling_std(window_size=ROLLING_WINDOW, min_samples=MIN_PERIODS)
        .over("route_id"),
    )

    # Z-score and anomaly flag (guard against division by zero when rolling_std ~ 0)
    df = df.with_columns(
        z_score=pl.when(pl.col("rolling_std") > 1e-9)
        .then((pl.col("otp") - pl.col("rolling_mean")) / pl.col("rolling_std"))
        .otherwise(0.0),
    )
    df = df.with_columns(
        is_anomaly=pl.col("z_score").abs() > Z_THRESHOLD,
    )

    # Add known events
    df = df.with_columns(
        known_event=pl.col("month").replace_strict(KNOWN_EVENTS, default=None),
    )

    anomalies = df.filter(pl.col("is_anomaly")).sort(["route_id", "month"])
    return df, anomalies


def make_chart(full_df: pl.DataFrame, anomalies: pl.DataFrame) -> None:
    """Generate time series profiles for routes with most anomalies."""
    plt = setup_plotting()

    # Find top 5 routes by anomaly count
    top_routes = (
        anomalies.group_by("route_id")
        .agg(pl.len().alias("anomaly_count"))
        .sort("anomaly_count", descending=True)
        .head(5)
    )

    route_ids = top_routes["route_id"].to_list()
    n_routes = len(route_ids)
    if n_routes == 0:
        print("  No anomalies detected; skipping chart.")
        return

    fig, axes = plt.subplots(n_routes, 1, figsize=(14, 3 * n_routes), sharex=True)
    if n_routes == 1:
        axes = [axes]

    for ax, rid in zip(axes, route_ids):
        route_data = full_df.filter(pl.col("route_id") == rid).sort("month")
        months = route_data["month"].to_list()
        otp_vals = route_data["otp"].to_list()
        rm_vals = route_data["rolling_mean"].to_list()
        rs_vals = route_data["rolling_std"].to_list()
        x = range(len(months))

        # OTP line
        ax.plot(x, otp_vals, color="#2563eb", linewidth=1, label="OTP")
        # Rolling mean
        ax.plot(x, rm_vals, color="#9ca3af", linewidth=1, linestyle="--", label="12-mo rolling mean")
        # Rolling std band (use NaN for missing values so matplotlib can handle them)
        nan = float("nan")
        upper = [m + s if m is not None and s is not None else nan for m, s in zip(rm_vals, rs_vals)]
        lower = [m - s if m is not None and s is not None else nan for m, s in zip(rm_vals, rs_vals)]
        ax.fill_between(list(x), lower, upper, alpha=0.15, color="#9ca3af")

        # Mark anomalies
        route_anomalies = route_data.filter(pl.col("is_anomaly"))
        anom_indices = [months.index(m) for m in route_anomalies["month"].to_list() if m in months]
        anom_otps = route_anomalies["otp"].to_list()
        ax.scatter(anom_indices, anom_otps, color="#ef4444", s=30, zorder=5, label="Anomaly")

        route_name = route_data["route_name"][0]
        count = len(anom_indices)
        ax.set_title(f"{rid} - {route_name} ({count} anomalies)", fontsize=10)
        ax.set_ylabel("OTP")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=7, loc="lower left")

        # X-axis ticks at January of each year
        tick_positions = [i for i, m in enumerate(months) if m.endswith("-01")]
        tick_labels = [months[i][:4] for i in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels)

    axes[-1].set_xlabel("Month")
    fig.suptitle("Routes with Most OTP Anomalies", fontsize=13, y=1.01)
    fig.tight_layout()
    fig.savefig(OUT / "anomaly_profiles.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'anomaly_profiles.png'}")


def main() -> None:
    """Entry point: load data, detect anomalies, chart, and save."""
    print("=" * 60)
    print("Analysis 05: Anomaly Investigation")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} OTP observations loaded")

    print("\nDetecting anomalies...")
    full_df, anomalies = analyze(df)
    n_routes_with = anomalies["route_id"].n_unique()
    print(f"  {len(anomalies)} anomalous months flagged across {n_routes_with} routes")
    print(f"  (threshold: |z-score| > {Z_THRESHOLD}, rolling window = {ROLLING_WINDOW} months)")

    # Top offenders
    top = (
        anomalies.group_by(["route_id", "route_name"])
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(5)
    )
    print("\n  Top 5 routes by anomaly count:")
    for row in top.iter_rows(named=True):
        print(f"    {row['route_id']:>5} - {row['route_name']}: {row['count']} anomalies")

    # Mode-stratified anomaly rates
    mode_summary = (
        full_df.filter(pl.col("rolling_mean").is_not_null())
        .group_by("mode")
        .agg(
            total_months=pl.len(),
            anomaly_count=pl.col("is_anomaly").sum(),
        )
        .with_columns(
            anomaly_rate=(pl.col("anomaly_count") / pl.col("total_months")),
        )
        .sort("mode")
    )
    print("\n  Anomaly rates by mode:")
    print(f"    {'Mode':<10} {'Anomalies':>10} {'Total Months':>13} {'Rate':>8}")
    print(f"    {'-' * 43}")
    for row in mode_summary.iter_rows(named=True):
        print(f"    {row['mode']:<10} {row['anomaly_count']:>10} {row['total_months']:>13} {row['anomaly_rate']:>8.1%}")

    # Expected false-positive rate comparison
    evaluated_obs = full_df.filter(pl.col("rolling_mean").is_not_null()).height
    expected_fp = int(round(evaluated_obs * 0.0455))  # ~4.55% for 2-sigma two-sided
    actual_anomalies = len(anomalies)
    print(f"\n  False-positive context (2-sigma, two-sided):")
    print(f"    Evaluated observations: {evaluated_obs:,}")
    print(f"    Expected under normality (~4.6%): ~{expected_fp}")
    print(f"    Actual anomalies flagged: {actual_anomalies}")
    print(f"    Ratio (actual / expected): {actual_anomalies / expected_fp:.2f}x")

    # Excluded routes (fewer than 7 months of data)
    route_month_counts = df.group_by("route_id").agg(pl.len().alias("n_months"))
    excluded = route_month_counts.filter(pl.col("n_months") < 7)
    excluded_with_names = excluded.join(
        df.select("route_id", "route_name").unique(),
        on="route_id",
    )
    print(f"\n  Routes excluded from anomaly detection (< 7 months of data): {len(excluded)}")
    for row in excluded_with_names.iter_rows(named=True):
        print(f"    {row['route_id']} - {row['route_name']} ({row['n_months']} months)")

    # UNKNOWN-mode routes
    unknown_routes = df.filter(pl.col("mode") == "UNKNOWN").select("route_id", "route_name").unique()
    print(f"\n  UNKNOWN-mode routes included: {len(unknown_routes)}")
    for row in unknown_routes.iter_rows(named=True):
        print(f"    {row['route_id']} - {row['route_name']}")

    print("\nSaving CSV...")
    anomalies.select(
        "route_id", "route_name", "mode", "month", "otp",
        "rolling_mean", "rolling_std", "z_score", "known_event",
    ).write_csv(OUT / "anomalies.csv")
    print(f"  Saved to {OUT / 'anomalies.csv'}")

    print("\nGenerating chart...")
    make_chart(full_df, anomalies)

    print("\nDone.")


if __name__ == "__main__":
    main()
