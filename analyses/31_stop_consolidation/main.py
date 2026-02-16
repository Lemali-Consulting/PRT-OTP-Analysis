"""Identify low-usage bus stops that are candidates for consolidation to improve OTP."""

import math
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from prt_otp_analysis.common import output_dir, query_to_polars, setup_plotting

HERE = Path(__file__).resolve().parent
OUT = output_dir(HERE)
DATA_DIR = HERE.parents[1] / "data"

USAGE_THRESHOLD = 5      # avg daily ons+offs below this = low-usage
WALK_DISTANCE_M = 400    # max walk distance to nearest neighbor


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the distance in metres between two lat/lon points."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_stop_usage() -> pl.DataFrame:
    """Load pre-pandemic weekday stop-route usage from the WPRDC CSV."""
    csv_path = DATA_DIR / "bus-stop-usage" / "wprdc_stop_data.csv"
    df = pl.read_csv(csv_path, null_values=["NA", ""])
    # Keep pre-pandemic weekday rows only
    df = df.filter(
        (pl.col("time_period") == "Pre-pandemic")
        & (pl.col("serviceday") == "Weekday")
    )
    # Average across the two pre-pandemic datekeys (201909, 202001)
    usage = (
        df.group_by(["stop_id", "route_name"])
        .agg(
            pl.col("avg_ons").mean().alias("avg_ons"),
            pl.col("avg_offs").mean().alias("avg_offs"),
            pl.col("latitude").first().alias("lat"),
            pl.col("longitude").first().alias("lon"),
            pl.col("stop_name").first().alias("stop_name"),
        )
        .with_columns(
            (pl.col("avg_ons") + pl.col("avg_offs")).alias("avg_daily_usage")
        )
    )
    return usage


def load_route_otp() -> pl.DataFrame:
    """Load average OTP and stop count per route from the database."""
    return query_to_polars("""
        SELECT o.route_id, r.route_name, r.mode,
               AVG(o.otp) AS avg_otp,
               COUNT(DISTINCT rs.stop_id) AS stop_count
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        LEFT JOIN route_stops rs ON o.route_id = rs.route_id
        GROUP BY o.route_id
        HAVING COUNT(DISTINCT o.month) >= 12
    """)


def get_otp_slope() -> float:
    """Compute the OTP ~ stop_count regression slope (bus-only) from DB data."""
    df = query_to_polars("""
        SELECT o.route_id, r.mode,
               AVG(o.otp) AS avg_otp,
               COUNT(DISTINCT rs.stop_id) AS stop_count
        FROM otp_monthly o
        JOIN routes r ON o.route_id = r.route_id
        LEFT JOIN route_stops rs ON o.route_id = rs.route_id
        GROUP BY o.route_id
        HAVING COUNT(DISTINCT o.month) >= 12
    """)
    bus = df.filter(pl.col("mode") == "BUS")
    lr = stats.linregress(bus["stop_count"].to_list(), bus["avg_otp"].to_list())
    return lr.slope


def find_candidates(usage: pl.DataFrame) -> pl.DataFrame:
    """Flag low-usage stops with a same-route neighbor within walk distance."""
    # Mark low-usage
    usage = usage.with_columns(
        (pl.col("avg_daily_usage") < USAGE_THRESHOLD).alias("low_usage")
    )

    # For each stop-route, find nearest neighbor on the same route
    rows = usage.to_dicts()
    # Build route -> list of (stop_id, lat, lon)
    route_stops: dict[str, list[tuple[str, float, float]]] = {}
    for r in rows:
        route_stops.setdefault(r["route_name"], []).append(
            (r["stop_id"], r["lat"], r["lon"])
        )

    nearest_dist = []
    for r in rows:
        siblings = route_stops[r["route_name"]]
        min_d = float("inf")
        for sid, slat, slon in siblings:
            if sid == r["stop_id"]:
                continue
            d = haversine_m(r["lat"], r["lon"], slat, slon)
            if d < min_d:
                min_d = d
        nearest_dist.append(min_d if min_d != float("inf") else None)

    usage = usage.with_columns(
        pl.Series("nearest_neighbor_m", nearest_dist)
    )

    # Candidate = low usage AND neighbor within walk distance
    usage = usage.with_columns(
        (
            pl.col("low_usage")
            & pl.col("nearest_neighbor_m").is_not_null()
            & (pl.col("nearest_neighbor_m") <= WALK_DISTANCE_M)
        ).alias("candidate")
    )
    return usage


def route_summary(candidates: pl.DataFrame, route_otp: pl.DataFrame, slope: float) -> pl.DataFrame:
    """Build per-route consolidation summary with estimated OTP gain."""
    # Count candidates per route (using route_name from CSV = route_id in DB)
    per_route = (
        candidates.group_by("route_name")
        .agg(
            pl.col("candidate").sum().alias("n_candidates"),
            pl.len().alias("n_stops_csv"),
        )
    )

    # CSV route_name (e.g. "69") corresponds to DB route_id
    merged = per_route.join(
        route_otp,
        left_on="route_name",
        right_on="route_id",
        how="inner",
    )

    merged = merged.with_columns(
        (pl.col("stop_count") - pl.col("n_candidates")).alias("projected_stops"),
        # slope is negative, removing stops means multiplying removed count by -slope
        (-slope * pl.col("n_candidates")).alias("est_otp_gain"),
    )

    return merged.sort("est_otp_gain", descending=True)


