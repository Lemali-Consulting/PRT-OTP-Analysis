# Methods: Neighborhood Equity

## Question
Are certain neighborhoods or municipalities systematically underserved by on-time performance?

## Approach
- Pre-aggregate OTP to route-level averages (`AVG(otp) GROUP BY route_id, HAVING COUNT(*) >= 12`), then join to `route_stops` and `stops`. This ensures each route contributes one weight regardless of how many months of data it has.
- Filter out `route_stops` rows with NULL `trips_7d` to avoid null-weight contamination.
- For each neighborhood, compute two OTP measures:
  - **Weighted OTP**: route-level average OTP weighted by `trips_7d` (weekly trip count per route-stop). Answers: "What OTP does the average *trip* in this neighborhood experience?"
  - **Unweighted OTP**: simple average across unique routes per neighborhood (deduplicated by route to avoid inflating routes with many stops). Answers: "What is the average reliability of *routes* serving this area?"
- Compute the gap (weighted - unweighted) per neighborhood to identify where high-frequency service over- or under-performs relative to the route average.
- **Bus-only stratification**: Repeat the weighted OTP analysis using only BUS-mode routes to check for Simpson's paradox (neighborhoods appearing well-served due to rail rather than bus performance).
- Rank neighborhoods by service quality.
- Examine whether the gap between best- and worst-served areas is widening or narrowing over time via rolling quintile assignment on monthly data.

## Data
- `otp_monthly` -- monthly OTP per route (routes with fewer than 12 months excluded)
- `route_stops` -- links routes to stops with trip counts (rows with NULL `trips_7d` excluded)
- `stops` -- neighborhood and municipality for each stop
- `routes` -- mode (BUS, RAIL) for bus-only stratification

## Output
- `output/neighborhood_otp.csv` -- OTP aggregated by neighborhood (weighted, unweighted, gap, and bus-only weighted)
- `output/neighborhood_otp_bus_only.csv` -- bus-only OTP by neighborhood
- `output/neighborhood_equity.png` -- top/bottom neighborhoods bar chart and quintile time series
- `output/weighted_vs_unweighted_otp.png` -- scatter plot comparing the two OTP measures and bar chart of the frequency-weighting effect per neighborhood
