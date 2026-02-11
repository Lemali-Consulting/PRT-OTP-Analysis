# Methods: Anomaly Investigation

## Question
What explains sharp OTP deviations (both drops and spikes) for routes across the system? Are they real performance issues or data artifacts?

## Approach
- For each route, flag months where OTP deviates more than 2 standard deviations from the route's rolling 12-month mean (two-sided: both positive and negative deviations).
- Use a lagged rolling window (current month excluded from baseline) to prevent self-dampening of z-scores.
- Guard against division by zero: when rolling standard deviation is near zero (< 1e-9), set z-score to 0.0.
- Catalog all flagged anomalies with route, month, OTP value, and deviation magnitude.
- Cross-reference known events: COVID shutdowns (Mar 2020), PRT service restructurings, construction projects.
- Report anomaly rates stratified by mode (BUS, RAIL, UNKNOWN).
- Compare actual anomaly count to the expected false-positive rate under normality (~4.6% for a 2-sigma two-sided threshold).
- Routes with fewer than 7 months of data are excluded from anomaly detection due to the rolling window requirement (shift + min_samples=6).

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- route metadata

## Output
- `output/anomalies.csv` -- all flagged anomaly months
- `output/anomaly_profiles.png` -- time series for routes with most anomalies
