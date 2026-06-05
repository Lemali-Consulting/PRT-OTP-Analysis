"""Fetch PennDOT RMSSEG road-classification attributes and join to GTFS routes.

Builds the ``route_road_class`` table: for each route, the length-weighted mean
lane count, functional class, and posted speed of the road segments its GTFS shape
runs along, plus the share of matched length on arterials and on divided roads.
Reuses the KDTree spatial-match machinery from :mod:`traffic_overlay`.
"""

import json
import sqlite3
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

from prt_otp_analysis.traffic_overlay import (
    BUFFER_METERS,
    DATA_DIR,
    build_penndot_kdtree,
    load_gtfs_routes,
    to_local_meters,
    web_mercator_to_wgs84,
)

DB_PATH = DATA_DIR / "prt.db"
CACHE_DIR = DATA_DIR / "penndot-roadclass"
BASE_URL = "https://gis.penndot.gov/arcgis/rest/services/opendata"

# FHWA functional class <= 4 covers Interstate (1), Other Freeway/Expressway (2),
# Other Principal Arterial (3), and Minor Arterial (4). 5-7 are collectors/local.
ARTERIAL_MAX_CLASS = 4

# DIVSR_TYPE '0' means no median (undivided); any other code denotes a median.
UNDIVIDED_CODE = "0"


# ---------------------------------------------------------------------------
# ArcGIS fetch
# ---------------------------------------------------------------------------

def fetch_layer(service: str, out_fields: str, *, geometry: bool) -> list[dict]:
    """Paginate an Allegheny-County (CTY_CODE='02') ArcGIS layer, caching raw features."""
    cache_file = CACHE_DIR / f"{service}.json"
    if cache_file.exists():
        print(f"  Loading cached {service} from {cache_file}")
        return json.loads(cache_file.read_text())

    print(f"  Fetching {service} from PennDOT ArcGIS API...")
    features: list[dict] = []
    offset = 0
    while True:
        params = urllib.parse.urlencode({
            "where": "CTY_CODE='02'",
            "outFields": out_fields,
            "returnGeometry": "true" if geometry else "false",
            "outSR": "3857",
            "f": "json",
            "resultOffset": offset,
            "resultRecordCount": 1000,
        })
        url = f"{BASE_URL}/{service}/MapServer/0/query?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "PRT-OTP-Analysis/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        page = data.get("features", [])
        features.extend(page)
        print(f"    offset={offset} got={len(page)} total={len(features)}")
        if not page or not data.get("exceededTransferLimit", False):
            break
        offset += 1000

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(features))
    print(f"  Cached {len(features)} features to {cache_file}")
    return features


