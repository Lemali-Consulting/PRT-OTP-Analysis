# Methods: Passenger-Weighted Delay Burden

## Question
Which routes impose the largest total delay burden on riders, accounting for both OTP and ridership volume?

## Approach
- Join monthly OTP with monthly weekday ridership by route and month.
- Compute monthly late rider-trips per route: `avg_riders * day_count * (1 - otp)` where otp is on a 0--1 scale.
- Rank routes by total and average monthly late rider-trips.
- Compute system-wide monthly late rider-trips and plot the trend over time.
- Identify the top 10 routes by cumulative late rider-trips -- these are where interventions would affect the most people.
- Compare the "worst by rate" (lowest OTP) with "worst by burden" (most late rider-trips) to show how ridership weighting shifts priorities.

## Data
- `otp_monthly`: route_id, month, otp
- `ridership_monthly`: route_id, month, day_type='WEEKDAY', avg_riders, day_count
- `routes`: route_id, route_name
- Join on route_id and month; overlap period only (Jan 2019 -- Oct 2024).

## Output
- `output/delay_burden_ranking.csv` -- routes ranked by total late rider-trips
- `output/delay_burden_trend.png` -- system-wide monthly late rider-trips
- `output/rate_vs_burden.png` -- scatter comparing OTP rank with delay burden rank
- `output/top10_burden.png` -- bar chart of top 10 routes by late rider-trips
