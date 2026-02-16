"""Fetch PennDOT AADT data and spatially join with GTFS routes to build route_traffic table."""

import csv
import json
import math
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path

import numpy as np
from scipy.spatial import KDTree

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "prt.db"
GTFS_DIR = DATA_DIR / "GTFS"
CACHE_DIR = DATA_DIR / "penndot-traffic"
CACHE_FILE = CACHE_DIR / "aadt_raw.json"

API_URL = (
    "https://gis.penndot.gov/arcgis/rest/services"
    "/opendata/roadwaytraffic/MapServer/0/query"
)

# Pittsburgh approximate latitude for equirectangular projection
PITTSBURGH_LAT_RAD = math.radians(40.44)
METERS_PER_DEG_LAT = 111_320.0
METERS_PER_DEG_LON = 111_320.0 * math.cos(PITTSBURGH_LAT_RAD)

# Spatial matching parameters
BUFFER_METERS = 30.0
DENSIFY_SPACING_M = 15.0


# ---------------------------------------------------------------------------
# PennDOT API fetch
# ---------------------------------------------------------------------------

def web_mercator_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """Convert EPSG:3857 (Web Mercator) coordinates to WGS84 lat/lon."""
    lon = math.degrees(x / 6378137.0)
    lat = math.degrees(2.0 * math.atan(math.exp(y / 6378137.0)) - math.pi / 2.0)
    return lat, lon


