"""Municipal and county equity analysis of on-time performance."""

from pathlib import Path

import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)

MIN_STOPS = 10


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Load per-municipality OTP and cross-jurisdictional route data."""
    # Trip-weighted OTP per stop via the routes that serve it
    stop_otp = query_to_polars("""
        SELECT rs.stop_id, rs.route_id, rs.trips_wd,
               s.muni, s.county,
               AVG(o.otp) AS route_avg_otp
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        JOIN otp_monthly o ON rs.route_id = o.route_id
        WHERE s.muni IS NOT NULL AND s.muni != '0'
        GROUP BY rs.stop_id, rs.route_id, rs.trips_wd, s.muni, s.county
    """)

    # Per-municipality: trip-weighted average OTP
    muni_otp = (
        stop_otp
        .with_columns((pl.col("route_avg_otp") * pl.col("trips_wd")).alias("weighted_otp"))
        .group_by("muni", "county")
        .agg(
            (pl.col("weighted_otp").sum() / pl.col("trips_wd").sum()).alias("avg_otp"),
            pl.col("stop_id").n_unique().alias("n_stops"),
            pl.col("route_id").n_unique().alias("n_routes"),
            pl.col("trips_wd").sum().alias("total_trips"),
        )
        .filter(pl.col("n_stops") >= MIN_STOPS)
        .sort("avg_otp", descending=True)
    )

    # Cross-jurisdictional routes: routes with stops in 2+ municipalities
    route_munis = query_to_polars("""
        SELECT rs.route_id, COUNT(DISTINCT s.muni) AS n_munis
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.muni IS NOT NULL AND s.muni != '0'
        GROUP BY rs.route_id
    """)
    avg_otp_by_route = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
    """)
    cross_jur = route_munis.join(avg_otp_by_route, on="route_id", how="inner")
    cross_jur = cross_jur.with_columns(
        pl.when(pl.col("n_munis") >= 2)
        .then(pl.lit("cross-jurisdictional"))
        .otherwise(pl.lit("single-municipality"))
        .alias("jurisdiction_type")
    )

    return muni_otp, cross_jur


def analyze(muni_otp: pl.DataFrame, cross_jur: pl.DataFrame) -> dict:
    """Compute summary stats and comparisons."""
    results = {}

    # Pittsburgh vs suburban
    pgh = muni_otp.filter(pl.col("muni") == "Pittsburgh")
    suburban = muni_otp.filter(pl.col("muni") != "Pittsburgh")

    if len(pgh) > 0:
        results["pgh_otp"] = pgh["avg_otp"][0]
        results["pgh_stops"] = pgh["n_stops"][0]
    results["suburban_median_otp"] = suburban["avg_otp"].median()
    results["suburban_mean_otp"] = suburban["avg_otp"].mean()
    results["n_munis"] = len(muni_otp)

    # Spread
    results["best_muni"] = muni_otp.sort("avg_otp", descending=True).head(1)["muni"][0]
    results["best_otp"] = muni_otp.sort("avg_otp", descending=True).head(1)["avg_otp"][0]
    results["worst_muni"] = muni_otp.sort("avg_otp").head(1)["muni"][0]
    results["worst_otp"] = muni_otp.sort("avg_otp").head(1)["avg_otp"][0]
    results["spread"] = results["best_otp"] - results["worst_otp"]

    # Cross-jurisdictional comparison
    cross = cross_jur.filter(pl.col("jurisdiction_type") == "cross-jurisdictional")
    single = cross_jur.filter(pl.col("jurisdiction_type") == "single-municipality")
    results["cross_mean_otp"] = cross["avg_otp"].mean()
    results["single_mean_otp"] = single["avg_otp"].mean()
    results["n_cross"] = len(cross)
    results["n_single"] = len(single)

    if len(cross) > 2 and len(single) > 2:
        t, p = stats.ttest_ind(cross["avg_otp"].to_list(), single["avg_otp"].to_list(),
                              equal_var=False)  # Welch's t-test: unequal group sizes
        results["cross_t"] = t
        results["cross_p"] = p

    return results


