"""Seasonal decomposition of OTP into trend, seasonal, and residual components."""

from pathlib import Path

import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data() -> pl.DataFrame:
    """Load OTP data with trip weights for seasonal analysis."""
    return query_to_polars("""
        SELECT o.route_id, o.month, o.otp, r.route_name, r.mode,
               COALESCE(rs_agg.trips_7d, 0) AS trips_7d
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        LEFT JOIN (
            SELECT route_id, SUM(trips_7d) AS trips_7d
            FROM route_stops
            GROUP BY route_id
        ) rs_agg ON o.route_id = rs_agg.route_id
    """)


def analyze(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Compute seasonal profiles, amplitudes, and decomposition."""
    # Extract month-of-year
    df = df.with_columns(
        month_num=pl.col("month").str.slice(5, 2).cast(pl.Int32),
    )

    # System-wide seasonal profile (trip-weighted)
    system_seasonal = (
        df.group_by("month_num")
        .agg(
            weighted_otp=pl.when(pl.col("trips_7d").sum() > 0)
            .then((pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum())
            .otherwise(pl.col("otp").mean()),
        )
        .sort("month_num")
    )
    system_mean = df.select(
        pl.when(pl.col("trips_7d").sum() > 0)
        .then((pl.col("otp") * pl.col("trips_7d")).sum() / pl.col("trips_7d").sum())
        .otherwise(pl.col("otp").mean())
    ).item()
    system_seasonal = system_seasonal.with_columns(
        deviation=pl.col("weighted_otp") - system_mean,
    )

    # Per-route seasonal profile and amplitude
    route_seasonal = (
        df.group_by(["route_id", "route_name", "month_num"])
        .agg(avg_otp=pl.col("otp").mean())
        .sort(["route_id", "month_num"])
    )

    route_amplitude = (
        route_seasonal.group_by(["route_id", "route_name"])
        .agg(
            seasonal_amplitude=pl.col("avg_otp").max() - pl.col("avg_otp").min(),
            best_month=pl.col("month_num").sort_by("avg_otp", descending=True).first(),
            worst_month=pl.col("month_num").sort_by("avg_otp").first(),
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
    ax.set_ylabel("OTP Deviation from Annual Mean")
    ax.set_title("System-Wide Seasonal Profile")
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
    ax.set_xlabel("Seasonal Amplitude (max - min month avg)")
    ax.set_title("Routes Most Affected by Season")
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

    top3 = route_amplitude.head(3)
    print("\n  Most seasonally affected routes:")
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
