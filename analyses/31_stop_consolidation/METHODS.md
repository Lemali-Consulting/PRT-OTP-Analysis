# Methods: Stop Consolidation Candidates

## Question
Which low-usage bus stops are candidates for consolidation, and how much OTP improvement could each route expect from fewer stops?

## Approach
- Use pre-pandemic weekday stop-level ridership (datekeys 201909 and 202001) as a stable baseline, averaging across the two periods.
- Compute average daily boardings + alightings per stop-route combination.
- Flag stops with average daily usage below a threshold (< 5 total ons+offs per weekday).
- For each low-usage stop on a route, compute haversine distance to the nearest other stop on the same route. If a neighbor exists within 400 m, the stop is a consolidation candidate (riders can walk to the next stop).
- Per route: count current stops, count candidates, compute the potential reduced stop count.
- Compute the stop-count/OTP regression slope independently (bus-only) and apply it to estimate the OTP benefit from consolidation. OTP gain estimates are produced only for bus routes; non-bus routes are included in the summary but flagged as not applicable for the bus-derived slope.
- Generate per-route summary, system-wide statistics, and a chart of estimated OTP gains.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `wprdc_stop_data.csv` | Stop-level boardings/alightings by route, period, and day type | Local CSV (`data/bus-stop-usage/`) |
| `route_stops` | Current route-stop assignments and stop locations | `prt.db` table |
| `stops` | Stop coordinates (lat/lon) | `prt.db` table |
| `otp_monthly` | Monthly OTP per route (for current performance baseline) | `prt.db` table |
| `routes` | Route name and mode | `prt.db` table |

## Output
- `output/consolidation_candidates.csv` -- per-stop detail: stop, route, usage, nearest neighbor distance, candidate flag
- `output/route_consolidation_summary.csv` -- per-route summary: current stops, candidates, projected new stop count, estimated OTP gain
- `output/otp_gain_by_route.png` -- bar chart of estimated OTP improvement per route
- `output/candidate_map.png` -- scatter map of candidate stops colored by usage
