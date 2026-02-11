# Methods: Weekend vs Weekday Service Profile

## Question
Do commuter-oriented routes (high weekday, low weekend service) perform differently than all-day routes (similar weekday and weekend service)? The ratio of weekend to weekday trips signals route purpose, and since OTP is reported monthly, it likely reflects weekday-dominant measurement.

## Approach
- For each route, compute peak weekday trips (MAX trips_wd), peak Saturday trips (MAX trips_sa), and peak Sunday trips (MAX trips_su) from `route_stops`.
- Compute **weekend ratio** = (max_sa + max_su) / (2 * max_wd), representing the proportion of weekday service provided on weekends (1.0 = identical, 0 = weekday-only).
- Correlate weekend ratio with average OTP.
- Classify routes as **weekday-heavy** (ratio < 0.3), **balanced** (0.3-0.7), or **weekend-heavy** (> 0.7) and compare OTP distributions.
- Scatter plot and box plot.

## Data
- `route_stops` -- weekday, Saturday, Sunday trip counts per stop
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode and name

## Output
- `output/service_profile.csv` -- per-route trip counts, weekend ratio, and OTP
- `output/weekend_ratio_vs_otp.png` -- scatter plot
- `output/service_tier_comparison.png` -- box plot by service profile tier
