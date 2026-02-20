"""Analysis 25: Measure ridership concentration on low-OTP routes using Lorenz curves and Gini coefficients."""

from pathlib import Path

import numpy as np
import polars as pl

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_MONTHS = 12


def load_data() -> pl.DataFrame:
    """Load route-level average OTP, ridership, and mode."""
    df = query_to_polars("""
        SELECT o.route_id, o.month, o.otp,
               r.avg_riders,
               rt.mode
        FROM otp_monthly o
        JOIN ridership_monthly r
            ON o.route_id = r.route_id AND o.month = r.month
            AND r.day_type = 'WEEKDAY'
        JOIN routes rt ON o.route_id = rt.route_id
        WHERE r.avg_riders IS NOT NULL
    """)

    # Filter to routes with enough paired months
    route_counts = df.group_by("route_id").agg(pl.col("month").count().alias("n"))
    keep = route_counts.filter(pl.col("n") >= MIN_MONTHS)["route_id"].to_list()
    df = df.filter(pl.col("route_id").is_in(keep))

    return df


def route_summary(df: pl.DataFrame) -> pl.DataFrame:
    """Compute route-level average OTP and average ridership."""
    return (
        df.group_by("route_id", "mode")
        .agg(
            avg_otp=pl.col("otp").mean(),
            avg_riders=pl.col("avg_riders").mean(),
            n_months=pl.col("month").count(),
        )
        .sort("avg_otp")  # worst to best
    )


def compute_lorenz(routes: pl.DataFrame) -> dict:
    """Compute Lorenz curve data and Gini-like concentration index.

    Routes are sorted worst-to-best by OTP.  The Lorenz curve plots
    cumulative route share (x) vs cumulative ridership share (y).
    If riders concentrate on low-OTP routes, the curve bows above
    the diagonal.
    """
    routes = routes.sort("avg_otp")  # worst to best
    riders = routes["avg_riders"].to_numpy()
    total = riders.sum()

    n = len(riders)
    cum_route_share = np.arange(1, n + 1) / n
    cum_rider_share = np.cumsum(riders) / total

    # Gini-like index: area between curve and diagonal
    # Positive = riders concentrate on low-OTP routes
    # Use trapezoidal integration
    area_under_curve = np.trapezoid(cum_rider_share, cum_route_share)
    area_under_diagonal = 0.5  # triangle
    gini = 2 * (area_under_curve - area_under_diagonal)

    # Find OTP threshold below which 50% of ridership is carried
    otp_vals = routes["avg_otp"].to_list()
    idx_50 = np.searchsorted(cum_rider_share, 0.5)
    if idx_50 < n:
        otp_at_50 = otp_vals[idx_50]
    else:
        otp_at_50 = otp_vals[-1]

    # Routes needed for 50% of ridership
    routes_for_50 = int(idx_50 + 1)

    return {
        "cum_route_share": np.concatenate([[0], cum_route_share]),
        "cum_rider_share": np.concatenate([[0], cum_rider_share]),
        "gini": gini,
        "otp_at_50_pct": otp_at_50,
        "routes_for_50_pct": routes_for_50,
        "n_routes": n,
        "otp_values": otp_vals,
    }


def compute_quintiles(routes: pl.DataFrame) -> pl.DataFrame:
    """Divide routes into OTP quintiles and compute summary stats."""
    routes = routes.sort("avg_otp")
    n = len(routes)
    quintile_size = n // 5
    remainder = n % 5

    # Assign quintile labels (Q1 = worst, Q5 = best)
    labels = []
    for q in range(1, 6):
        size = quintile_size + (1 if q <= remainder else 0)
        labels.extend([f"Q{q}"] * size)

    routes = routes.with_columns(
        pl.Series("quintile", labels),
    )

    summary = (
        routes.group_by("quintile")
        .agg(
            n_routes=pl.col("route_id").count(),
            avg_otp=pl.col("avg_otp").mean(),
            min_otp=pl.col("avg_otp").min(),
            max_otp=pl.col("avg_otp").max(),
            total_riders=pl.col("avg_riders").sum(),
            avg_riders=pl.col("avg_riders").mean(),
        )
        .sort("quintile")
    )

    # Add ridership share
    total = summary["total_riders"].sum()
    summary = summary.with_columns(
        (pl.col("total_riders") / total * 100).alias("ridership_share_pct"),
    )

    return summary


