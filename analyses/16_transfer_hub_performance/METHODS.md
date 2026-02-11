# Methods: Transfer Hub Performance

## Question
Do passengers at major transfer hubs -- stops served by many routes -- experience worse reliability than passengers at simpler stops? This matters because transfer hub passengers are disproportionately transit-dependent and a missed connection at a hub cascades into longer wait times.

## Approach
- Count distinct routes per stop from `route_stops` to measure **connectivity** (number of routes serving each stop).
- For each stop, compute a trip-weighted average OTP across all routes serving it.
- Classify stops as **hubs** (5+ routes), **medium** (2-4 routes), or **simple** (1 route).
- Compare OTP distributions across these tiers.
- Identify the busiest hubs and their OTP.
- Scatter plot of connectivity vs stop-level OTP.

## Data
- `route_stops` -- which routes serve which stops, with trip counts
- `stops` -- stop names and coordinates
- `otp_monthly` -- monthly OTP per route
- `routes` -- mode for context

## Output
- `output/hub_performance.csv` -- per-stop connectivity, OTP, and classification
- `output/connectivity_vs_otp.png` -- scatter plot of routes-per-stop vs OTP
- `output/hub_tier_comparison.png` -- box plot of OTP by hub tier
