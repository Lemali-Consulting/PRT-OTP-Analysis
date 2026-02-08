# Methods: Neighborhood Equity

## Question
Are certain neighborhoods or municipalities systematically underserved by on-time performance?

## Approach
- Join `route_stops` to `stops` to get neighborhood/municipality per route-stop pair.
- For each neighborhood, compute the average OTP of the routes serving it (weighted by trips through that neighborhood).
- Rank neighborhoods by service quality.
- Examine whether the gap between best- and worst-served areas is widening or narrowing over time.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- links routes to stops with trip counts
- `stops` -- neighborhood and municipality for each stop

## Output
- `output/neighborhood_otp.csv` -- OTP aggregated by neighborhood
- `output/neighborhood_equity.png` -- geographic distribution chart
