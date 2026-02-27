# Methods: Route Geographic Span vs OTP

## Question
Does the geographic extent of a route predict on-time performance independently of stop count? Analysis 07 found stop count is the strongest OTP predictor (r = -0.53), but routes with many stops also tend to cover more distance. Disentangling the two could clarify whether the problem is "too many stops" or "too long a route."

## Approach
- For each route, collect all stop coordinates from `route_stops` joined to `stops`.
- Compute **geographic span** as the maximum haversine distance between any pair of stops on the route (the diameter of the stop set in km).
- Compute **stop density** as stops per km of span, to capture how tightly packed stops are.
- Correlate span, stop density, and stop count separately with average OTP (Pearson and Spearman).
- Use partial correlation to test whether span predicts OTP after controlling for stop count, and vice versa.
- Scatter plots for span vs OTP and stop density vs OTP.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `route_stops` | Links routes to stops | `prt.db` table |
| `stops` | Lat/lon coordinates | `prt.db` table |
| `otp_monthly` | Monthly OTP per route | `prt.db` table |
| `routes` | Mode classification | `prt.db` table |

## Output
- `output/geographic_span.csv` -- per-route span, stop density, stop count, avg OTP
- `output/span_vs_otp.png` -- scatter plot of geographic span vs OTP
- `output/density_vs_otp.png` -- scatter plot of stop density vs OTP
