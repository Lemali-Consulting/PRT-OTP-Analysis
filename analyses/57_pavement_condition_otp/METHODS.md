# Methods: Pavement Condition and OTP

## Question
Analyses 55 and 56 established that **road width** (lane count) is a robust
correlate of on-time performance: buses on wider, multi-lane roads run late more
often. But both measured road *geometry*. They never tested road *quality*. SPC's
National Highway System pavement-condition layer adds one attribute neither dataset
has: **pavement roughness**, the International Roughness Index (IRI). This analysis
asks two questions:

1. **Does pavement roughness correlate with OTP at all?** Rougher pavement plausibly
   forces slower, more variable bus speeds.
2. **Does roughness add explanatory power *net of road width*?** This is the decisive
   question. The roughest roads are busy urban arterials -- which are also the wide,
   multi-lane roads we already know run late. So a raw IRI->OTP correlation is almost
   certainly confounded with lane count. The honest test is whether IRI survives once
   road width is controlled. A null here is itself a clean finding: it would mean the
   road-type signal is about geometry (how a road channels traffic and stops), not the
   physical condition of the surface.

This is deliberately framed as a confound-aware test, not a hunt for a positive result.

## Approach
- Build `route_road_pavement` (pipeline step 14): for each route, the length-weighted
  mean IRI of NHS pavement segments within 30 m of its GTFS shape, plus the
  length-weighted overall pavement index (OPI) and the share of length rated POOR.
  Match rate records the within-buffer (≈ on-NHS) fraction of the route.
- Include routes with 12+ months of OTP and `route_road_pavement.match_rate >= 0.3`.
- **Bivariate:** correlate IRI with OTP. Also correlate IRI with the PennDOT lane
  count (Analysis 55's `route_road_class.weighted_lanes`) to quantify the confound
  directly.
- **Regression (the core):** replicate the Analysis 18/55 six-feature structural OLS
  baseline on the pavement-matched sample, then build a nested ladder:
  - Model A: structural baseline (6 features).
  - Model B: baseline + IRI (does roughness matter beyond structure?).
  - Model C: baseline + lane count (the road-width control).
  - Model D: baseline + lane count + IRI (**does IRI survive controlling for width?**).
  Test each addition with a nested F-test; compute VIF for the full model and flag any
  predictor with VIF > 5 (IRI and lane count are expected to be correlated).
- Report OPI and poor-share descriptively (Pearson r with OTP).
- Repeat the baseline-vs-IRI comparison on the bus-only subset.

All regression helpers (`compute_span`, `fit_ols`, `compute_vif`, `f_test_nested`) are
replicated locally so the analysis does not import from Analysis 18/55/56 (analyses
must be independent).

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | route_id, month, otp (averaged to route level, 12+ months required) | `prt.db` table |
| `route_road_pavement` | route_id, weighted_iri, weighted_opi, poor_share, match_rate (built by `road_overlay_pavement.py`, pipeline step 14) | `prt.db` table |
| `route_road_class` | route_id, weighted_lanes (PennDOT, the road-width control) | `prt.db` table |
| `route_stops` | stop counts, trip frequencies | `prt.db` table |
| `stops` | lat, lon for geographic span; muni for municipality count | `prt.db` table |
| `routes` | route_id, mode for subtype classification | `prt.db` table |

Inclusion: routes with 12+ months of OTP and `route_road_pavement.match_rate >= 0.3`.
IRI is length-weighted over the NHS pavement segments within 30 m of the route's GTFS
shape. The layer is **NHS-only** (interstates and principal arterials), so each route's
IRI characterizes only its major-arterial running; the match rate quantifies the
covered share. The lane-count control models are fit on the subset of routes that also
clear `route_road_class.match_rate >= 0.3`.

## Output
- `output/model_comparison.csv` -- regression results (baseline, +IRI, +lanes, +lanes+IRI, bus subset)
- `output/vif_table.csv` -- VIF values for the full model
- `output/route_pavement_summary.csv` -- per-route IRI, OPI, poor-share, lane count, OTP
- `output/iri_vs_otp.png` -- bivariate scatter of IRI vs OTP
- `output/iri_vs_lanes.png` -- IRI vs lane count, showing the confound
- `output/r2_progression.png` -- adjusted R² across the nested model ladder
- `output/coefficient_comparison.png` -- beta weights, baseline vs full model
