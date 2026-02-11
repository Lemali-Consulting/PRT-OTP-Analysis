# Methods: Seasonal Patterns

## Question
Do PRT routes exhibit consistent seasonal OTP patterns? Are summer or winter months systematically better or worse?

## Approach
- Restrict to **complete calendar years** (2019--2024) to ensure every month-of-year has equal year coverage.
- Use a **balanced panel** of routes present in all 12 months-of-year for the system-wide profile, preventing compositional bias from seasonal or short-lived routes.
- Compute a system-wide seasonal profile by averaging across balanced-panel routes (trip-weighted).
- Measure seasonal amplitude: max(month-of-year avg) - min(month-of-year avg) per route.
- Decompose into trend + seasonal + residual using a moving-average approach:
  1. Trend = 12-month centered rolling mean
  2. Seasonal = month-of-year mean of (OTP - trend)
  3. Residual = OTP - trend - seasonal
- Rank routes by seasonal amplitude to identify those most affected by seasons.
- Route-level analysis requires at least 3 years of data (36 months) for reliable seasonal estimates.

## Data
- `otp_monthly` -- monthly OTP per route
- `route_stops` -- trip counts for weighting
- `routes` -- route metadata

## Output
- `output/seasonal_patterns.csv` -- month-of-year seasonal profile per route
- `output/seasonal_patterns.png` -- seasonal decomposition charts
