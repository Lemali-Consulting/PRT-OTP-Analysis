# Methods: Ridership-Weighted OTP

## Question
How does the average rider's on-time experience differ from the average route's OTP? Does weighting by actual ridership instead of scheduled trip frequency change the system-wide OTP picture?

## Approach
- Join monthly OTP data with monthly average weekday ridership by route and month.
- Compute three monthly system OTP series:
  1. **Unweighted**: simple mean of all route OTPs (all routes equal).
  2. **Trip-weighted**: `sum(otp_i * trips_7d_i) / sum(trips_7d_i)` using static scheduled trip counts from `route_stops` (same weight every month).
  3. **Ridership-weighted**: `sum(otp_i * avg_riders_i) / sum(avg_riders_i)` using that route's average daily weekday ridership for the same month (weight varies month-to-month).
- Plot all three series over time to visualize divergence.
- Compute summary statistics (mean, spread) for each weighting scheme.
- Test whether the ridership-weighted series is significantly different from the trip-weighted series (paired t-test or Wilcoxon).

## Data
- `otp_monthly`: route, month, otp
- `data/average-ridership/`: route, month_start, day_type='WEEKDAY', avg_riders
- `route_stops`: for trip-weighted baseline (trips_wd)
- Join on route code and month; restrict to overlap period (Jan 2019 -- Oct 2024).
- Exclude routes with fewer than 12 months of data.

## Output
- `output/ridership_weighted_otp_trend.png` -- three-series time plot
- `output/weighting_comparison.csv` -- monthly values for all three series
- `output/summary_stats.csv` -- mean, median, std for each weighting scheme