def fetch_penndot_pages() -> list[dict]:
    """Paginate through the PennDOT ArcGIS REST API for Allegheny County segments."""
    all_features = []
    offset = 0
    page_size = 1000

    while True:
        params = urllib.parse.urlencode({
            "where": "CTY_CODE='02'",
            "outFields": "OBJECTID,CUR_AADT,TRK_PCT,SEG_LNGTH_FEET,ST_RT_NO",
            "returnGeometry": "true",
            "outSR": "3857",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        })
        url = f"{API_URL}?{params}"
        print(f"  Fetching offset={offset} ...")

        req = urllib.request.Request(url, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        print(f"    Got {len(features)} features (total: {len(all_features)})")

        if not data.get("exceededTransferLimit", False):
            break
        offset += page_size

    return all_features


def load_penndot_data() -> list[dict]:
    """Load PennDOT data from cache or fetch from API."""
    if CACHE_FILE.exists():
        print(f"  Loading cached data from {CACHE_FILE}")
        with open(CACHE_FILE, "r") as f:
            features = json.load(f)
        print(f"  {len(features)} cached features")
        return features

    print("  Fetching from PennDOT ArcGIS API...")
    features = fetch_penndot_pages()
    print(f"  Total: {len(features)} features")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(features, f)
    print(f"  Cached to {CACHE_FILE}")

    return features


def parse_penndot_segments(features: list[dict]) -> list[dict]:
    """Parse PennDOT features into segment dicts with WGS84 coordinates."""
    segments = []
    skipped = 0
    for feat in features:
        attrs = feat.get("attributes", {})
        geom = feat.get("geometry", {})
        paths = geom.get("paths", [])

        aadt = attrs.get("CUR_AADT")
        if aadt is None or aadt <= 0:
            skipped += 1
            continue
        if not paths:
            skipped += 1
            continue

        # Convert all path points to WGS84
        wgs_points = []
        for path in paths:
            for x, y in path:
                lat, lon = web_mercator_to_wgs84(x, y)
                wgs_points.append((lat, lon))

        segments.append({
            "object_id": attrs.get("OBJECTID"),
            "aadt": aadt,
            "truck_pct": attrs.get("TRK_PCT"),
            "length_ft": attrs.get("SEG_LNGTH_FEET", 0.0) or 0.0,
            "route_no": attrs.get("ST_RT_NO"),
            "points": wgs_points,
        })

    if skipped:
        print(f"  Skipped {skipped} features (no AADT or no geometry)")
    print(f"  Parsed {len(segments)} valid segments")
    return segments


# ---------------------------------------------------------------------------
# GTFS route geometries
# ---------------------------------------------------------------------------

def load_gtfs_routes() -> dict[str, list[tuple[float, float]]]:
    """Load GTFS shapes and map to route_id via trips.txt."""
    # Read trips.txt to map shape_id -> route_id
    shape_to_route: dict[str, str] = {}
    trips_path = GTFS_DIR / "trips.txt"
    with open(trips_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["shape_id"]
            rid = row["route_id"]
            if sid not in shape_to_route:
                shape_to_route[sid] = rid

    print(f"  {len(shape_to_route)} unique shapes mapped to routes")

    # Read shapes.txt
    route_points: dict[str, list[tuple[float, float]]] = {}
    shapes_path = GTFS_DIR / "shapes.txt"
    with open(shapes_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["shape_id"]
            rid = shape_to_route.get(sid)
            if rid is None:
                continue
            lat = float(row["shape_pt_lat"])
            lon = float(row["shape_pt_lon"])
            if rid not in route_points:
                route_points[rid] = []
            route_points[rid].append((lat, lon))

    # Deduplicate points per route (round to ~1m precision)
    for rid in route_points:
        seen = set()
        unique = []
        for lat, lon in route_points[rid]:
            key = (round(lat, 5), round(lon, 5))
            if key not in seen:
                seen.add(key)
                unique.append((lat, lon))
        route_points[rid] = unique

    print(f"  {len(route_points)} routes with shape data")
    total_pts = sum(len(v) for v in route_points.values())
    print(f"  {total_pts:,} total unique shape points")

    return route_points


# ---------------------------------------------------------------------------
# Spatial matching via KDTree
# ---------------------------------------------------------------------------

def to_local_meters(lat: float, lon: float) -> tuple[float, float]:
    """Convert lat/lon to approximate local meters (equirectangular at Pittsburgh)."""
    return lat * METERS_PER_DEG_LAT, lon * METERS_PER_DEG_LON


def densify_segment(points: list[tuple[float, float]], spacing_m: float) -> list[tuple[float, float]]:
    """Interpolate additional points along a polyline segment at the given spacing."""
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


def build_penndot_kdtree(
    segments: list[dict],
) -> tuple[KDTree, np.ndarray, np.ndarray]:
    """Build KDTree from densified PennDOT segment points.

    Returns (tree, point_coords_meters, point_segment_indices).
    """
    all_coords = []
    all_seg_idx = []

    for seg_idx, seg in enumerate(segments):
        dense = densify_segment(seg["points"], DENSIFY_SPACING_M)
        for lat, lon in dense:
            mx, my = to_local_meters(lat, lon)
            all_coords.append((mx, my))
            all_seg_idx.append(seg_idx)

    coords = np.array(all_coords)
    seg_indices = np.array(all_seg_idx)

    print(f"  KDTree: {len(coords):,} densified PennDOT points from {len(segments)} segments")
    tree = KDTree(coords)
    return tree, coords, seg_indices


def match_routes(
    route_points: dict[str, list[tuple[float, float]]],
    segments: list[dict],
    tree: KDTree,
    seg_indices: np.ndarray,
) -> list[dict]:
    """For each route, find PennDOT segments within BUFFER_METERS and aggregate."""
    results = []

    for route_id, pts in sorted(route_points.items()):
        # Convert route points to local meters
        route_m = np.array([to_local_meters(lat, lon) for lat, lon in pts])
        n_route_pts = len(route_m)

        # Query KDTree for nearby PennDOT points
        indices = tree.query_ball_point(route_m, r=BUFFER_METERS)

        # Collect unique matched segment indices
        matched_seg_set = set()
        n_matched_pts = 0
        for idx_list in indices:
            if idx_list:
                n_matched_pts += 1
                for idx in idx_list:
                    matched_seg_set.add(int(seg_indices[idx]))

        match_rate = n_matched_pts / n_route_pts if n_route_pts > 0 else 0.0

        if not matched_seg_set:
            results.append({
                "route_id": route_id,
                "n_segments": 0,
                "total_length_ft": 0.0,
                "weighted_aadt": 0.0,
                "max_aadt": 0,
                "median_aadt": 0.0,
                "p90_aadt": 0.0,
                "avg_truck_pct": None,
                "n_route_points": n_route_pts,
                "match_rate": match_rate,
            })
            continue

        # Aggregate over matched segments
        matched = [segments[i] for i in matched_seg_set]
        aadts = np.array([s["aadt"] for s in matched], dtype=float)
        lengths = np.array([s["length_ft"] for s in matched], dtype=float)

        total_length = float(np.sum(lengths))
        if total_length > 0:
            weighted_aadt = float(np.sum(aadts * lengths) / total_length)
        else:
            weighted_aadt = float(np.mean(aadts))

        truck_pcts = [s["truck_pct"] for s in matched if s["truck_pct"] is not None]
        if truck_pcts and total_length > 0:
            truck_lengths = np.array([
                s["length_ft"] for s in matched if s["truck_pct"] is not None
            ], dtype=float)
            truck_vals = np.array(truck_pcts, dtype=float)
            avg_truck = float(np.sum(truck_vals * truck_lengths) / np.sum(truck_lengths))
        elif truck_pcts:
            avg_truck = float(np.mean(truck_pcts))
        else:
            avg_truck = None

        results.append({
            "route_id": route_id,
            "n_segments": len(matched_seg_set),
            "total_length_ft": total_length,
            "weighted_aadt": weighted_aadt,
            "max_aadt": int(np.max(aadts)),
            "median_aadt": float(np.median(aadts)),
            "p90_aadt": float(np.percentile(aadts, 90)),
            "avg_truck_pct": avg_truck,
            "n_route_points": n_route_pts,
            "match_rate": match_rate,
        })

    return results


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def write_to_db(results: list[dict]) -> None:
    """Write route_traffic table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS route_traffic")
    conn.execute("""
        CREATE TABLE route_traffic (
            route_id        TEXT PRIMARY KEY,
            n_segments      INTEGER NOT NULL,
            total_length_ft REAL NOT NULL,
            weighted_aadt   REAL NOT NULL,
            max_aadt        INTEGER NOT NULL,
            median_aadt     REAL NOT NULL,
            p90_aadt        REAL NOT NULL,
            avg_truck_pct   REAL,
            n_route_points  INTEGER NOT NULL,
            match_rate      REAL NOT NULL
        )
    """)

    conn.executemany(
        """INSERT INTO route_traffic
           (route_id, n_segments, total_length_ft, weighted_aadt, max_aadt,
            median_aadt, p90_aadt, avg_truck_pct, n_route_points, match_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["route_id"], r["n_segments"], r["total_length_ft"],
                r["weighted_aadt"], r["max_aadt"], r["median_aadt"],
                r["p90_aadt"], r["avg_truck_pct"], r["n_route_points"],
                r["match_rate"],
            )
            for r in results
        ],
    )
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM route_traffic").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to route_traffic table in {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: fetch PennDOT data, match to routes, write to DB."""
    print("=" * 60)
    print("PennDOT Traffic Overlay")
    print("=" * 60)

    # Step 1: Load PennDOT data
    print("\n1. Loading PennDOT AADT data...")
    features = load_penndot_data()
    segments = parse_penndot_segments(features)

    aadt_values = [s["aadt"] for s in segments]
    print(f"  AADT range: {min(aadt_values):,} -- {max(aadt_values):,}")
    print(f"  AADT median: {np.median(aadt_values):,.0f}")

    # Step 2: Load GTFS route geometries
    print("\n2. Loading GTFS route shapes...")
    route_points = load_gtfs_routes()

    # Step 3: Build KDTree and match
    print("\n3. Building spatial index...")
    tree, coords, seg_indices = build_penndot_kdtree(segments)

    print("\n4. Matching routes to PennDOT segments...")
    results = match_routes(route_points, segments, tree, seg_indices)

    # Step 4: Write to DB
    print("\n5. Writing to database...")
    write_to_db(results)

    # Verification
    print("\n--- Verification ---")
    matched = [r for r in results if r["n_segments"] > 0]
    unmatched = [r for r in results if r["n_segments"] == 0]
    print(f"  {len(matched)} routes matched, {len(unmatched)} unmatched")

    print("\n  Top 10 routes by weighted AADT:")
    top = sorted(matched, key=lambda r: r["weighted_aadt"], reverse=True)[:10]
    print(f"  {'Route':<10s} {'AADT':>10s} {'Max AADT':>10s} {'Segments':>10s} {'Match':>8s}")
    for r in top:
        print(f"  {r['route_id']:<10s} {r['weighted_aadt']:>10,.0f} {r['max_aadt']:>10,d} "
              f"{r['n_segments']:>10d} {r['match_rate']:>7.1%}")

    print("\n  Routes with lowest match rate (>0):")
    low_match = sorted(
        [r for r in matched if r["match_rate"] > 0],
        key=lambda r: r["match_rate"],
    )[:10]
    for r in low_match:
        print(f"  {r['route_id']:<10s} match_rate={r['match_rate']:.1%} "
              f"({r['n_segments']} segments, AADT={r['weighted_aadt']:,.0f})")

    if unmatched:
        print(f"\n  Unmatched routes: {', '.join(r['route_id'] for r in unmatched)}")

    print("\nDone.")


if __name__ == "__main__":
    main()
