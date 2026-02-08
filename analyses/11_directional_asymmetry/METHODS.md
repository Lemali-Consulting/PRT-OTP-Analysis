# Methods: Inbound vs Outbound Asymmetry

## Question
Does a structural directional imbalance in trip frequency correlate with worse OTP? Routes with significantly different IB vs OB trip counts may face operational challenges.

## Approach
- For each route, compute total IB trips and OB trips from `route_stops`.
- Compute an asymmetry index: abs(IB_trips - OB_trips) / (IB_trips + OB_trips).
- Correlate asymmetry with average OTP.
- Investigate routes with highest asymmetry.
- Exclude stops with combined `IB,OB` direction since they cannot be split.

## Data
- `route_stops` -- directional trip counts
- `otp_monthly` -- OTP per route
- `routes` -- route metadata

## Output
- `output/directional_asymmetry.csv` -- per-route directional trip breakdown and OTP
- `output/directional_asymmetry.png` -- scatter plot of asymmetry vs OTP
