# Methods: Route Ranking

## Question
Which routes are the best and worst performers? Which are improving or declining? Which are most volatile?

## Approach
- Compute per-route summary stats: mean OTP, standard deviation, min, max.
- Fit a simple linear slope (OTP vs. time) per route to quantify trend direction.
- Rank routes three ways: by average OTP, by trend slope, and by volatility (std dev).
- Flag routes with high volatility that may warrant anomaly investigation.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- route metadata
- `route_stops` -- stop count as a complexity proxy

## Output
- `output/route_ranking.csv` -- per-route summary stats and rankings
- `output/top_bottom_routes.png` -- best/worst performers chart
