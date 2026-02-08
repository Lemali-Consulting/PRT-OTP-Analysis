# Methods: Stop Count vs OTP

## Question
Do routes with more stops have worse on-time performance? Each stop is another opportunity to fall behind schedule.

## Approach
- Count distinct stops per route from `route_stops`.
- Compute average OTP per route from `otp_monthly`.
- Create a scatter plot of stop count vs average OTP, colored by mode.
- Compute Pearson correlation coefficient.
- Fit a simple linear regression line.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- stop count per route
- `routes` -- mode classification

## Output
- `output/stop_count_otp.csv` -- per-route stop count and average OTP
- `output/stop_count_vs_otp.png` -- scatter plot with regression line
