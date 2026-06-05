"""Fetch the City of Pittsburgh street centerline and join to GTFS routes.

Builds the ``route_road_city`` table: for each route, the length-weighted mean
lane count of the *city* street segments its GTFS shape runs along, plus the
one-way share and limited-access (freeway) share. Unlike the PennDOT RMSSEG
overlay (state roads only), the city centerline includes local 1-2 lane streets,
so this provides an independent, broader-network measure of road width to
cross-validate Analysis 55. Reuses the KDTree spatial-match machinery from
:mod:`traffic_overlay`.
"""

import json
import sqlite3
import urllib.request
from pathlib import Path

import numpy as np

from prt_otp_analysis.traffic_overlay import (
    BUFFER_METERS,
    DATA_DIR,
    build_penndot_kdtree,
    load_gtfs_routes,
    to_local_meters,
)

DB_PATH = DATA_DIR / "prt.db"
CACHE_DIR = DATA_DIR / "pgh-centerline"
CACHE_FILE = CACHE_DIR / "centerline_raw.geojson"

# City of Pittsburgh "Pittsburgh Street Centerline" feature service, downloaded
# as GeoJSON (WGS84 / CRS84) via the ArcGIS Hub item endpoint.
DOWNLOAD_URL = (
    "https://hub.arcgis.com/api/download/v1/items/"
    "db12137760a64e86bc4ea74574c4dd30/geojson?redirect=true&layers=0&where=1=1"
)

# CFCC (Census Feature Class Code) A1x = primary highway with limited access
# (interstate / freeway / ramps). In this dataset the A2x/A3x/A4x distinctions
# are largely degenerate (A3x lumps ~88% of streets together), so only the
# limited-access flag is used; lane count carries the road-width signal.
LIMITED_ACCESS_PREFIX = "A1"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def load_centerline() -> list[dict]:
    """Load the centerline GeoJSON features from cache, downloading if absent."""
    if CACHE_FILE.exists():
        print(f"  Loading cached centerline from {CACHE_FILE}")
        return json.loads(CACHE_FILE.read_text())["features"]

    print("  Downloading Pittsburgh street centerline from ArcGIS Hub...")
    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read().decode("utf-8")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(raw)
    print(f"  Cached centerline to {CACHE_FILE}")
    return json.loads(raw)["features"]


def _to_float(value: object) -> float | None:
    """Coerce a numeric-ish value to float; None/blank/non-numeric/zero -> None.

    Lane count is coded ``0`` (and occasionally null) when unknown, so zero is
    treated as missing rather than as a real zero-lane street.
    """
    if value is None or value == "" or value == 0:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------

def parse_segments(features: list[dict]) -> list[dict]:
    """Parse centerline GeoJSON line features into matchable dicts (lat, lon order)."""
    segments: list[dict] = []
    skipped = 0
    for feat in features:
        geom = feat.get("geometry") or {}
        props = feat.get("properties", {})
        coords = geom.get("coordinates") or []
        if geom.get("type") == "MultiLineString":
            points = [(y, x) for part in coords for x, y in part]
        else:
            points = [(y, x) for x, y in coords]
        if not points:
            skipped += 1
            continue

        # Length in feet from the local-meters projection (geometry is WGS84).
        length_ft = 0.0
        for i in range(len(points) - 1):
            ax, ay = to_local_meters(*points[i])
            bx, by = to_local_meters(*points[i + 1])
            length_ft += np.hypot(ax - bx, ay - by) * 3.28084

        cfcc = (props.get("cfcc") or "").strip()
        oneway = (props.get("oneway") or "").strip().upper()
        segments.append({
            "points": points,
            "length_ft": length_ft,
            "lanes": _to_float(props.get("no_lanes")),
            "is_oneway": oneway in ("Y", "FT", "TF"),
            "is_limited_access": cfcc.startswith(LIMITED_ACCESS_PREFIX),
        })
    if skipped:
        print(f"  Skipped {skipped} features without geometry")
    with_lanes = sum(1 for s in segments if s["lanes"] is not None)
    print(f"  Parsed {len(segments)} segments ({with_lanes} with lane count)")
    return segments


def _lw(pairs: list[tuple[float, float | None]]) -> float | None:
    """Length-weighted mean of (length, value) pairs, skipping missing/zero-length."""
    good = [(length, val) for length, val in pairs if val is not None and length > 0]
    total = sum(length for length, _ in good)
    return sum(length * val for length, val in good) / total if total else None


