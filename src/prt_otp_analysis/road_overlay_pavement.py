"""Fetch SPC's NHS pavement-condition layer and join to GTFS routes.

Builds the ``route_road_pavement`` table: for each route, the length-weighted
mean pavement roughness (IRI, the International Roughness Index) of the National
Highway System segments its GTFS shape runs along, plus the length-weighted
overall pavement index (OPI) and the share of length rated POOR. Unlike the
PennDOT RMSSEG (Analysis 55) and city-centerline (Analysis 56) overlays -- which
measure road *geometry* (lane count, functional class) -- this captures road
*quality*, a distinct attribute not present in either. Reuses the KDTree
spatial-match machinery from :mod:`traffic_overlay`.
"""

import json
import sqlite3
import urllib.parse
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
CACHE_DIR = DATA_DIR / "spc-pavement"
CACHE_FILE = CACHE_DIR / "pavement_raw.geojson"

# SPC "PM2_Roadways" (NHS_Pavement_Condition) feature service. Queried as GeoJSON
# in WGS84, paged 1000 features at a time, filtered to segments with a real IRI.
SERVICE_URL = (
    "https://services3.arcgis.com/MV5wh5WkCMqlwISp/arcgis/rest/services/"
    "PM2_Roadways/FeatureServer/0/query"
)
OUT_FIELDS = "ROUGH_INDX,OVERALL_PV,IRI_RATING,LANE_CNT,STREET_NAM"
PAGE_SIZE = 1000

# IRI_RATING value treated as poor pavement when computing poor_share.
POOR_RATING = "POOR"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def load_pavement() -> list[dict]:
    """Load the NHS pavement GeoJSON features from cache, downloading if absent."""
    if CACHE_FILE.exists():
        print(f"  Loading cached pavement layer from {CACHE_FILE}")
        return json.loads(CACHE_FILE.read_text())["features"]

    print("  Downloading SPC NHS pavement-condition layer from ArcGIS...")
    feats: list[dict] = []
    offset = 0
    while True:
        params = {
            "where": "ROUGH_INDX>0",
            "outFields": OUT_FIELDS,
            "outSR": "4326",
            "f": "geojson",
            "resultOffset": str(offset),
            "resultRecordCount": str(PAGE_SIZE),
        }
        url = SERVICE_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            batch = json.loads(resp.read().decode("utf-8")).get("features", [])
        feats.extend(batch)
        print(f"    fetched {len(feats)} features...")
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    print(f"  Cached pavement layer to {CACHE_FILE}")
    return feats


def _to_float(value: object) -> float | None:
    """Coerce a numeric-ish value to float; None/blank/non-positive -> None.

    OPI and IRI are coded ``0`` when unmeasured, so zero is treated as missing
    rather than as a real smooth/perfect-condition reading.
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
    """Parse pavement GeoJSON line features into matchable dicts (lat, lon order)."""
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
        if len(points) < 2:
            skipped += 1
            continue

        # Length in feet from the local-meters projection (geometry is WGS84).
        length_ft = 0.0
        for i in range(len(points) - 1):
            ax, ay = to_local_meters(*points[i])
            bx, by = to_local_meters(*points[i + 1])
            length_ft += np.hypot(ax - bx, ay - by) * 3.28084

        rating = (props.get("IRI_RATING") or "").strip().upper()
        segments.append({
            "points": points,
            "length_ft": length_ft,
            "iri": _to_float(props.get("ROUGH_INDX")),
            "opi": _to_float(props.get("OVERALL_PV")),
            "is_poor": rating == POOR_RATING,
        })
    if skipped:
        print(f"  Skipped {skipped} features without usable geometry")
    with_iri = sum(1 for s in segments if s["iri"] is not None)
    print(f"  Parsed {len(segments)} segments ({with_iri} with IRI)")
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
    """For each route, aggregate pavement metrics over segments within BUFFER_METERS."""
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
                "weighted_iri": None, "weighted_opi": None, "poor_share": None,
                "n_route_points": n_route_pts, "match_rate": match_rate,
            })
            continue

        matched = [segments[i] for i in seg_set]
        total_length = sum(s["length_ft"] for s in matched)
        iri_length = sum(s["length_ft"] for s in matched if s["iri"] is not None)
        poor_length = sum(s["length_ft"] for s in matched if s["is_poor"] and s["iri"] is not None)

        results.append({
            "route_id": route_id,
            "n_segments": len(seg_set),
            "total_length_ft": total_length,
            "weighted_iri": _lw([(s["length_ft"], s["iri"]) for s in matched]),
            "weighted_opi": _lw([(s["length_ft"], s["opi"]) for s in matched]),
            "poor_share": (poor_length / iri_length) if iri_length else None,
            "n_route_points": n_route_pts,
            "match_rate": match_rate,
        })
    return results


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def write_to_db(results: list[dict]) -> None:
    """Write the route_road_pavement table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS route_road_pavement")
    conn.execute("""
        CREATE TABLE route_road_pavement (
            route_id        TEXT PRIMARY KEY,
            n_segments      INTEGER NOT NULL,
            total_length_ft REAL NOT NULL,
            weighted_iri    REAL,
            weighted_opi    REAL,
            poor_share      REAL,
            n_route_points  INTEGER NOT NULL,
            match_rate      REAL NOT NULL
        )
    """)
    conn.executemany(
        """INSERT INTO route_road_pavement
           (route_id, n_segments, total_length_ft, weighted_iri, weighted_opi,
            poor_share, n_route_points, match_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["route_id"], r["n_segments"], r["total_length_ft"],
                r["weighted_iri"], r["weighted_opi"], r["poor_share"],
                r["n_route_points"], r["match_rate"],
            )
            for r in results
        ],
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM route_road_pavement").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to route_road_pavement in {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: load pavement layer, match to routes, write route_road_pavement."""
    print("=" * 60)
    print("SPC NHS Pavement-Condition Overlay")
    print("=" * 60)

    print("\n1. Loading NHS pavement layer...")
    features = load_pavement()
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
    covered = [r for r in matched if r["match_rate"] >= 0.3 and r["weighted_iri"]]
    print("\n--- Verification ---")
    print(f"  {len(matched)} routes matched, {len(covered)} with match_rate>=0.3 and IRI")
    rates = [r["match_rate"] for r in results]
    print(f"  Median match rate (all routes): {np.median(rates):.1%}")
    print("\n  Roughest 10 routes by length-weighted IRI:")
    top = sorted((r for r in covered), key=lambda r: r["weighted_iri"], reverse=True)[:10]
    print(f"  {'Route':<10s} {'IRI':>7s} {'Poor%':>7s} {'Match':>7s}")
    for r in top:
        print(f"  {r['route_id']:<10s} {r['weighted_iri']:>7.0f} "
              f"{(r['poor_share'] or 0):>6.0%} {r['match_rate']:>7.1%}")
    print("\nDone.")


if __name__ == "__main__":
    main()
