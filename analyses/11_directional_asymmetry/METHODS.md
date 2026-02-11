# Methods: Inbound vs Outbound Asymmetry

## Question
Does a structural directional imbalance in trip frequency correlate with worse OTP? Routes with significantly different IB vs OB trip counts may face operational challenges.

## Approach
- For each route, compute peak IB frequency and peak OB frequency (`MAX(trips_wd)`) from `route_stops`. Stops with `trips_wd IS NULL` are excluded.
- Include stops with `IB,OB` direction in both IB and OB counts to avoid exclusion bias.
- Compute an asymmetry index: abs(IB_trips - OB_trips) / (IB_trips + OB_trips).
- Compute average OTP per route from `otp_monthly`, requiring at least 12 months of data (`HAVING COUNT(*) >= 12`).
- Correlate asymmetry with average OTP using Pearson (all routes), Pearson (bus-only), and Spearman (bus-only).
- Investigate routes with highest asymmetry.

## Data
- `route_stops` -- directional trip counts
- `otp_monthly` -- OTP per route
- `routes` -- route metadata

## Output
- `output/directional_asymmetry.csv` -- per-route directional trip breakdown and OTP
- `output/directional_asymmetry.png` -- scatter plot of asymmetry vs OTP
