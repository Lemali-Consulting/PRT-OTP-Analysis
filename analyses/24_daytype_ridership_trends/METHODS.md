# Methods: Weekday vs Weekend Ridership Trends

## Question
How have weekday, Saturday, and Sunday ridership patterns changed over time, and does the weekend-to-weekday ridership ratio correlate with OTP?

## Approach
- Compute system-wide total ridership by day_type (WEEKDAY, SAT., SUN.) per month using `avg_riders * day_count` to estimate total monthly riders.
- Index each series to Jan 2019 = 100 to show relative recovery trends.
- Compute per-route weekend-to-weekday ridership ratio (Saturday + Sunday avg_riders divided by weekday avg_riders, averaged over all months with all three day types present) and correlate with route-level average OTP.
- Test whether routes with higher weekend ridership share have different OTP (Pearson, Spearman).
- Plot the weekend share trend over time system-wide: weekend share = (SAT total riders + SUN total riders) / (WEEKDAY + SAT + SUN total riders).

## Data
- `ridership_monthly`: route_id, month, day_type, avg_riders, day_count
- `otp_monthly`: route_id, month, otp (for correlation with weekend share)
- All day types used for ridership trends; overlap period (Jan 2019 -- Oct 2024) for OTP correlation.

## Output
- `output/daytype_ridership_trend.png` -- indexed ridership by day type over time
- `output/weekend_share_trend.png` -- weekend ridership share over time
- `output/weekend_share_vs_otp.png` -- scatter of weekend share vs route OTP
- `output/daytype_summary.csv` -- monthly ridership by day type
