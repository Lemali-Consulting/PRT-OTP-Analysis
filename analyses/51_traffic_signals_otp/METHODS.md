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
- **Cross-validate the OSM signal exposure against PRT's authoritative records.**
  From the `stop_signals` table (PRT-supplied, pipeline `15_stop_signals`),
  compute each route's `sig_stop_share` — the fraction of its stops that sit at a
  traffic signal — and `n_sig_stops`. Correlate these against the OSM
  `signal_density` / `n_signals`; strong agreement confirms the OSM proxy is
  sound. As with raw count, `sig_stop_share` (stop-normalized) is the honest
  predictor and `n_sig_stops` is reported only descriptively (it tracks stop
  count, which itself depresses OTP).
- **Re-test with the authoritative predictor.** Fit `base + sig_stop_share`
  (Model 3) and `base + signal_density + sig_stop_share` (Model 4), each with a
  nested F-test and VIF, to check whether PRT's independent measure confirms the
  signal→OTP relationship and whether the two signal measures are redundant.
- Repeat the expanded comparison on the bus-only subset.
- Generate a bivariate scatter (signal density vs OTP), a coefficient comparison
  chart, a partial residual plot, and a cross-validation scatter (PRT
  signalized-stop share vs OSM signal density).

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, otp (averaged to route-level, 12+ months required) | `prt.db` table |
| `route_signals` | route_id, n_signals, length_km, signal_density, match_rate (built by `signal_overlay.py`) | `prt.db` table |
| `stop_signals` | per-stop authoritative signal class; aggregated to per-route `sig_stop_share` / `n_sig_stops` (built by `15_stop_signals`) | `prt.db` table |
| `route_stops` | stop counts, trip frequencies, stop→route mapping for authoritative aggregation | `prt.db` table |
| `stops` | lat, lon for geographic span computation; muni for municipal reach | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

## Output
- `output/model_comparison.csv` -- regression results for all models (base,
  +signal_density, +sig_stop_share, combined, bus-only)
- `output/vif_table.csv` -- VIF values for the expanded model
- `output/route_signals_summary.csv` -- per-route signal data with OTP, including
  authoritative `n_sig_stops` and `sig_stop_share`
- `output/signal_density_vs_otp_scatter.png` -- bivariate scatter of signal density vs OTP
- `output/coefficient_comparison.png` -- beta weight comparison between base and expanded models
- `output/partial_residual.png` -- partial residual plot for signal density
- `output/cross_validation_signal_exposure.png` -- PRT authoritative signalized-stop
  share vs OSM signal density (proxy validation)
