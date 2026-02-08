# Methods: Seasonal Patterns

## Question
Do PRT routes exhibit consistent seasonal OTP patterns? Are summer or winter months systematically better or worse?

## Approach
- For each route, compute a month-of-year average OTP (Jan avg, Feb avg, etc.) across all available years.
- Compute a system-wide seasonal profile by averaging across routes (trip-weighted).
- Measure seasonal amplitude: max(month-of-year avg) - min(month-of-year avg) per route.
- Decompose into trend + seasonal + residual using a moving-average approach:
  1. Trend = 12-month centered rolling mean
  2. Seasonal = month-of-year mean of (OTP - trend)
  3. Residual = OTP - trend - seasonal
- Rank routes by seasonal amplitude to identify those most affected by seasons.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- trip counts for weighting
- `routes` -- route metadata

## Output
- `output/seasonal_patterns.csv` -- month-of-year seasonal profile per route
- `output/seasonal_patterns.png` -- seasonal decomposition charts
