# Methods: City Centerline and OTP

## Question
Analysis 55 found that **lane count** is the strongest road-type predictor of OTP
(r = -0.47), but it was computed only over **PennDOT state roads** -- the major,
arterial portion of each route. Two concerns follow: (1) is the lane-count signal a
real road-width effect, or an artifact of which segments PennDOT happens to inventory?
(2) does it hold on the broader street network, including the local 1-2 lane streets
that state-road data omits? This analysis answers both by recomputing route lane count
from a fully independent dataset -- the **City of Pittsburgh street centerline** -- and
re-testing it against OTP.

This is primarily a **robustness / cross-validation** analysis, not a coverage-expansion
one: the city centerline matches almost the same routes PennDOT does (the centerline is
city-limits-only, so suburban route segments are uncovered), but it measures lane count
a completely different way, from a different agency's inventory of a broader set of streets.

## Approach
- Build `route_road_city` (pipeline step 13): for each route, the length-weighted mean
  lane count of city street segments within 30 m of its GTFS shape, plus one-way share
  and limited-access (freeway, CFCC `A1*`) share. Lane count `0`/null is treated as
  missing. Match rate records the within-buffer (≈ within-city) fraction of the route.
- Include routes with 12+ months of OTP and `route_road_city.match_rate >= 0.3`.
- **Bivariate:** correlate city-network lane count with OTP, and compare against
  Analysis 55's PennDOT lane-count correlation.
- **Head-to-head:** for routes matched by both datasets, compare the city vs PennDOT
  lane count (means and Pearson r) to show they are related but distinct measures.
- **Regression:** replicate the Analysis 18/55 six-feature structural OLS baseline on the
  city-matched sample, then add city lane count and test the improvement with a nested
  F-test. Compute VIF for the augmented model and flag any predictor with VIF > 5.
- Report one-way share and limited-access share descriptively (Pearson r with OTP).
- Repeat the base-vs-lanes comparison on the bus-only subset.

The CFCC functional-class codes in this dataset are largely degenerate (A3* lumps ~88%
of streets), so functional class is **not** used as a predictor; lane count carries the
road-width signal, consistent with Analysis 55 where lane count dominated.

All regression helpers (`compute_span`, `fit_ols`, `compute_vif`, `f_test_nested`) are
replicated locally so the analysis does not import from Analysis 18/55 (analyses must be
independent).

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, otp (averaged to route level, 12+ months required) | `prt.db` table |
| `route_road_city` | route_id, weighted_lanes, oneway_share, limited_access_share, match_rate (built by `road_overlay_city.py`, pipeline step 13) | `prt.db` table |
| `route_road_class` | route_id, weighted_lanes (PennDOT, for head-to-head comparison) | `prt.db` table |
| `route_stops` | stop counts, trip frequencies | `prt.db` table |
| `stops` | lat, lon for geographic span; muni for municipality count | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

Inclusion: routes with 12+ months of OTP and `route_road_city.match_rate >= 0.3`.
Lane count is length-weighted over the City of Pittsburgh centerline segments within 30 m
of the route's GTFS shape. Because the centerline is city-limits-only, routes that run
into the suburbs are only partially covered; the match rate quantifies the covered share.

## Output
- `output/model_comparison.csv` -- regression results (base vs + city lanes, bus subset)
- `output/vif_table.csv` -- VIF values for the augmented model
- `output/route_road_city_summary.csv` -- per-route city vs PennDOT lane metrics with OTP
- `output/city_lanes_vs_otp.png` -- bivariate scatter of city lane count vs OTP
- `output/city_vs_penndot_lanes.png` -- city vs PennDOT lane count agreement scatter
- `output/r2_progression.png` -- adjusted R² baseline vs + city lanes
- `output/coefficient_comparison.png` -- beta-weight comparison, base vs augmented model
