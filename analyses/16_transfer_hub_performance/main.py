"""Transfer hub analysis: do high-connectivity stops have worse OTP?"""

import math

import polars as pl

from prt_otp_analysis.common import analysis_dir, correlate, query_to_polars, run_analysis, save_chart, save_csv, setup_plotting, weighted_mean

OUT = analysis_dir(__file__)


def load_data() -> tuple[pl.DataFrame, pl.DataFrame]:
    """Compute per-stop connectivity and trip-weighted OTP, plus route-level aggregation."""
    stop_route_otp = query_to_polars("""
        SELECT rs.stop_id, s.stop_name, s.lat, s.lon, s.muni,
               rs.route_id, rs.trips_wd, r.mode,
               AVG(o.otp) AS route_avg_otp
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        JOIN otp_monthly o ON rs.route_id = o.route_id
        JOIN routes r ON rs.route_id = r.route_id
        GROUP BY rs.stop_id, s.stop_name, s.lat, s.lon, s.muni,
                 rs.route_id, rs.trips_wd, r.mode
    """)

    # Per-stop: trip-weighted OTP and route count
    stop_otp = (
        stop_route_otp
        .group_by("stop_id", "stop_name", "lat", "lon", "muni")
        .agg(
            avg_otp=weighted_mean("route_avg_otp", "trips_wd"),
            n_routes=pl.col("route_id").n_unique(),
            total_trips=pl.col("trips_wd").sum(),
        )
    )
    stop_otp = stop_otp.with_columns(
        pl.when(pl.col("n_routes") >= 5).then(pl.lit("hub (5+)"))
        .when(pl.col("n_routes") >= 2).then(pl.lit("medium (2-4)"))
        .otherwise(pl.lit("simple (1)"))
        .alias("tier")
    )
    stop_otp = stop_otp.drop_nulls("avg_otp").filter(pl.col("avg_otp").is_not_nan())

    # Route-level: mean connectivity of stops on each route, plus route OTP
    route_connectivity = (
        stop_route_otp
        .group_by("route_id")
        .agg(
            pl.col("stop_id").n_unique().alias("n_stops_on_route"),
            pl.col("route_avg_otp").first().alias("route_otp"),
            pl.col("mode").first().alias("mode"),
        )
    )
    # Count distinct routes per stop, then average per route
    stop_counts = (
        stop_route_otp
        .group_by("stop_id")
        .agg(pl.col("route_id").n_unique().alias("stop_n_routes"))
    )
    route_avg_connectivity = (
        stop_route_otp.select("route_id", "stop_id")
        .unique()
        .join(stop_counts, on="stop_id", how="left")
        .group_by("route_id")
        .agg(pl.col("stop_n_routes").mean().alias("avg_stop_connectivity"))
    )
    route_level = route_connectivity.join(route_avg_connectivity, on="route_id", how="left")
    route_level = route_level.drop_nulls("route_otp").filter(pl.col("route_otp").is_not_nan())

    return stop_otp, route_level


def analyze(stop_df: pl.DataFrame, route_df: pl.DataFrame) -> dict:
    """Compute tier statistics, stop-level and route-level correlations."""
    clean = stop_df
    results = {}
    results["n_stops"] = len(clean)

    for tier in ["hub (5+)", "medium (2-4)", "simple (1)"]:
        subset = clean.filter(pl.col("tier") == tier)
        key = tier.split(" ")[0]
        results[f"{key}_n"] = len(subset)
        results[f"{key}_mean_otp"] = subset["avg_otp"].mean()
        results[f"{key}_median_otp"] = subset["avg_otp"].median()

    # Stop-level correlation (inflated n, caveat in output)
    stop_corr = correlate(clean, "n_routes", "avg_otp")
    results["stop_connectivity_r"] = stop_corr["pearson_r"]
    results["stop_connectivity_p"] = stop_corr["pearson_p"]
    results["stop_connectivity_rho"] = stop_corr["spearman_r"]
    results["stop_connectivity_rho_p"] = stop_corr["spearman_p"]

    # Route-level correlation (independent observations)
    route_corr = correlate(route_df, "avg_stop_connectivity", "route_otp")
    results["route_connectivity_r"] = route_corr["pearson_r"]
    results["route_connectivity_p"] = route_corr["pearson_p"]
    results["n_routes"] = len(route_df)

    # Bus-only route-level
    bus = route_df.filter(pl.col("mode") == "BUS")
    bus_corr = correlate(bus, "avg_stop_connectivity", "route_otp", min_n=6)
    results["bus_route_connectivity_r"] = bus_corr["pearson_r"]
    results["bus_route_connectivity_p"] = bus_corr["pearson_p"]
    results["n_bus_routes"] = bus_corr["n"]

    return results


