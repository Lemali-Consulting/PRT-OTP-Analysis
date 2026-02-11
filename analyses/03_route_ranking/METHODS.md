# Methods: Route Ranking

## Question
Which routes are the best and worst performers? Which are improving or declining? Which are most volatile?

## Approach
- Compute per-route summary stats: mean OTP, standard deviation, min, max.
- Compute trailing 12-month average OTP as "recent performance" metric.
- Fit a simple linear slope (OTP vs. time) per route **for the post-2022 period only** (`POST_COVID_START = "2022-01"`) to quantify recent trend direction without COVID distortion. Slopes are computed via `scipy.stats.linregress`, which provides standard errors.
- For each slope, compute a 95% confidence interval and flag whether it is statistically significant (CI excludes zero).
- A zero-variance guard prevents division-by-zero when all observations fall in the same month.
- Compute actual observation span (first-to-last month range) alongside observation count to identify routes with narrow windows.
- Rank routes three ways: by recent average OTP, by trend slope, and by volatility (std dev). Rankings are computed both overall and **within mode** (BUS, RAIL, etc.).
- Flag routes with high volatility that may warrant anomaly investigation.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- route metadata (name, mode)
- `route_stops` -- stop count as a complexity proxy (5 routes lack entries in this table)

## Output
- `output/route_ranking.csv` -- per-route summary stats, slopes with SEs/CIs, overall and within-mode rankings
- `output/top_bottom_routes.png` -- best/worst performers chart
