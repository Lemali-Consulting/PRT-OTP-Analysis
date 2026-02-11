"""Geographic span analysis: does route length predict OTP independently of stop count?"""

import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def compute_span(lats: list[float], lons: list[float]) -> float:
    """Return the max pairwise haversine distance (km) among a set of points."""
    max_dist = 0.0
    n = len(lats)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(lats[i], lons[i], lats[j], lons[j])
            if d > max_dist:
                max_dist = d
    return max_dist


def load_data() -> pl.DataFrame:
    """Load per-route geographic span, stop count, and average OTP."""
    stops_by_route = query_to_polars("""
        SELECT rs.route_id, s.lat, s.lon
        FROM route_stops rs
        JOIN stops s ON rs.stop_id = s.stop_id
        WHERE s.lat IS NOT NULL AND s.lon IS NOT NULL
    """)
    avg_otp = query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp, COUNT(*) AS months
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        GROUP BY o.route_id
        HAVING COUNT(*) >= 12
    """)
    stop_counts = query_to_polars("""
        SELECT route_id, COUNT(DISTINCT stop_id) AS stop_count
        FROM route_stops
        GROUP BY route_id
    """)

    # Compute geographic span per route
    spans = []
    for route_id in stops_by_route["route_id"].unique().sort().to_list():
        subset = stops_by_route.filter(pl.col("route_id") == route_id)
        lats = subset["lat"].to_list()
        lons = subset["lon"].to_list()
        span_km = compute_span(lats, lons)
        spans.append({"route_id": route_id, "span_km": span_km})

    span_df = pl.DataFrame(spans)
    df = avg_otp.join(stop_counts, on="route_id", how="inner")
    df = df.join(span_df, on="route_id", how="inner")
    df = df.with_columns(
        pl.when(pl.col("span_km") > 0)
        .then(pl.col("stop_count") / pl.col("span_km"))
        .otherwise(None)
        .alias("stop_density")
    )
    return df


def partial_corr(x: list, y: list, z: list) -> tuple[float, float]:
    """Compute partial Pearson correlation of x and y controlling for z."""
    x_arr, y_arr, z_arr = np.array(x), np.array(y), np.array(z)
    slope_xz = np.polyfit(z_arr, x_arr, 1)
    x_resid = x_arr - np.polyval(slope_xz, z_arr)
    slope_yz = np.polyfit(z_arr, y_arr, 1)
    y_resid = y_arr - np.polyval(slope_yz, z_arr)
    return stats.pearsonr(x_resid, y_resid)


def analyze(df: pl.DataFrame) -> dict:
    """Compute correlations between span, stop count, density, and OTP."""
    results = {}
    bus = df.filter(pl.col("mode") == "BUS")

    # --- Bus-only correlations (primary, avoids Simpson's paradox) ---
    r, p = stats.pearsonr(bus["span_km"].to_list(), bus["avg_otp"].to_list())
    results["bus_span_r"] = r
    results["bus_span_p"] = p
    rho, p_rho = stats.spearmanr(bus["span_km"].to_list(), bus["avg_otp"].to_list())
    results["bus_span_rho"] = rho
    results["bus_span_rho_p"] = p_rho

    # All-mode (secondary, for reference)
    r, p = stats.pearsonr(df["span_km"].to_list(), df["avg_otp"].to_list())
    results["all_span_r"] = r
    results["all_span_p"] = p

    # Stop density vs OTP (bus only, excluding zero-span routes)
    bus_dens = bus.filter(pl.col("stop_density").is_not_null())
    r, p = stats.pearsonr(bus_dens["stop_density"].to_list(), bus_dens["avg_otp"].to_list())
    results["density_r"] = r
    results["density_p"] = p

    # Partial: span vs OTP controlling for stop count (bus only)
    r, p = partial_corr(
        bus["span_km"].to_list(), bus["avg_otp"].to_list(), bus["stop_count"].to_list()
    )
    results["span_partial_r"] = r
    results["span_partial_p"] = p

    # Partial: stop count vs OTP controlling for span (bus only)
    r, p = partial_corr(
        bus["stop_count"].to_list(), bus["avg_otp"].to_list(), bus["span_km"].to_list()
    )
    results["stops_partial_r"] = r
    results["stops_partial_p"] = p

    # Span vs stop count (collinearity check)
    r, p = stats.pearsonr(bus["span_km"].to_list(), bus["stop_count"].to_list())
    results["span_stops_r"] = r

    results["n_all"] = len(df)
    results["n_bus"] = len(bus)
    return results


def make_charts(df: pl.DataFrame, results: dict) -> None:
    """Generate scatter plots for span vs OTP and density vs OTP."""
    plt = setup_plotting()
    mode_colors = {"BUS": "#3b82f6", "RAIL": "#22c55e", "INCLINE": "#f59e0b", "UNKNOWN": "#9ca3af"}

    # Span vs OTP
    fig, ax = plt.subplots(figsize=(10, 7))
    for mode, color in mode_colors.items():
        subset = df.filter(pl.col("mode") == mode)
        if len(subset) == 0:
            continue
        ax.scatter(subset["span_km"].to_list(), subset["avg_otp"].to_list(),
                   color=color, label=mode, s=40, alpha=0.7, edgecolors="white", linewidths=0.5)

    bus = df.filter(pl.col("mode") == "BUS")
    x, y = bus["span_km"].to_list(), bus["avg_otp"].to_list()
    slope, intercept = np.polyfit(x, y, 1)
    x_line = [min(x), max(x)]
    ax.plot(x_line, [slope * xi + intercept for xi in x_line],
            color="#1e40af", linewidth=1.5, linestyle="--",
            label=f"BUS trend (r={results['bus_span_r']:.3f})")
    ax.set_xlabel("Geographic Span (km)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Route Geographic Span vs On-Time Performance")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT / "span_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'span_vs_otp.png'}")

    # Density vs OTP (bus only)
    fig, ax = plt.subplots(figsize=(10, 7))
    bus_dens = bus.filter(pl.col("stop_density").is_not_null())
    ax.scatter(bus_dens["stop_density"].to_list(), bus_dens["avg_otp"].to_list(),
               color="#3b82f6", s=40, alpha=0.7, edgecolors="white", linewidths=0.5)
    x, y = bus_dens["stop_density"].to_list(), bus_dens["avg_otp"].to_list()
    slope, intercept = np.polyfit(x, y, 1)
    x_line = [min(x), max(x)]
    ax.plot(x_line, [slope * xi + intercept for xi in x_line],
            color="#1e40af", linewidth=1.5, linestyle="--",
            label=f"BUS trend (r={results['density_r']:.3f})")
    ax.set_xlabel("Stop Density (stops / km)")
    ax.set_ylabel("Average OTP")
    ax.set_title("Stop Density vs On-Time Performance (Bus Only)")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(OUT / "density_vs_otp.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved to {OUT / 'density_vs_otp.png'}")


def main() -> None:
    """Entry point: load data, analyze, chart, and save."""
    print("=" * 60)
    print("Analysis 12: Route Geographic Span vs OTP")
    print("=" * 60)

    print("\nLoading data and computing geographic spans...")
    df = load_data()
    print(f"  {len(df)} routes with span, stop count, and OTP data")

    print("\nAnalyzing correlations...")
    results = analyze(df)
    print(f"\n  Bus-only (primary):")
    print(f"    Span vs OTP:  Pearson r = {results['bus_span_r']:.4f} (p = {results['bus_span_p']:.4f})")
    print(f"                  Spearman rho = {results['bus_span_rho']:.4f} (p = {results['bus_span_rho_p']:.4f})")
    print(f"    n = {results['n_bus']} bus routes")
    print(f"\n  All-mode (secondary, Simpson's paradox risk):")
    print(f"    Span vs OTP:  Pearson r = {results['all_span_r']:.4f} (p = {results['all_span_p']:.4f})")
    print(f"    n = {results['n_all']} routes")
    print(f"\n  Density vs OTP (bus):          r = {results['density_r']:.4f} (p = {results['density_p']:.4f})")
    print(f"  Span vs OTP | stop count (bus): r = {results['span_partial_r']:.4f} (p = {results['span_partial_p']:.4f})")
    print(f"  Stops vs OTP | span (bus):      r = {results['stops_partial_r']:.4f} (p = {results['stops_partial_p']:.4f})")
    print(f"  Span-stop count collinearity:  r = {results['span_stops_r']:.4f}")

    print("\nSaving CSV...")
    df.write_csv(OUT / "geographic_span.csv")
    print(f"  Saved to {OUT / 'geographic_span.csv'}")

    print("\nGenerating charts...")
    make_charts(df, results)

    print("\nDone.")


if __name__ == "__main__":
    main()
