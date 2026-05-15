"""Unit tests for the traffic-signal overlay ETL pure functions."""

import pytest

from prt_otp_analysis.signal_overlay import (
    DENSIFY_SPACING_M,
    build_signal_kdtree,
    compute_route_lengths,
    densify_segment,
    haversine_km,
    match_routes,
    parse_signals,
    polyline_length_km,
    signal_density,
)


def test_haversine_km_known_distance():
    """One degree of latitude is roughly 111.2 km along a meridian."""
    assert haversine_km(0.0, 0.0, 1.0, 0.0) == pytest.approx(111.195, abs=0.5)
    # Two Pittsburgh points ~100 m apart in latitude.
    assert haversine_km(40.44, -79.99, 40.440898, -79.99) == pytest.approx(0.1, abs=0.005)


def test_parse_signals_extracts_coords():
    """parse_signals pulls (lat, lon) from Overpass node elements."""
    elements = [
        {"type": "node", "id": 1, "lat": 40.44, "lon": -79.99},
        {"type": "node", "id": 2, "lat": 40.45, "lon": -79.98},
    ]
    assert parse_signals(elements) == [(40.44, -79.99), (40.45, -79.98)]


def test_parse_signals_skips_missing_coords():
    """Elements without lat/lon are dropped, not crashed on."""
    elements = [
        {"type": "node", "id": 1, "lat": 40.44, "lon": -79.99},
        {"type": "node", "id": 2},  # no coordinates
        {"type": "node", "id": 3, "lat": 40.45},  # partial
    ]
    assert parse_signals(elements) == [(40.44, -79.99)]


def test_parse_signals_dedupes_coincident_nodes():
    """Nodes at the same rounded location collapse to a single signal."""
    elements = [
        {"type": "node", "id": 1, "lat": 40.441234, "lon": -79.991234},
        {"type": "node", "id": 2, "lat": 40.4412341, "lon": -79.9912339},
    ]
    assert parse_signals(elements) == [(40.441234, -79.991234)]


def test_densify_segment_spacing():
    """Densified polyline points are spaced no farther than the target spacing."""
    points = [(40.44, -79.99), (40.44, -79.98)]  # ~845 m apart in longitude
    dense = densify_segment(points, DENSIFY_SPACING_M)
    assert len(dense) > len(points)
    for (lat0, lon0), (lat1, lon1) in zip(dense, dense[1:]):
        gap_m = haversine_km(lat0, lon0, lat1, lon1) * 1000.0
        assert gap_m <= DENSIFY_SPACING_M + 1e-6


def test_polyline_length_km_sums_ordered_segments():
    """polyline_length_km sums great-circle distance between consecutive points."""
    points = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    assert polyline_length_km(points) == pytest.approx(222.39, abs=1.0)
    assert polyline_length_km([(0.0, 0.0)]) == 0.0


def test_compute_route_lengths_uses_longest_shape():
    """A route's length is the length of its longest GTFS shape, not the sum."""
    shape_to_route = {"short": "R1", "long": "R1", "other": "R2"}
    shape_points = {
        "short": [(0.0, 0.0), (0.5, 0.0)],
        "long": [(0.0, 0.0), (2.0, 0.0)],
        "other": [(0.0, 0.0), (1.0, 0.0)],
    }
    lengths = compute_route_lengths(shape_to_route, shape_points)
    assert lengths["R1"] == pytest.approx(polyline_length_km(shape_points["long"]))
    assert lengths["R1"] > polyline_length_km(shape_points["short"])
    assert lengths["R2"] == pytest.approx(polyline_length_km(shape_points["other"]))


def test_match_routes_dedupes_signal_near_many_route_points():
    """A single signal near many route points is counted once."""
    signal_points = [(40.44, -79.99)]
    tree, _ = build_signal_kdtree(signal_points)
    # Route points all within ~15 m of the lone signal.
    route_points = {
        "R1": [(40.44, -79.99), (40.44005, -79.99), (40.44010, -79.99)],
    }
    results = match_routes(route_points, {"R1": 0.05}, tree)
    assert len(results) == 1
    row = results[0]
    assert row["route_id"] == "R1"
    assert row["n_signals"] == 1
    assert row["n_route_points"] == 3
    assert row["match_rate"] == pytest.approx(1.0)


def test_match_routes_no_signals_in_range():
    """A route far from every signal yields zero count and zero match rate."""
    tree, _ = build_signal_kdtree([(40.44, -79.99)])
    route_points = {"R2": [(40.60, -80.20), (40.601, -80.20)]}
    results = match_routes(route_points, {"R2": 1.0}, tree)
    row = results[0]
    assert row["n_signals"] == 0
    assert row["match_rate"] == 0.0
    assert row["signal_density"] == 0.0


def test_signal_density_is_count_over_length():
    """signal_density divides count by route length; zero length yields None."""
    assert signal_density(10, 5.0) == pytest.approx(2.0)
    assert signal_density(0, 5.0) == 0.0
    assert signal_density(5, 0.0) is None
