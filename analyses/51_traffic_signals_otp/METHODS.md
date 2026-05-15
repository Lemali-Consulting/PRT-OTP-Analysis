# Methods: Traffic Signals and OTP

## Question
Does the density of traffic signals along a route (signals per route-km) explain
on-time performance (OTP) variance beyond stop count, geographic span, and the
other structural features from the Analysis 18 / 27 model?

## Approach
- Use the `route_signals` table (built by pipeline step `11_signal_overlay`),
  which counts OpenStreetMap `highway=traffic_signals` nodes within 30 m of each
  route's GTFS shape and divides by the route's longest-shape length.
- **Use signal density, not raw signal count, as the predictor.** Raw `n_signals`
  is mechanically correlated with route length, and route length itself depresses
  OTP, so a model using raw count would capture a length artifact rather than a
  signal effect. Raw count is reported descriptively only. As a diagnostic, the
  bivariate correlations of both `n_signals` and `signal_density` against OTP are
  compared to demonstrate this confound.
- Replicate the Analysis 27 six-feature OLS base model (stop count, geographic
  span, is_rail, is_premium_bus, weekend ratio, municipal reach) on routes with
  matched `route_signals` data and at least 12 months of OTP observations.
- Add `signal_density` as a seventh predictor. Compare adjusted R-squared between
  the six- and seven-feature models with a nested F-test.
- Check VIF for multicollinearity. `signal_density`, `stop_count`, and `span_km`
  all partly encode "urban arterial vs. suburban" route character, so a VIF above
  5 is plausible and is reported, not silently dropped.
- Repeat the comparison on the bus-only subset.
- The `route_signals.match_rate` field (fraction of shape points near a signal)
  is **not** used as an inclusion filter: unlike the PennDOT road-network match
  rate in Analysis 27, it is essentially proportional to signal density and is
  not a coverage-quality signal. It is retained only as a diagnostic column.
- Generate a bivariate scatter (signal density vs OTP), a coefficient comparison
  chart, and a partial residual plot.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, otp (averaged to route-level, 12+ months required) | `prt.db` table |
| `route_signals` | route_id, n_signals, length_km, signal_density, match_rate (built by `signal_overlay.py`) | `prt.db` table |
| `route_stops` | stop counts, trip frequencies | `prt.db` table |
| `stops` | lat, lon for geographic span computation; muni for municipal reach | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

## Output
- `output/model_comparison.csv` -- regression results for all models
- `output/vif_table.csv` -- VIF values for the expanded model
- `output/route_signals_summary.csv` -- per-route signal data with OTP
- `output/signal_density_vs_otp_scatter.png` -- bivariate scatter of signal density vs OTP
- `output/coefficient_comparison.png` -- beta weight comparison between base and expanded models
- `output/partial_residual.png` -- partial residual plot for signal density
