# Methods: Service Level vs OTP Longitudinal

## Question
Within the same route over time, does increasing or decreasing scheduled trip frequency predict OTP changes? This is a within-route panel design that controls for all time-invariant route characteristics (length, geography, mode).

## Approach
- Join `scheduled_trips_monthly` (WEEKDAY) with `otp_monthly` on (route_id, month) for the 27-month overlap (Jan 2019 -- Mar 2021).
- Compute month-over-month changes within each route: delta_trips and delta_otp.
- Remove the system-wide trend by subtracting the monthly mean delta_otp across all routes (detrending), so we isolate route-specific effects.
- Estimate a fixed-effects panel regression: detrended delta_otp ~ delta_trips, with route fixed effects (route demeaning).
- Also compute Pearson and Spearman correlations between delta_trips and detrended delta_otp.
- Stratify by mode (bus-only) and by period (pre-COVID vs post-COVID onset).
- Scatter plot: delta_trips vs detrended delta_otp, with regression line and confidence band.

## Data
- `scheduled_trips_monthly` -- WEEKDAY daily trip counts per route per month (Jan 2019 -- Mar 2021)
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode classification for bus-only stratification

## Output
- `output/service_level_panel.csv` -- route-month panel with delta_trips, delta_otp, detrended delta_otp
- `output/service_level_scatter.png` -- scatter of delta_trips vs detrended delta_otp with regression line
- `output/service_level_summary.csv` -- regression and correlation results
