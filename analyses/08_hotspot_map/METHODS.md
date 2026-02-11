# Methods: Hot-Spot Map

## Question
Where do poor-performing routes cluster geographically? Are there corridor-level bottlenecks visible on a map?

## Approach
- For each stop, compute the trip-weighted average OTP of all routes serving it. This is a **derived metric** ("route-weighted OTP"): each stop inherits the average OTP of the routes serving it, weighted by trip frequency (`trips_7d`). It reflects route composition at each stop, not independently measured stop-level performance.
- Only include routes with at least 12 months of OTP data to avoid projecting noisy estimates onto the map.
- Plot stops on a lat/lon scatter plot, colored by route-weighted OTP performance.
- Use a diverging red-yellow-green colormap so low OTP areas are immediately visible.
- Display the unweighted stop-level average as a reference (note: this is unweighted across stops, not weighted by trip volume).
- Track the mode (BUS/RAIL) of routes serving each stop for context.
- Stops with null or NaN OTP (due to zero total trips or missing data) are excluded from the map.

## Data
- `otp_monthly` -- monthly OTP per route (averaged across all months, routes with < 12 months excluded)
- `route_stops` -- which stops are served by which routes, with trip counts
- `routes` -- route metadata including mode
- `stops` -- lat/lon coordinates
- GTFS `shapes.txt` and `trips.txt` -- route polyline geometries

## Output
- `output/hotspot_map.csv` -- per-stop route-weighted OTP with coordinates
- `output/hotspot_map.png` -- geographic scatter plot
- `output/hotspot_map.html` -- interactive folium map over OpenStreetMap tiles with per-stop popups
