# Methods: OTP → Ridership Causality

## Question
Does a decline in on-time performance predict subsequent ridership losses? If so, at what lag and magnitude?

## Approach
- Join monthly OTP with monthly weekday ridership by route and month over the overlap period.
- For each route, compute lagged cross-correlations between OTP and ridership at lags of 1--6 months (OTP leading ridership).
- Aggregate cross-correlations across routes (median and IQR) to identify the dominant lag.
- Run Granger causality tests (statsmodels) on routes with sufficient data (36+ months), testing whether lagged OTP improves ridership prediction beyond ridership's own autoregressive trend.
- Control for system-wide trends by detrending both series (subtract system monthly mean) before testing.
- Report the share of routes where Granger causality is significant at p < 0.05, with Bonferroni correction.

## Data
- `otp_monthly`: route_id, month, otp
- `ridership_monthly`: route_id, month, day_type='WEEKDAY', avg_riders
- Join on route_id and month; overlap period only (Jan 2019 -- Oct 2024).
- Exclude routes with fewer than 36 months of paired data.

## Output
- `output/lagged_crosscorr.png` -- median cross-correlation by lag with IQR band
- `output/granger_results.csv` -- per-route Granger test results (F-stat, p-value, optimal lag)
- `output/granger_summary.png` -- histogram of p-values across routes
