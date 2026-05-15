"""Fetch OpenStreetMap traffic signal nodes and spatially join with GTFS routes to build route_signals table."""

import csv
import json
import math
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from scipy.spatial import KDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
GTFS_DIR = DATA_DIR / "GTFS"
CACHE_DIR = DATA_DIR / "osm-signals"
CACHE_FILE = CACHE_DIR / "traffic_signals_raw.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Allegheny County bounding box (south, west, north, east) in WGS84.
ALLEGHENY_BBOX = (40.18, -80.37, 40.68, -79.69)

# Pittsburgh approximate latitude for equirectangular projection.
PITTSBURGH_LAT_RAD = math.radians(40.44)
METERS_PER_DEG_LAT = 111_320.0
METERS_PER_DEG_LON = 111_320.0 * math.cos(PITTSBURGH_LAT_RAD)

# Spatial matching parameters.
BUFFER_METERS = 30.0
DENSIFY_SPACING_M = 15.0


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def to_local_meters(lat: float, lon: float) -> tuple[float, float]:
    """Convert lat/lon to approximate local meters (equirectangular at Pittsburgh)."""
    return lat * METERS_PER_DEG_LAT, lon * METERS_PER_DEG_LON


def densify_segment(
    points: list[tuple[float, float]], spacing_m: float,
) -> list[tuple[float, float]]:
    """Interpolate additional points along a polyline at the given spacing."""
    dense = []
    for i in range(len(points)):
        lat0, lon0 = points[i]
        dense.append((lat0, lon0))

        if i + 1 < len(points):
            lat1, lon1 = points[i + 1]
            mx0, my0 = to_local_meters(lat0, lon0)
            mx1, my1 = to_local_meters(lat1, lon1)
            dist = math.hypot(mx1 - mx0, my1 - my0)

            if dist > spacing_m:
                n_interp = int(dist / spacing_m)
                for j in range(1, n_interp + 1):
                    frac = j / (n_interp + 1)
                    lat_i = lat0 + frac * (lat1 - lat0)
                    lon_i = lon0 + frac * (lon1 - lon0)
                    dense.append((lat_i, lon_i))

    return dense


def polyline_length_km(points: list[tuple[float, float]]) -> float:
    """Return the total length in km of an ordered polyline of lat/lon points."""
    total = 0.0
    for (lat0, lon0), (lat1, lon1) in zip(points, points[1:]):
        total += haversine_km(lat0, lon0, lat1, lon1)
    return total


def signal_density(n_signals: int, length_km: float) -> float | None:
    """Return signals per route-km, or None when the route length is zero."""
    if length_km <= 0:
        return None
    return n_signals / length_km


# ---------------------------------------------------------------------------
# OpenStreetMap Overpass fetch
# ---------------------------------------------------------------------------

