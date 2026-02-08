# Methods: Trip Frequency vs OTP

## Question
Is there a correlation between how often a route runs (trip frequency) and its on-time performance? High-frequency routes may suffer from schedule adherence issues like bunching.

## Approach
- Compute total weekday trips per route from `route_stops` (sum of `trips_wd` across all stops, used as a proxy for frequency volume).
- Compute average OTP per route from `otp_monthly`.
- Scatter plot of trip frequency vs average OTP, colored by mode.
- Compute Pearson correlation.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- trip counts (`trips_wd`, `trips_7d`)
- `routes` -- mode classification

## Output
- `output/frequency_otp.csv` -- per-route frequency and OTP summary
- `output/frequency_vs_otp.png` -- scatter plot with correlation