def make_lorenz_chart(lorenz_all: dict, lorenz_bus: dict) -> None:
    """Plot Lorenz curves for all routes and bus-only."""
    plt = setup_plotting()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    for ax, lorenz, title in [
        (ax1, lorenz_all, f"All Routes (n={lorenz_all['n_routes']})"),
        (ax2, lorenz_bus, f"Bus Only (n={lorenz_bus['n_routes']})"),
    ]:
        ax.plot(
            lorenz["cum_route_share"], lorenz["cum_rider_share"],
            color="#2563eb", linewidth=2.0, label="Actual", zorder=3,
        )
        ax.plot([0, 1], [0, 1], color="gray", linestyle="--", linewidth=1.0,
                label="Perfect equality", alpha=0.6)
        ax.fill_between(
            lorenz["cum_route_share"], lorenz["cum_rider_share"],
            lorenz["cum_route_share"],
            alpha=0.15, color="#2563eb",
        )

        # Mark 50% ridership point
        idx_50 = np.searchsorted(lorenz["cum_rider_share"], 0.5)
        if idx_50 < len(lorenz["cum_route_share"]):
            x50 = lorenz["cum_route_share"][idx_50]
            ax.axhline(0.5, color="#e11d48", linestyle=":", alpha=0.4)
            ax.axvline(x50, color="#e11d48", linestyle=":", alpha=0.4)
            ax.plot(x50, 0.5, "o", color="#e11d48", markersize=6, zorder=4)
            ax.annotate(
                f"50% riders\n({lorenz['routes_for_50_pct']}/{lorenz['n_routes']} routes"
                f"\nOTP < {lorenz['otp_at_50_pct']:.1%})",
                xy=(x50, 0.5), xytext=(x50 + 0.12, 0.35),
                fontsize=8, color="#e11d48",
                arrowprops=dict(arrowstyle="->", color="#e11d48", lw=1.0),
            )

        ax.set_xlabel("Cumulative Share of Routes (worst OTP -> best)")
        ax.set_ylabel("Cumulative Share of Ridership")
        ax.set_title(f"{title}\nGini = {lorenz['gini']:.3f}")
        ax.legend(loc="upper left", fontsize=9)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")

    fig.suptitle("Ridership Concentration on Low-OTP Routes", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "ridership_lorenz.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'ridership_lorenz.png'}")


def make_quintile_chart(quintiles_all: pl.DataFrame, quintiles_bus: pl.DataFrame) -> None:
    """Bar chart of ridership share and average OTP by quintile."""
    plt = setup_plotting()
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, quintiles, title in [
        (axes[0], quintiles_all, "All Routes"),
        (axes[1], quintiles_bus, "Bus Only"),
    ]:
        qs = quintiles["quintile"].to_list()
        ridership_share = quintiles["ridership_share_pct"].to_list()
        avg_otp = [v * 100 for v in quintiles["avg_otp"].to_list()]

        x = np.arange(len(qs))
        width = 0.35

        bars1 = ax.bar(x - width / 2, ridership_share, width, label="Ridership Share (%)",
                        color="#2563eb", alpha=0.7)
        ax.set_ylabel("Ridership Share (%)", color="#2563eb")
        ax.set_xlabel("OTP Quintile (Q1=worst, Q5=best)")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(qs)

        # Add OTP values on secondary axis
        ax2 = ax.twinx()
        bars2 = ax2.bar(x + width / 2, avg_otp, width, label="Avg OTP (%)",
                         color="#e11d48", alpha=0.7)
        ax2.set_ylabel("Average OTP (%)", color="#e11d48")
        ax2.set_ylim(50, 90)

        # Add value labels
        for bar, val in zip(bars1, ridership_share):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=8, color="#2563eb")
        for bar, val in zip(bars2, avg_otp):
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                     f"{val:.1f}%", ha="center", va="bottom", fontsize=8, color="#e11d48")

        # Combined legend
        lines = [bars1, bars2]
        labels = ["Ridership Share", "Avg OTP"]
        ax.legend(lines, labels, loc="upper left", fontsize=8)

    fig.suptitle("Ridership and OTP by Quintile", fontsize=13, y=1.02)
    fig.tight_layout()
    fig.savefig(OUT / "quintile_summary.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'quintile_summary.png'}")