def make_charts(candidates: pl.DataFrame, summary: pl.DataFrame) -> None:
    """Generate bar chart of OTP gains and scatter map of candidate stops."""
    plt = setup_plotting()

    # --- Bar chart: top 20 routes by estimated OTP gain ---
    top = summary.filter(pl.col("n_candidates") > 0).sort("est_otp_gain", descending=True).head(20)
    if len(top) == 0:
        print("  No routes with candidates -- skipping bar chart.")
        return

    fig, ax = plt.subplots(figsize=(12, 7))
    labels = top["route_name"].to_list()
    gains = [g * 100 for g in top["est_otp_gain"].to_list()]  # convert to pp
    n_cands = top["n_candidates"].to_list()
    bars = ax.barh(range(len(labels)), gains, color="#3b82f6", edgecolor="white")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([f"{lbl}  ({n} stops)" for lbl, n in zip(labels, n_cands)], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Estimated OTP Gain (percentage points)")
    ax.set_title("Top 20 Routes: Estimated OTP Improvement from Stop Consolidation")
    for bar, val in zip(bars, gains):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"+{val:.1f} pp", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "otp_gain_by_route.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'otp_gain_by_route.png'}")

    # --- Scatter map of candidate stops ---
    cand_only = candidates.filter(pl.col("candidate"))
    non_cand = candidates.filter(~pl.col("candidate"))

    fig, ax = plt.subplots(figsize=(10, 10))
    ax.scatter(
        non_cand["lon"].to_list(), non_cand["lat"].to_list(),
        s=4, alpha=0.15, color="#94a3b8", label=f"Retained ({len(non_cand):,})", zorder=1,
    )
    sc = ax.scatter(
        cand_only["lon"].to_list(), cand_only["lat"].to_list(),
        s=12, c=cand_only["avg_daily_usage"].to_list(), cmap="YlOrRd_r",
        edgecolors="black", linewidths=0.3, alpha=0.8,
        label=f"Candidates ({len(cand_only):,})", zorder=2,
    )
    plt.colorbar(sc, ax=ax, label="Avg Daily Usage (ons+offs)", shrink=0.6)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Stop Consolidation Candidates (low usage + neighbor < 400 m)")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "candidate_map.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {OUT / 'candidate_map.png'}")


def main() -> None:
    """Entry point: load data, find candidates, estimate OTP gains, chart."""
    print("=" * 60)
    print("Analysis 31: Stop Consolidation Candidates")
    print("=" * 60)

    print("\nLoading stop-level usage (pre-pandemic weekday)...")
    usage = load_stop_usage()
    print(f"  {len(usage):,} stop-route combinations")

    print("\nLoading route OTP and stop counts from DB...")
    route_otp = load_route_otp()
    print(f"  {len(route_otp)} routes with OTP data")

    print("\nComputing OTP ~ stop_count regression slope (bus-only)...")
    slope = get_otp_slope()
    print(f"  Slope = {slope:.6f} OTP per stop (i.e., {slope * 100:.3f} pp per stop)")

    print("\nIdentifying consolidation candidates...")
    candidates = find_candidates(usage)
    n_low = candidates.filter(pl.col("low_usage")).shape[0]
    n_cand = candidates.filter(pl.col("candidate")).shape[0]
    print(f"  {n_low:,} low-usage stop-route pairs (< {USAGE_THRESHOLD} daily ons+offs)")
    print(f"  {n_cand:,} consolidation candidates (low usage + neighbor <= {WALK_DISTANCE_M} m)")

    print("\nBuilding route summary...")
    summary = route_summary(candidates, route_otp, slope)
    routes_with_cand = summary.filter(pl.col("n_candidates") > 0)
    print(f"  {len(routes_with_cand)} routes have at least one candidate")
    if len(routes_with_cand) > 0:
        total_cand = routes_with_cand["n_candidates"].sum()
        avg_gain = routes_with_cand["est_otp_gain"].mean() * 100
        max_gain = routes_with_cand["est_otp_gain"].max() * 100
        print(f"  Total candidates across routes: {total_cand}")
        print(f"  Avg estimated OTP gain: +{avg_gain:.1f} pp")
        print(f"  Max estimated OTP gain: +{max_gain:.1f} pp")

    print("\nSaving CSVs...")
    candidates.write_csv(OUT / "consolidation_candidates.csv")
    print(f"  Saved {OUT / 'consolidation_candidates.csv'}")
    summary.write_csv(OUT / "route_consolidation_summary.csv")
    print(f"  Saved {OUT / 'route_consolidation_summary.csv'}")

    print("\nGenerating charts...")
    make_charts(candidates, summary)

    print("\nDone.")


if __name__ == "__main__":
    main()
