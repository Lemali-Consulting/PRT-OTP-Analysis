# Methods: Hot-Spot Map

## Question
Where do poor-performing routes cluster geographically? Are there corridor-level bottlenecks visible on a map?

## Approach
- For each stop, compute the trip-weighted average OTP of all routes serving it.
- Plot stops on a lat/lon scatter plot, colored by OTP performance.
- Use a diverging red-yellow-green colormap so low OTP areas are immediately visible.
- Overlay the system average as a reference threshold.

## Data
- `otp_monthly` -- monthly OTP per route (averaged across all months)
- `route_stops` -- which stops are served by which routes, with trip counts
- `stops` -- lat/lon coordinates

## Output
- `output/hotspot_map.csv` -- per-stop OTP with coordinates
- `output/hotspot_map.png` -- geographic scatter plot