def main() -> None:
    """Entry point: load data, compute Lorenz/Gini, quintiles, chart, and save."""
    print("=" * 60)
    print("Analysis 25: Ridership Concentration & Equity")
    print("=" * 60)

    print("\nLoading data...")
    df = load_data()
    n_routes = df["route_id"].n_unique()
    print(f"  {len(df):,} route-month observations ({n_routes} routes)")

    print("\nComputing route-level summaries...")
    routes_all = route_summary(df)
    routes_bus = routes_all.filter(pl.col("mode") == "BUS")
    print(f"  All routes: {len(routes_all)}, Bus only: {len(routes_bus)}")

    # Lorenz curves
    print("\nComputing Lorenz curves...")
    lorenz_all = compute_lorenz(routes_all)
    lorenz_bus = compute_lorenz(routes_bus)

    print(f"\n  All routes:")
    print(f"    Gini concentration index: {lorenz_all['gini']:.3f}")
    print(f"    50% of ridership carried by {lorenz_all['routes_for_50_pct']}/{lorenz_all['n_routes']} "
          f"routes (OTP < {lorenz_all['otp_at_50_pct']:.1%})")
    print(f"  Bus only:")
    print(f"    Gini concentration index: {lorenz_bus['gini']:.3f}")
    print(f"    50% of ridership carried by {lorenz_bus['routes_for_50_pct']}/{lorenz_bus['n_routes']} "
          f"routes (OTP < {lorenz_bus['otp_at_50_pct']:.1%})")

    # Quintiles
    print("\nComputing quintile breakdowns...")
    quintiles_all = compute_quintiles(routes_all)
    quintiles_bus = compute_quintiles(routes_bus)

    print("\n  All routes quintiles:")
    print(f"  {'Quintile':<10} {'Routes':>7} {'Avg OTP':>9} {'OTP Range':>18} {'Ridership%':>11}")
    for row in quintiles_all.iter_rows(named=True):
        print(f"  {row['quintile']:<10} {row['n_routes']:>7} {row['avg_otp']:>9.1%} "
              f"{row['min_otp']:>8.1%} - {row['max_otp']:.1%} {row['ridership_share_pct']:>10.1f}%")

    print("\n  Bus-only quintiles:")
    print(f"  {'Quintile':<10} {'Routes':>7} {'Avg OTP':>9} {'OTP Range':>18} {'Ridership%':>11}")
    for row in quintiles_bus.iter_rows(named=True):
        print(f"  {row['quintile']:<10} {row['n_routes']:>7} {row['avg_otp']:>9.1%} "
              f"{row['min_otp']:>8.1%} - {row['max_otp']:.1%} {row['ridership_share_pct']:>10.1f}%")

    # Equity metrics CSV
    print("\nSaving CSV...")
    metrics = pl.DataFrame([
        {"metric": "gini_all", "value": lorenz_all["gini"]},
        {"metric": "gini_bus", "value": lorenz_bus["gini"]},
        {"metric": "otp_at_50pct_all", "value": lorenz_all["otp_at_50_pct"]},
        {"metric": "otp_at_50pct_bus", "value": lorenz_bus["otp_at_50_pct"]},
        {"metric": "routes_for_50pct_all", "value": float(lorenz_all["routes_for_50_pct"])},
        {"metric": "routes_for_50pct_bus", "value": float(lorenz_bus["routes_for_50_pct"])},
        {"metric": "n_routes_all", "value": float(lorenz_all["n_routes"])},
        {"metric": "n_routes_bus", "value": float(lorenz_bus["n_routes"])},
    ])
    metrics.write_csv(OUT / "equity_metrics.csv")
    print(f"  {OUT / 'equity_metrics.csv'}")

    # Also save quintile detail
    quintiles_all.with_columns(pl.lit("all").alias("subset")).vstack(
        quintiles_bus.with_columns(pl.lit("bus").alias("subset"))
    ).write_csv(OUT / "quintile_detail.csv")
    print(f"  {OUT / 'quintile_detail.csv'}")

    print("\nGenerating charts...")
    make_lorenz_chart(lorenz_all, lorenz_bus)
    make_quintile_chart(quintiles_all, quintiles_bus)

    print("\nDone.")


if __name__ == "__main__":
    main()
