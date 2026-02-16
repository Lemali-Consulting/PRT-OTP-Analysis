# Methods: Stop Consolidation Candidates

## Question
Which low-usage bus stops are candidates for consolidation, and how much OTP improvement could each route expect from fewer stops?

## Approach
- Use pre-pandemic weekday stop-level ridership (datekeys 201909 and 202001) as a stable baseline, averaging across the two periods.
- Compute average daily boardings + alightings per stop-route combination.
- Flag stops with average daily usage below a threshold (< 5 total ons+offs per weekday).
- For each low-usage stop on a route, compute haversine distance to the nearest other stop on the same route. If a neighbor exists within 400 m, the stop is a consolidation candidate (riders can walk to the next stop).
- Per route: count current stops, count candidates, compute the potential reduced stop count.
- Join with route-level OTP from `otp_monthly` and the stop-count/OTP regression slope from Analysis 07 to estimate the OTP benefit from consolidation.
- Generate per-route summary, system-wide statistics, and a chart of estimated OTP gains.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` -- stop-level boardings/alightings by route, period, and day type
- `route_stops` -- current route-stop assignments and stop locations
- `stops` -- stop coordinates (lat/lon)
- `otp_monthly` -- monthly OTP per route (for current performance baseline)
- `routes` -- route name and mode

## Output
- `output/consolidation_candidates.csv` -- per-stop detail: stop, route, usage, nearest neighbor distance, candidate flag
- `output/route_consolidation_summary.csv` -- per-route summary: current stops, candidates, projected new stop count, estimated OTP gain
- `output/otp_gain_by_route.png` -- bar chart of estimated OTP improvement per route
- `output/candidate_map.png` -- scatter map of candidate stops colored by usage
