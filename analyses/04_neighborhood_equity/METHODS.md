# Methods: Neighborhood Equity

## Question
Are certain neighborhoods or municipalities systematically underserved by on-time performance?

## Approach
- Join `route_stops` to `stops` to get neighborhood/municipality per route-stop pair.
- For each neighborhood, compute two OTP measures:
  - **Weighted OTP**: average OTP weighted by `trips_7d` (weekly trip count per route-stop). Answers: "What OTP does the average *trip* in this neighborhood experience?"
  - **Unweighted OTP**: simple average across unique routes per neighborhood (deduplicated by route-month to avoid inflating routes with many stops). Answers: "What is the average reliability of *routes* serving this area?"
- Compute the gap (weighted - unweighted) per neighborhood to identify where high-frequency service over- or under-performs relative to the route average.
- Rank neighborhoods by service quality.
- Examine whether the gap between best- and worst-served areas is widening or narrowing over time via rolling quintile assignment.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- links routes to stops with trip counts
- `stops` -- neighborhood and municipality for each stop

## Output
- `output/neighborhood_otp.csv` -- OTP aggregated by neighborhood (weighted, unweighted, and gap)
- `output/neighborhood_equity.png` -- top/bottom neighborhoods bar chart and quintile time series
- `output/weighted_vs_unweighted_otp.png` -- scatter plot comparing the two OTP measures and bar chart of the frequency-weighting effect per neighborhood