def make_charts(muni_otp: pl.DataFrame, cross_jur: pl.DataFrame, results: dict) -> None:
    """Generate bar charts for municipality ranking and Pittsburgh comparison."""
    plt = setup_plotting()

    # Top/bottom municipalities
    n_show = 10
    top = muni_otp.sort("avg_otp", descending=True).head(n_show)
    bottom = muni_otp.sort("avg_otp").head(n_show)
    combined = pl.concat([top, bottom.sort("avg_otp", descending=True)])
    # Remove duplicates if muni appears in both
    combined = combined.unique(subset=["muni"]).sort("avg_otp", descending=True)

    fig, ax = plt.subplots(figsize=(12, 8))
    munis = combined["muni"].to_list()
    otps = combined["avg_otp"].to_list()
    colors = ["#22c55e" if v >= 0.70 else "#f59e0b" if v >= 0.65 else "#ef4444" for v in otps]
    bars = ax.barh(range(len(munis)), otps, color=colors, edgecolor="white")
    ax.set_yticks(range(len(munis)))
    ax.set_yticklabels(munis, fontsize=8)
    ax.set_xlabel("Average OTP")
    ax.set_title(f"Top & Bottom Municipalities by OTP (min {MIN_STOPS} stops)")
    ax.set_xlim(0.4, 1.0)
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT / "top_bottom_municipalities.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'top_bottom_municipalities.png'}")

    # Pittsburgh vs suburban
    fig, ax = plt.subplots(figsize=(8, 5))
    categories = ["Pittsburgh", "Suburban\n(median)", "Suburban\n(mean)"]
    values = [
        results.get("pgh_otp", 0),
        results["suburban_median_otp"],
        results["suburban_mean_otp"],
    ]
    colors = ["#3b82f6", "#22c55e", "#22c55e"]
    ax.bar(categories, values, color=colors, edgecolor="white", width=0.5)
    ax.set_ylabel("Average OTP")
    ax.set_title("Pittsburgh vs Suburban Municipalities")
    ax.set_ylim(0.5, 0.85)
    for i, v in enumerate(values):
        ax.text(i, v + 0.005, f"{v:.1%}", ha="center", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "pittsburgh_vs_suburban.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'pittsburgh_vs_suburban.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 15: Municipal/County Equity")
    print("=" * 60)

    print("\nLoading data...")
    muni_otp, cross_jur = load_data()
    print(f"  {len(muni_otp)} municipalities with {MIN_STOPS}+ stops")

    print("\nAnalyzing...")
    results = analyze(muni_otp, cross_jur)
    print(f"  Best:  {results['best_muni']} ({results['best_otp']:.1%})")
    print(f"  Worst: {results['worst_muni']} ({results['worst_otp']:.1%})")
    print(f"  Spread: {results['spread']:.1%}")
    if "pgh_otp" in results:
        print(f"  Pittsburgh: {results['pgh_otp']:.1%} ({results['pgh_stops']} stops)")
    print(f"  Suburban median: {results['suburban_median_otp']:.1%}")
    print(f"  Cross-jurisdictional routes: {results['n_cross']} "
          f"(avg OTP={results['cross_mean_otp']:.1%})")
    print(f"  Single-municipality routes: {results['n_single']} "
          f"(avg OTP={results['single_mean_otp']:.1%})")
    if "cross_p" in results:
        print(f"  Difference t-test: t={results['cross_t']:.3f}, p={results['cross_p']:.4f}")

    print("\nSaving CSV...")
    muni_otp.write_csv(OUT / "municipal_otp.csv")
    print(f"  Saved to {OUT / 'municipal_otp.csv'}")

    print("\nGenerating charts...")
    make_charts(muni_otp, cross_jur, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