# ---------------------------------------------------------------------------
# Spatial match & per-route aggregation
# ---------------------------------------------------------------------------

def match_routes(
    route_points: dict[str, list[tuple[float, float]]],
    segments: list[dict],
    tree,
    seg_indices: np.ndarray,
) -> list[dict]:
    """For each route, aggregate city road metrics over segments within BUFFER_METERS."""
    results = []
    for route_id, pts in sorted(route_points.items()):
        route_m = np.array([to_local_meters(lat, lon) for lat, lon in pts])
        n_route_pts = len(route_m)
        neighbors = tree.query_ball_point(route_m, r=BUFFER_METERS)

        matched_pts = sum(1 for n in neighbors if n)
        match_rate = matched_pts / n_route_pts if n_route_pts else 0.0
        seg_set = {int(seg_indices[i]) for n in neighbors for i in n}

        if not seg_set:
            results.append({
                "route_id": route_id, "n_segments": 0, "total_length_ft": 0.0,
                "weighted_lanes": None, "oneway_share": None, "limited_access_share": None,
                "n_route_points": n_route_pts, "match_rate": match_rate,
            })
            continue

        matched = [segments[i] for i in seg_set]
        total_length = sum(s["length_ft"] for s in matched)
        ow_length = sum(s["length_ft"] for s in matched if s["is_oneway"])
        la_length = sum(s["length_ft"] for s in matched if s["is_limited_access"])

        results.append({
            "route_id": route_id,
            "n_segments": len(seg_set),
            "total_length_ft": total_length,
            "weighted_lanes": _lw([(s["length_ft"], s["lanes"]) for s in matched]),
            "oneway_share": (ow_length / total_length) if total_length else None,
            "limited_access_share": (la_length / total_length) if total_length else None,
            "n_route_points": n_route_pts,
            "match_rate": match_rate,
        })
    return results


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def write_to_db(results: list[dict]) -> None:
    """Write the route_road_city table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS route_road_city")
    conn.execute("""
        CREATE TABLE route_road_city (
            route_id             TEXT PRIMARY KEY,
            n_segments           INTEGER NOT NULL,
            total_length_ft      REAL NOT NULL,
            weighted_lanes       REAL,
            oneway_share         REAL,
            limited_access_share REAL,
            n_route_points       INTEGER NOT NULL,
            match_rate           REAL NOT NULL
        )
    """)
    conn.executemany(
        """INSERT INTO route_road_city
           (route_id, n_segments, total_length_ft, weighted_lanes, oneway_share,
            limited_access_share, n_route_points, match_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["route_id"], r["n_segments"], r["total_length_ft"],
                r["weighted_lanes"], r["oneway_share"], r["limited_access_share"],
                r["n_route_points"], r["match_rate"],
            )
            for r in results
        ],
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM route_road_city").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to route_road_city in {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: load centerline, match to routes, write route_road_city."""
    print("=" * 60)
    print("City of Pittsburgh Street-Centerline Overlay")
    print("=" * 60)

    print("\n1. Loading street centerline...")
    features = load_centerline()
    segments = parse_segments(features)

    print("\n2. Loading GTFS route shapes...")
    route_points = load_gtfs_routes()

    print("\n3. Building spatial index and matching...")
    tree, _coords, seg_indices = build_penndot_kdtree(segments)
    results = match_routes(route_points, segments, tree, seg_indices)

    print("\n4. Writing to database...")
    write_to_db(results)

    # Verification
    matched = [r for r in results if r["n_segments"] > 0]
    covered = [r for r in matched if r["match_rate"] >= 0.3 and r["weighted_lanes"]]
    print("\n--- Verification ---")
    print(f"  {len(matched)} routes matched, {len(covered)} with match_rate>=0.3 and lanes")
    rates = [r["match_rate"] for r in results]
    print(f"  Median match rate (all routes): {np.median(rates):.1%}")
    print("\n  Top 10 routes by weighted lane count (city network):")
    top = sorted(
        (r for r in covered), key=lambda r: r["weighted_lanes"], reverse=True,
    )[:10]
    print(f"  {'Route':<10s} {'Lanes':>7s} {'1way%':>7s} {'Match':>7s}")
    for r in top:
        print(f"  {r['route_id']:<10s} {r['weighted_lanes']:>7.2f} "
              f"{(r['oneway_share'] or 0):>6.0%} {r['match_rate']:>7.1%}")
    print("\nDone.")


if __name__ == "__main__":
    main()
