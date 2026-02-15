# Methods: Ridership Concentration & Equity

## Question
What share of total system ridership is carried by the lowest-performing (worst OTP) routes? Is there a concentration of riders on unreliable service?

## Approach
- Compute route-level average OTP and average weekday ridership over the overlap period.
- Sort routes by OTP (worst to best) and compute cumulative ridership share.
- Plot a Lorenz-style curve: x-axis = cumulative share of routes (by OTP rank), y-axis = cumulative share of ridership. The diagonal represents perfect equality (every route carries the same ridership regardless of OTP). If the curve bows above the diagonal, ridership is concentrated on low-OTP routes.
- Compute a Gini-like concentration index: area between the Lorenz curve and the diagonal, scaled to [0, 1]. A value of 0 means ridership is uniformly distributed across OTP ranks; positive values mean riders are disproportionately on low-OTP routes.
- Identify the OTP threshold below which 50% of ridership is carried.
- Divide routes into OTP quintiles (Q1 = worst, Q5 = best) and compute each quintile's share of total ridership plus average OTP.
- Repeat all analyses for bus-only to control for mode effects.

## Data
- `otp_monthly`: route_id, month, otp
- `ridership_monthly`: route_id, month, day_type='WEEKDAY', avg_riders
- `routes`: route_id, mode
- Overlap period (Jan 2019 -- Oct 2024); exclude routes with fewer than 12 months of paired data.

## Output
- `output/ridership_lorenz.png` -- Lorenz curve of ridership vs OTP rank (all routes + bus-only)
- `output/quintile_summary.png` -- bar chart of ridership share and average OTP by quintile
- `output/equity_metrics.csv` -- Gini index, 50th-percentile OTP threshold, quintile breakdowns
