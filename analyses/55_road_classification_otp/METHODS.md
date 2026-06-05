# Methods: Road Classification and OTP

## Question
Does the **type of road** a route runs on -- lane count, functional class, and posted
speed -- explain OTP variance beyond the structural features (stop count, geographic
span, mode, etc.) of the Analysis 18 model? Analysis 27 found that traffic *volume*
(AADT) does not, and that the only traffic-related predictor with signal was truck
percentage, which it argued was a noisy proxy for road type. This analysis tests road
type directly.

## Approach
- Replicate the Analysis 18 / 27 six-feature structural OLS baseline on routes with
  matched road-classification data (`match_rate >= 0.3`).
- Add a **road-type block** -- length-weighted lane count, functional class, and posted
  speed -- and compare adjusted R-squared against the baseline using a nested F-test.
- Fit an intermediate model with **lane count alone** to isolate its contribution
  (the bivariate spike showed lane count is by far the strongest road attribute,
  r = -0.47 with OTP).
- Fit a **truck-percentage** model (base + `avg_truck_pct` from `route_traffic`) on the
  same sample, so the road-type block can be compared head-to-head against Analysis 27's
  best traffic predictor.
- Compute VIF for the full road-type model. Lane count, functional class, and speed are
  expected to intercorrelate and to correlate with stop count and span -- flag any
  predictor with VIF > 5 and interpret coefficient attribution with that in mind.
- Report `arterial_share` and `divided_share` descriptively (Pearson r with OTP); they
  are not added to the regression to avoid inflating collinearity.
- Repeat the base-vs-road-block comparison on the bus-only subset.
- Charts: lane-count vs OTP scatter, adjusted-R² progression across nested models,
  standardized-coefficient comparison, and a partial-residual plot for lane count.

All regression helpers (`compute_span`, `fit_ols`, `compute_vif`, `f_test_nested`) are
replicated locally so the analysis does not import from Analysis 18/27 (analyses must be
independent).

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, otp (averaged to route level, 12+ months required) | `prt.db` table |
| `route_road_class` | route_id, weighted_lanes, weighted_func_cls, weighted_speed, arterial_share, divided_share, match_rate (built by `road_overlay.py`, pipeline step 12) | `prt.db` table |
| `route_traffic` | route_id, avg_truck_pct (for head-to-head comparison) | `prt.db` table |
| `route_stops` | stop counts, trip frequencies | `prt.db` table |
| `stops` | lat, lon for geographic span; muni for municipality count | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

Inclusion: routes with 12+ months of OTP and `route_road_class.match_rate >= 0.3`.
Road-type metrics are length-weighted over the PennDOT segments within 30 m of the
route's GTFS shape. Functional class uses FHWA codes (1 = Interstate ... 7 = Local);
lower values denote more major roads. `divided_share` treats `DIVSR_TYPE = '0'` as
undivided and any other code as divided.

## Output
- `output/model_comparison.csv` -- regression results for all models
- `output/vif_table.csv` -- VIF values for the full road-type model
- `output/route_road_class_summary.csv` -- per-route road-type metrics with OTP
- `output/lanes_vs_otp_scatter.png` -- bivariate scatter of lane count vs OTP
- `output/r2_progression.png` -- adjusted R² across the nested models
- `output/coefficient_comparison.png` -- beta-weight comparison, base vs road-type model
- `output/partial_residual.png` -- partial-residual plot for lane count