def make_charts(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter and box plots."""
    plt = setup_plotting()

    # Connectivity vs OTP scatter
    fig, ax = plt.subplots(figsize=(10, 7))
    tier_colors = {"hub (5+)": "#ef4444", "medium (2-4)": "#f59e0b", "simple (1)": "#3b82f6"}
    for tier, color in tier_colors.items():
        subset = df.filter(pl.col("tier") == tier)
        ax.scatter(subset["n_routes"].to_list(), subset["avg_otp"].to_list(),
                   color=color, label=f"{tier} (n={len(subset)})",
                   s=15, alpha=0.4, edgecolors="none")
    ax.set_xlabel("Number of Routes Serving Stop")
    ax.set_ylabel("Trip-Weighted Average OTP")
    ax.set_title(f"Stop Connectivity vs OTP (stop-level r={results['stop_connectivity_r']:.3f}, "
                 f"route-level r={results['route_connectivity_r']:.3f})")
    ax.legend(fontsize=9)
    ax.set_ylim(0.4, 1.0)
    save_chart(fig, OUT / "connectivity_vs_otp.png")

    # Hub tier box plot
    fig, ax = plt.subplots(figsize=(8, 6))
    tiers = ["simple (1)", "medium (2-4)", "hub (5+)"]
    box_data = [df.filter(pl.col("tier") == t)["avg_otp"].to_list() for t in tiers]
    bp = ax.boxplot(box_data, tick_labels=[f"{t}\n(n={len(d)})" for t, d in zip(tiers, box_data)],
                    patch_artist=True)
    colors = ["#3b82f6", "#f59e0b", "#ef4444"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel("Trip-Weighted Average OTP")
    ax.set_title("OTP by Stop Connectivity Tier")
    save_chart(fig, OUT / "hub_tier_comparison.png")


@run_analysis(16, "Transfer Hub Performance")
def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("\nLoading data...")
    stop_df, route_df = load_data()
    print(f"  {len(stop_df)} stops with OTP and connectivity data")
    print(f"  {len(route_df)} routes with avg stop connectivity")

    print("\nAnalyzing...")
    results = analyze(stop_df, route_df)
    for tier, key in [("Hub (5+)", "hub"), ("Medium (2-4)", "medium"), ("Simple (1)", "simple")]:
        print(f"  {tier}: n={results[f'{key}_n']}, "
              f"mean OTP={results[f'{key}_mean_otp']:.1%}, "
              f"median OTP={results[f'{key}_median_otp']:.1%}")

    print(f"\n  Stop-level (n={results['n_stops']}, non-independent -- inflated power):")
    print(f"    Pearson r = {results['stop_connectivity_r']:.4f} (p = {results['stop_connectivity_p']:.4f})")
    print(f"    Spearman rho = {results['stop_connectivity_rho']:.4f} (p = {results['stop_connectivity_rho_p']:.4f})")
    print(f"\n  Route-level (n={results['n_routes']}, independent observations):")
    print(f"    Pearson r = {results['route_connectivity_r']:.4f} (p = {results['route_connectivity_p']:.4f})")
    if not math.isnan(results["bus_route_connectivity_r"]):
        print(f"\n  Route-level, bus only (n={results['n_bus_routes']}):")
        print(f"    Pearson r = {results['bus_route_connectivity_r']:.4f} "
              f"(p = {results['bus_route_connectivity_p']:.4f})")

    # Top hubs
    print("\nBusiest hubs:")
    hubs = stop_df.filter(pl.col("tier") == "hub (5+)").sort("n_routes", descending=True).head(10)
    for row in hubs.iter_rows(named=True):
        print(f"  {row['stop_name']:<40s} {row['n_routes']} routes, "
              f"OTP={row['avg_otp']:.1%}, {row['total_trips']} trips/wk")

    save_csv(stop_df, OUT / "hub_performance.csv")

    print("\nGenerating charts...")
    make_charts(stop_df, results)


if __name__ == "__main__":
    main()
