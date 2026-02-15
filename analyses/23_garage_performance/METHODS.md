# Methods: Garage-Level Performance

## Question
Do PRT garages (Ross, Collier, East Liberty, West Mifflin) differ systematically in the OTP and ridership of routes they operate?

## Approach
- Join ridership data (which includes `current_garage`) with OTP data by route and month.
- Compute garage-level aggregate OTP (ridership-weighted and unweighted) and total ridership per month.
- Test for differences across garages using Kruskal-Wallis on route-level average OTP, grouped by garage.
- Plot garage-level OTP trends over time to see if garages diverge or move together.
- Control for route composition (garages may differ because they operate different types of routes, not because of operational quality) by comparing within-mode (bus-only) results.
- Fit a controlled OLS model (bus-only): base model with stop_count and span_km, then full model adding garage dummy variables (East Liberty as reference, being the largest). Use an F-test on the nested models to determine if garage dummies add significant explanatory power beyond route structure.

## Data
- `otp_monthly`: route_id, month, otp
- `ridership_monthly`: route_id, month, current_garage, day_type='WEEKDAY', avg_riders
- `routes`: route_id, mode for bus-only stratification
- `route_stops`: route_id, stop_id for stop counts
- `stops`: stop_id, lat, lon for geographic span computation
- Join on route_id and month; overlap period only (Jan 2019 -- Oct 2024).
- Exclude routes with fewer than 12 months of paired data or NULL garage.

## Output
- `output/garage_otp_trend.png` -- monthly OTP by garage
- `output/garage_boxplot.png` -- OTP distribution by garage
- `output/garage_summary.csv` -- garage-level summary statistics
