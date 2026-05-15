# Findings: Signal Overlay ETL

## Summary
Route-level traffic signal exposure metrics are computed from OpenStreetMap
traffic-signal nodes and written to `prt.db`.

## Notes
- Each route's signal count is the number of unique signals within 30 m of its
  densified GTFS shape; `signal_density` divides this by the route's longest
  shape length.
- Matching diagnostics include `n_route_points` and `match_rate`.
- Cached Overpass responses are reused when available.
