# Methods: Stop Count vs OTP

## Question
Do routes with more stops have worse on-time performance? Each stop is another opportunity to fall behind schedule.

## Approach
- Count distinct stops per route from `route_stops`.
- Compute average OTP per route from `otp_monthly`, requiring at least 12 months of data (`HAVING COUNT(*) >= 12`) to exclude routes with sparse observations.
- Create a scatter plot of stop count vs average OTP, colored by mode.
- Compute Pearson and Spearman correlation coefficients, both for all routes and for bus-only (to check for Simpson's paradox from mixing modes).
- Fit a simple linear regression line (bus-only, via `scipy.stats.linregress`).

**Note:** Stop counts come from the current `route_stops` snapshot, while OTP is averaged across all historical months. Routes that changed stop configurations over time will have a mismatch between their current stop count and the OTP values from earlier periods.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- stop count per route
- `routes` -- mode classification

## Output
- `output/stop_count_otp.csv` -- per-route stop count and average OTP
- `output/stop_count_vs_otp.png` -- scatter plot with regression line