def _to_float(value: object) -> float | None:
    """Coerce an ArcGIS numeric-ish value to float; None/blank/non-numeric -> None."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Parsing & join of the two layers
# ---------------------------------------------------------------------------

def build_admin_index(admin_features: list[dict]) -> dict[int, list[dict]]:
    """Index roadwayadmin rows by NLF_ID for length-weighted func-class/speed lookup."""
    by_nlf: dict[int, list[dict]] = defaultdict(list)
    for feat in admin_features:
        attrs = feat["attributes"]
        nlf = attrs.get("NLF_ID")
        if nlf is None:
            continue
        by_nlf[nlf].append({
            "length_ft": _to_float(attrs.get("SEG_LNGTH_FEET")) or 0.0,
            # Prefer the FHWA functional class; fall back to the PennDOT FUNC_CLS.
            "func_cls": _to_float(attrs.get("FHWA_FUNC_CLS")) or _to_float(attrs.get("FUNC_CLS")),
            "speed": _to_float(attrs.get("SPEED_LIMIT")),
        })
    return by_nlf


def _lw(pairs: list[tuple[float, float | None]]) -> float | None:
    """Length-weighted mean of (length, value) pairs, skipping missing values/zero length."""
    good = [(length, val) for length, val in pairs if val is not None and length > 0]
    total = sum(length for length, _ in good)
    return sum(length * val for length, val in good) / total if total else None


def admin_for_nlf(by_nlf: dict[int, list[dict]], nlf: int | None) -> tuple[float | None, float | None]:
    """Length-weighted functional class and posted speed for a linear-feature id."""
    rows = by_nlf.get(nlf, []) if nlf is not None else []
    func = _lw([(r["length_ft"], r["func_cls"]) for r in rows])
    speed = _lw([(r["length_ft"], r["speed"]) for r in rows if (r["speed"] or 0) > 0])
    return func, speed


def parse_segments(seg_features: list[dict], by_nlf: dict[int, list[dict]]) -> list[dict]:
    """Parse roadwaysegments into matchable dicts carrying road-type attributes."""
    segments: list[dict] = []
    skipped = 0
    for feat in seg_features:
        attrs = feat["attributes"]
        paths = feat.get("geometry", {}).get("paths", [])
        if not paths:
            skipped += 1
            continue
        points = [web_mercator_to_wgs84(x, y) for path in paths for x, y in path]
        nlf = attrs.get("NLF_ID")
        func_cls, speed = admin_for_nlf(by_nlf, nlf)
        divsr = attrs.get("DIVSR_TYPE")
        segments.append({
            "points": points,
            "length_ft": _to_float(attrs.get("SEG_LNGTH_FEET")) or 0.0,
            "lanes": _to_float(attrs.get("LANE_CNT")),
            "func_cls": func_cls,
            "speed": speed,
            "is_divided": (divsr is not None and divsr != UNDIVIDED_CODE),
        })
    if skipped:
        print(f"  Skipped {skipped} segments without geometry")
    print(f"  Parsed {len(segments)} segments")
    return segments


# ---------------------------------------------------------------------------
# Spatial match & per-route aggregation
# ---------------------------------------------------------------------------

def match_routes(
    route_points: dict[str, list[tuple[float, float]]],
    segments: list[dict],
    tree,
    seg_indices: np.ndarray,
) -> list[dict]:
    """For each route, aggregate road-type attributes over segments within BUFFER_METERS."""
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
                "weighted_lanes": None, "weighted_func_cls": None, "weighted_speed": None,
                "arterial_share": None, "divided_share": None,
                "n_route_points": n_route_pts, "match_rate": match_rate,
            })
            continue

        matched = [segments[i] for i in seg_set]
        total_length = sum(s["length_ft"] for s in matched)

        func_length = sum(s["length_ft"] for s in matched if s["func_cls"] is not None)
        art_length = sum(
            s["length_ft"] for s in matched
            if s["func_cls"] is not None and s["func_cls"] <= ARTERIAL_MAX_CLASS
        )
        div_length = sum(s["length_ft"] for s in matched if s["is_divided"])

        results.append({
            "route_id": route_id,
            "n_segments": len(seg_set),
            "total_length_ft": total_length,
            "weighted_lanes": _lw([(s["length_ft"], s["lanes"]) for s in matched]),
            "weighted_func_cls": _lw([(s["length_ft"], s["func_cls"]) for s in matched]),
            "weighted_speed": _lw([(s["length_ft"], s["speed"]) for s in matched]),
            "arterial_share": (art_length / func_length) if func_length else None,
            "divided_share": (div_length / total_length) if total_length else None,
            "n_route_points": n_route_pts,
            "match_rate": match_rate,
        })
    return results


# ---------------------------------------------------------------------------
# Database write
# ---------------------------------------------------------------------------

def write_to_db(results: list[dict]) -> None:
    """Write the route_road_class table to prt.db (drop/recreate only this table)."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS route_road_class")
    conn.execute("""
        CREATE TABLE route_road_class (
            route_id          TEXT PRIMARY KEY,
            n_segments        INTEGER NOT NULL,
            total_length_ft   REAL NOT NULL,
            weighted_lanes    REAL,
            weighted_func_cls REAL,
            weighted_speed    REAL,
            arterial_share    REAL,
            divided_share     REAL,
            n_route_points    INTEGER NOT NULL,
            match_rate        REAL NOT NULL
        )
    """)
    conn.executemany(
        """INSERT INTO route_road_class
           (route_id, n_segments, total_length_ft, weighted_lanes, weighted_func_cls,
            weighted_speed, arterial_share, divided_share, n_route_points, match_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["route_id"], r["n_segments"], r["total_length_ft"],
                r["weighted_lanes"], r["weighted_func_cls"], r["weighted_speed"],
                r["arterial_share"], r["divided_share"], r["n_route_points"],
                r["match_rate"],
            )
            for r in results
        ],
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM route_road_class").fetchone()[0]
    conn.close()
    print(f"  Wrote {count} rows to route_road_class in {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point: fetch RMSSEG layers, match to routes, write route_road_class."""
    print("=" * 60)
    print("PennDOT RMSSEG Road-Classification Overlay")
    print("=" * 60)

    print("\n1. Fetching roadwaysegments (lanes, divider, geometry)...")
    seg_features = fetch_layer(
        "roadwaysegments",
        "OBJECTID,NLF_ID,SEG_LNGTH_FEET,LANE_CNT,DIVSR_TYPE",
        geometry=True,
    )
    print("\n2. Fetching roadwayadmin (functional class, speed limit)...")
    admin_features = fetch_layer(
        "roadwayadmin",
        "NLF_ID,SEG_LNGTH_FEET,FUNC_CLS,FHWA_FUNC_CLS,SPEED_LIMIT",
        geometry=False,
    )

    print("\n3. Parsing and joining layers on NLF_ID...")
    by_nlf = build_admin_index(admin_features)
    segments = parse_segments(seg_features, by_nlf)

    print("\n4. Loading GTFS route shapes...")
    route_points = load_gtfs_routes()

    print("\n5. Building spatial index and matching...")
    tree, _coords, seg_indices = build_penndot_kdtree(segments)
    results = match_routes(route_points, segments, tree, seg_indices)

    print("\n6. Writing to database...")
    write_to_db(results)

    # Verification
    matched = [r for r in results if r["n_segments"] > 0]
    unmatched = [r for r in results if r["n_segments"] == 0]
    print(f"\n--- Verification ---")
    print(f"  {len(matched)} routes matched, {len(unmatched)} unmatched")
    print("\n  Top 10 routes by weighted lane count:")
    top = sorted(
        (r for r in matched if r["weighted_lanes"] is not None),
        key=lambda r: r["weighted_lanes"], reverse=True,
    )[:10]
    print(f"  {'Route':<10s} {'Lanes':>7s} {'FuncCls':>8s} {'Speed':>7s} {'Match':>7s}")
    for r in top:
        print(f"  {r['route_id']:<10s} {r['weighted_lanes']:>7.2f} "
              f"{r['weighted_func_cls'] or float('nan'):>8.2f} "
              f"{r['weighted_speed'] or float('nan'):>7.1f} {r['match_rate']:>6.1%}")
    if unmatched:
        print(f"\n  Unmatched routes: {', '.join(r['route_id'] for r in unmatched)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