def fetch_overpass_signals() -> list[dict]:
    """Query the Overpass API for traffic-signal nodes in Allegheny County."""
    south, west, north, east = ALLEGHENY_BBOX
    query = (
        "[out:json][timeout:120];"
        f'node["highway"="traffic_signals"]({south},{west},{north},{east});'
        "out body;"
    )
    data_bytes = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data_bytes,
        headers={"User-Agent": "PRT-OTP-Analysis/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Overpass API returned HTTP {exc.code}; try again later "
            "(the public endpoint rate-limits)."
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Overpass API request failed: {exc.reason}") from exc

    return payload.get("elements", [])


def load_signal_data() -> list[dict]:
    """Load OSM traffic-signal elements from cache or fetch from the Overpass API."""
    if CACHE_FILE.exists():
        print(f"  Loading cached data from {CACHE_FILE}")
        with open(CACHE_FILE, "r") as f:
            elements = json.load(f)
        print(f"  {len(elements)} cached elements")
        return elements

    print("  Fetching from OpenStreetMap Overpass API...")
    elements = fetch_overpass_signals()
    print(f"  Total: {len(elements)} elements")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(elements, f)
    print(f"  Cached to {CACHE_FILE}")

    return elements


def parse_signals(elements: list[dict]) -> list[tuple[float, float]]:
    """Parse Overpass node elements into deduplicated (lat, lon) signal points."""
    seen: set[tuple[float, float]] = set()
    signals: list[tuple[float, float]] = []
    skipped = 0

    for el in elements:
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            skipped += 1
            continue
        key = (round(lat, 5), round(lon, 5))
        if key in seen:
            continue
        seen.add(key)
        signals.append((lat, lon))

    if skipped:
        print(f"  Skipped {skipped} elements (no coordinates)")
    print(f"  Parsed {len(signals)} unique traffic-signal points")
    return signals


# ---------------------------------------------------------------------------
# GTFS route geometries
# ---------------------------------------------------------------------------

def compute_route_lengths(
    shape_to_route: dict[str, str],
    shape_points: dict[str, list[tuple[float, float]]],
) -> dict[str, float]:
    """Return each route's representative length: its longest GTFS shape, in km."""
    route_length: dict[str, float] = {}
    for shape_id, pts in shape_points.items():
        route_id = shape_to_route.get(shape_id)
        if route_id is None:
            continue
        length = polyline_length_km(pts)
        if length > route_length.get(route_id, 0.0):
            route_length[route_id] = length
    return route_length


def load_gtfs_shapes_detailed() -> tuple[
    dict[str, list[tuple[float, float]]], dict[str, float]
]:
    """Load GTFS shapes, returning per-route point clouds and representative lengths.

    Returns (route_points, route_length_km). ``route_points`` is the deduplicated
    union of all shape points for a route, used for spatial matching.
    ``route_length_km`` is the length of each route's longest single shape.
    """
    # Map shape_id -> route_id via trips.txt.
    shape_to_route: dict[str, str] = {}
    trips_path = GTFS_DIR / "trips.txt"
    with open(trips_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["shape_id"]
            if sid and sid not in shape_to_route:
                shape_to_route[sid] = row["route_id"]

    print(f"  {len(shape_to_route)} unique shapes mapped to routes")

    # Read shapes.txt into ordered per-shape point lists.
    shape_rows: dict[str, list[tuple[int, float, float]]] = {}
    shapes_path = GTFS_DIR / "shapes.txt"
    with open(shapes_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["shape_id"]
            if sid not in shape_to_route:
                continue
            shape_rows.setdefault(sid, []).append((
                int(row["shape_pt_sequence"]),
                float(row["shape_pt_lat"]),
                float(row["shape_pt_lon"]),
            ))

    shape_points: dict[str, list[tuple[float, float]]] = {}
    for sid, rows in shape_rows.items():
        rows.sort(key=lambda r: r[0])
        shape_points[sid] = [(lat, lon) for _, lat, lon in rows]

    route_length_km = compute_route_lengths(shape_to_route, shape_points)

    # Build deduplicated per-route point clouds for spatial matching.
    route_points: dict[str, list[tuple[float, float]]] = {}
    for sid, pts in shape_points.items():
        route_id = shape_to_route[sid]
        route_points.setdefault(route_id, []).extend(pts)

    for route_id in route_points:
        seen: set[tuple[float, float]] = set()
        unique = []
        for lat, lon in route_points[route_id]:
            key = (round(lat, 5), round(lon, 5))
            if key not in seen:
                seen.add(key)
                unique.append((lat, lon))
        route_points[route_id] = unique

    total_pts = sum(len(v) for v in route_points.values())
    print(f"  {len(route_points)} routes with shape data")
    print(f"  {total_pts:,} total unique shape points")

    return route_points, route_length_km


# ---------------------------------------------------------------------------
# Spatial matching via KDTree
# ---------------------------------------------------------------------------

def build_signal_kdtree(
    signal_points: list[tuple[float, float]],
) -> tuple[KDTree, np.ndarray]:
    """Build a KDTree over traffic-signal points projected to local meters."""
    coords = np.array([to_local_meters(lat, lon) for lat, lon in signal_points])
    tree = KDTree(coords)
    return tree, coords


def match_routes(
    route_points: dict[str, list[tuple[float, float]]],
    route_length_km: dict[str, float],
    tree: KDTree,
) -> list[dict]:
    """For each route, count unique signals within BUFFER_METERS of its shape."""
    results = []

    for route_id, pts in sorted(route_points.items()):
        n_route_pts = len(pts)

        # match_rate: fraction of original shape points near at least one signal.
        orig_m = np.array([to_local_meters(lat, lon) for lat, lon in pts])
        orig_hits = tree.query_ball_point(orig_m, r=BUFFER_METERS)
        n_matched_pts = sum(1 for hit in orig_hits if hit)
        match_rate = n_matched_pts / n_route_pts if n_route_pts > 0 else 0.0

        # n_signals: unique signals near the densified route shape.
        dense = densify_segment(pts, DENSIFY_SPACING_M)
        dense_m = np.array([to_local_meters(lat, lon) for lat, lon in dense])
        dense_hits = tree.query_ball_point(dense_m, r=BUFFER_METERS)
        signal_set: set[int] = set()
        for hit in dense_hits:
            signal_set.update(int(i) for i in hit)
        n_signals = len(signal_set)

        length_km = route_length_km.get(route_id, 0.0)

        results.append({
            "route_id": route_id,
            "n_signals": n_signals,
            "length_km": length_km,
            "signal_density": signal_density(n_signals, length_km),
            "n_route_points": n_route_pts,
            "match_rate": match_rate,
        })

    return results


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def write_to_db(results: list[dict]) -> None:
    """Write route_signals table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS route_signals")
    conn.execute("""
        CREATE TABLE route_signals (
            route_id        TEXT PRIMARY KEY,
            n_signals       INTEGER NOT NULL,
            length_km       REAL NOT NULL,
            signal_density  REAL,
            n_route_points  INTEGER NOT NULL,
            match_rate      REAL NOT NULL
        )
    """)

    conn.executemany(
        """INSERT INTO route_signals
           (route_id, n_signals, length_km, signal_density,
            n_route_points, match_rate)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (
                r["route_id"], r["n_signals"], r["length_km"],
                r["signal_density"], r["n_route_points"], r["match_rate"],
            )
            for r in results
        ],
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM route_signals").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to route_signals table in {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: fetch OSM signals, match to routes, write to DB."""
    print("=" * 60)
    print("OpenStreetMap Traffic Signal Overlay")
    print("=" * 60)

    print("\n1. Loading OSM traffic-signal data...")
    elements = load_signal_data()
    signals = parse_signals(elements)

    print("\n2. Loading GTFS route shapes...")
    route_points, route_length_km = load_gtfs_shapes_detailed()

    print("\n3. Building spatial index...")
    tree, coords = build_signal_kdtree(signals)
    print(f"  KDTree: {len(coords):,} signal points")

    print("\n4. Matching routes to traffic signals...")
    results = match_routes(route_points, route_length_km, tree)

    print("\n5. Writing to database...")
    write_to_db(results)

    # Verification
    print("\n--- Verification ---")
    matched = [r for r in results if r["n_signals"] > 0]
    unmatched = [r for r in results if r["n_signals"] == 0]
    print(f"  {len(matched)} routes with signals, {len(unmatched)} without")

    print("\n  Top 10 routes by signal density:")
    print(f"  {'Route':<10s} {'Signals':>8s} {'Length km':>10s} "
          f"{'Sig/km':>8s} {'Match':>8s}")
    top = sorted(
        (r for r in matched if r["signal_density"] is not None),
        key=lambda r: r["signal_density"],
        reverse=True,
    )[:10]
    for r in top:
        print(f"  {r['route_id']:<10s} {r['n_signals']:>8d} "
              f"{r['length_km']:>10.1f} {r['signal_density']:>8.2f} "
              f"{r['match_rate']:>7.1%}")

    print("\n  Routes with lowest match rate (>0):")
    low_match = sorted(
        (r for r in matched if r["match_rate"] > 0),
        key=lambda r: r["match_rate"],
    )[:10]
    for r in low_match:
        print(f"  {r['route_id']:<10s} match_rate={r['match_rate']:.1%} "
              f"({r['n_signals']} signals, {r['signal_density']:.2f}/km)")

    if unmatched:
        print(f"\n  Routes with no signals: "
              f"{', '.join(r['route_id'] for r in unmatched)}")

    print("\nDone.")


if __name__ == "__main__":
    main()
