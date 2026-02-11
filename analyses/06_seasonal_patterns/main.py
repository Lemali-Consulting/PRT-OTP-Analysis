"""Seasonal decomposition of OTP into trend, seasonal, and residual components."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MIN_YEARS = 3  # minimum years of data for route-level seasonal amplitude
# Restrict to complete calendar years so every month-of-year has the same
# number of years of data (avoids bias from partial years at the boundaries).
COMPLETE_YEAR_START = "2019-01"
COMPLETE_YEAR_END = "2024-12"


def load_data() -> pl.DataFrame:
    """Load OTP data with trip weights, restricted to complete calendar years."""
    return query_to_polars(f"""
        SELECT o.route_id, o.month, o.otp, r.route_name, r.mode,
               COALESCE(rs_agg.trips_7d, 0) AS trips_7d
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        LEFT JOIN (
            SELECT route_id, SUM(trips_7d) AS trips_7d
            FROM route_stops
            GROUP BY route_id
        ) rs_agg ON o.route_id = rs_agg.route_id
        WHERE o.month >= '{COMPLETE_YEAR_START}' AND o.month <= '{COMPLETE_YEAR_END}'
    """)


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Compute detrended seasonal profiles and amplitudes."""
    # Extract month-of-year
    df = df.with_columns(
        month_num=pl.col("month").str.slice(5, 2).cast(pl.Int32),
    )

    # --- Balanced panel: only routes present in all 12 months-of-year ---
    # This prevents compositional bias (e.g., winter-only routes inflating
    # winter averages).
    months_per_route = (
        df.group_by("route_id")
        .agg(n_months_of_year=pl.col("month_num").n_unique())
    )
    balanced_routes = months_per_route.filter(
        pl.col("n_months_of_year") == 12
    )["route_id"].to_list()
    n_total = df["route_id"].n_unique()
    n_balanced = len(balanced_routes)
    print(f"  Balanced panel: {n_balanced} of {n_total} routes present in all 12 months-of-year")

    df_balanced = df.filter(pl.col("route_id").is_in(balanced_routes))

    # --- System-wide seasonal profile (trip-weighted, detrended) ---
    # Uses only balanced-panel routes so route composition is constant across months.
    # Note: trips_7d is a static snapshot and may not reflect historical service levels.
    # Step 1: trip-weighted system OTP per month
    system_monthly = (
        df_balanced.group_by("month")
        .agg(
            weighted_otp=pl.when(pl.col("trips_7d").sum() > 0)
            .then((pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum())
            .otherwise(pl.col("otp").mean()),
        )
        .sort("month")
    )

    # Step 2: 12-month centered rolling mean as trend (approximate center via shift)
    system_monthly = system_monthly.with_columns(
        trend=pl.col("weighted_otp").rolling_mean(window_size=12, min_samples=6).shift(-6),
        month_num=pl.col("month").str.slice(5, 2).cast(pl.Int32),
    )

    # Step 3: detrend and average by month-of-year
    system_monthly = system_monthly.with_columns(
        detrended=pl.col("weighted_otp") - pl.col("trend"),
    )
    system_seasonal = (
        system_monthly.filter(pl.col("detrended").is_not_null())
        .group_by("month_num")
        .agg(
            deviation=pl.col("detrended").mean(),
            weighted_otp=pl.col("weighted_otp").mean(),
        )
        .sort("month_num")
    )

    # --- Per-route: detrend, then compute seasonal amplitude ---
    min_months = MIN_YEARS * 12
    route_counts = df.group_by("route_id").agg(n_months=pl.col("month").n_unique())
    eligible = route_counts.filter(pl.col("n_months") >= min_months)["route_id"].to_list()
    df_elig = df.filter(pl.col("route_id").is_in(eligible)).sort(["route_id", "month"])

    # Per-route trend and detrending
    df_elig = df_elig.with_columns(
        trend=pl.col("otp")
        .rolling_mean(window_size=12, min_samples=6)
        .shift(-6)
        .over("route_id"),
    )
    df_elig = df_elig.with_columns(
        detrended=pl.col("otp") - pl.col("trend"),
    )

    # Raw month-of-year averages (for heatmap display)
    route_seasonal = (
        df_elig.group_by(["route_id", "route_name", "month_num"])
        .agg(avg_otp=pl.col("otp").mean())
        .sort(["route_id", "month_num"])
    )

    # Amplitude from detrended values
    detrended_by_month = (
        df_elig.filter(pl.col("detrended").is_not_null())
        .group_by(["route_id", "route_name", "month_num"])
        .agg(avg_detrended=pl.col("detrended").mean())
    )
    route_amplitude = (
        detrended_by_month.group_by(["route_id", "route_name"])
        .agg(
            seasonal_amplitude=pl.col("avg_detrended").max() - pl.col("avg_detrended").min(),
            best_month=pl.col("month_num").sort_by("avg_detrended", descending=True).first(),
            worst_month=pl.col("month_num").sort_by("avg_detrended").first(),
        )
        .sort("seasonal_amplitude", descending=True)
    )

    return system_seasonal, route_seasonal, route_amplitude


def make_chart(
    system_seasonal: pl.DataFrame,
    route_seasonal: pl.DataFrame,
    route_amplitude: pl.DataFrame,
) -> None:
    """Generate seasonal pattern charts."""
    plt = setup_plotting()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))

    # Top-left: System-wide seasonal profile (bar chart)
    ax = axes[0, 0]
    months = system_seasonal["month_num"].to_list()
    devs = system_seasonal["deviation"].to_list()
    colors = ["#22c55e" if d >= 0 else "#ef4444" for d in devs]
    ax.bar(months, devs, color=colors, alpha=0.8)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_ylabel("OTP Deviation from Trend")
    ax.set_title("System-Wide Seasonal Profile (detrended)")
    ax.axhline(0, color="black", linewidth=0.5)

    # Top-right: Top 10 routes by seasonal amplitude
    ax = axes[0, 1]
    top10 = route_amplitude.head(10)
    labels = [f"{r} - {n}" for r, n in zip(top10["route_id"].to_list(), top10["route_name"].to_list())]
    values = top10["seasonal_amplitude"].to_list()
    y_pos = range(len(labels))
    ax.barh(y_pos, values, color="#7c3aed", alpha=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Seasonal Amplitude (detrended, max - min)")
    ax.set_title(f"Routes Most Affected by Season ({MIN_YEARS}+ years data)")
    ax.invert_yaxis()

    # Bottom-left: Heatmap of seasonal OTP for top-amplitude routes
    ax = axes[1, 0]
    top_routes = route_amplitude.head(20)["route_id"].to_list()
    heatmap_data = (
        route_seasonal.filter(pl.col("route_id").is_in(top_routes))
        .pivot(on="month_num", index=["route_id", "route_name"], values="avg_otp")
        .sort("route_id")
    )
    # Build matrix
    route_labels = [f"{r} - {n}" for r, n in zip(
        heatmap_data["route_id"].to_list(), heatmap_data["route_name"].to_list()
    )]
    month_cols = sorted([c for c in heatmap_data.columns if c not in ("route_id", "route_name")], key=int)
    matrix = []
    for col in month_cols:
        matrix.append(heatmap_data[col].to_list())
    import numpy as np
    matrix_arr = np.array(matrix, dtype=float).T  # routes x months

    im = ax.imshow(matrix_arr, aspect="auto", cmap="RdYlGn", vmin=0.3, vmax=1.0)
    ax.set_xticks(range(len(month_cols)))
    ax.set_xticklabels([MONTH_LABELS[int(c) - 1] for c in month_cols], fontsize=8)
    ax.set_yticks(range(len(route_labels)))
    ax.set_yticklabels(route_labels, fontsize=6)
    ax.set_title("Seasonal OTP Heatmap (top 20 by amplitude)")
    fig.colorbar(im, ax=ax, label="Average OTP", shrink=0.8)

    # Bottom-right: Overall best/worst months (system-wide distribution)
    ax = axes[1, 1]
    system_otps = system_seasonal["weighted_otp"].to_list()
    ax.bar(range(1, 13), system_otps, color="#3b82f6", alpha=0.8)
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(MONTH_LABELS)
    ax.set_ylabel("Weighted Average OTP")
    ax.set_title("System OTP by Month of Year")
    ax.set_ylim(0, 1)

    fig.suptitle("Seasonal Patterns in PRT On-Time Performance", fontsize=13)
    fig.tight_layout()
    fig.savefig(OUT / "seasonal_patterns.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'seasonal_patterns.png'}")


def main() -> None:
    """Entry point: load data, analyze seasonal patterns, chart, and save."""
    print("=" * 60)
    print("Analysis 06: Seasonal Patterns")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    print(f"  {len(df):,} OTP observations loaded")

    print("\nAnalyzing...")
    system_seasonal, route_seasonal, route_amplitude = analyze(df)

    # Summary
    best_sys = system_seasonal.sort("weighted_otp", descending=True).head(1)
    worst_sys = system_seasonal.sort("weighted_otp").head(1)
    print(f"  Best system month:  {MONTH_LABELS[best_sys['month_num'][0] - 1]} ({best_sys['weighted_otp'][0]:.1%})")
    print(f"  Worst system month: {MONTH_LABELS[worst_sys['month_num'][0] - 1]} ({worst_sys['weighted_otp'][0]:.1%})")

    n_eligible = route_amplitude.height
    print(f"  {n_eligible} routes with {MIN_YEARS}+ years of data for seasonal ranking")

    top3 = route_amplitude.head(3)
    print("\n  Most seasonally affected routes (detrended):")
    for row in top3.iter_rows(named=True):
        print(f"    {row['route_id']} - {row['route_name']}: amplitude = {row['seasonal_amplitude']:.3f}")

    print("\nSaving CSV...")
    route_amplitude.write_csv(OUT / "seasonal_patterns.csv")
    print(f"  Saved to {OUT / 'seasonal_patterns.csv'}")

    print("\nGenerating chart...")
    make_chart(system_seasonal, route_seasonal, route_amplitude)

    print("\nDone.")


if __name__ == "__main__":
    main()
