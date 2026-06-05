# Findings: City Centerline and OTP

## Summary
Analysis 55 found that buses on wider, multi-lane roads run late more often, using
PennDOT's **state-road** inventory. This analysis re-tests that finding with a fully
independent dataset -- the **City of Pittsburgh street centerline**, which counts lanes
on the *entire* city street network, local streets included -- and the result holds
almost exactly. City-network lane count correlates with OTP at **r = -0.44** (vs PennDOT's
-0.47), and adding it to the structural baseline lifts explained variance from **43% to
60%** (a +0.16 jump in adjusted R², F = 29.4, p < 0.0001). Two lane-count measures built
from different agencies' data, by different methods, point to the same conclusion: road
width is a real, robust correlate of on-time performance, not an artifact of which roads
PennDOT happens to inventory.

## Key Numbers
- **City lane count vs OTP:** r = -0.438 (p = 0.0001, n = 77 routes). Analysis 55 PennDOT: r = -0.470.
- **Regression gain:** adjusted R² 0.432 -> 0.596 (+0.164) when city lane count is added to the 6-feature structural baseline. Nested F = 29.4, p < 0.0001.
- **City lane count beta weight:** -0.418 (p < 0.0001) -- the largest standardized effect in the augmented model, comparable to stop count (-0.483) and span (-0.294).
- **VIF for city lane count = 1.12** -- essentially no collinearity with the structural features; it carries independent information.
- **Two measures agree:** city vs PennDOT lane count correlate at r = +0.511 (n = 75); means 2.14 (city) vs 2.21 (PennDOT) lanes.
- **Bus-only:** adjusted R² 0.365 -> 0.549 when city lane count is added (F = 29.1, p < 0.0001).
- **Coverage:** 77 of 89 city-matched routes have match_rate >= 0.3; median within-city coverage 66%.

## Observations
- **The lane-count finding replicates on an independent dataset.** The whole point of this
  analysis was to check whether Analysis 55's lane-count effect was an artifact of PennDOT's
  state-road selection. It is not: a different agency's inventory, covering a broader set of
  streets (including local roads PennDOT omits), produces a near-identical correlation and an
  even larger single-predictor R² gain.
- **The two lane-count measures are related but not identical (r = +0.51), yet both predict
  OTP about equally.** If the effect were a measurement artifact, the two differently-built
  measures would not agree this consistently on direction and magnitude. Their partial
  agreement (city lanes fold in local 1-2 lane streets, lowering the mean slightly from 2.21
  to 2.14) is what we would expect from two honest measures of the same underlying road width.
- **Coverage expansion turned out modest.** The original phase-2 hope was that the city
  centerline would fill in routes PennDOT misses. In practice it added only ~2 such routes:
  city routes spend roughly half their length outside Pittsburgh limits (median within-city
  coverage 66%), where the centerline does not reach. The analysis's value is robustness, not
  coverage.
- **One-way share and limited-access (freeway) share show no association with OTP** (r = +0.03
  and +0.01, both n.s.). Lane count alone carries the road-width signal, consistent with
  Analysis 55, where lane count dominated functional class and posted speed.

## Caveats
- **Area-level (ecological) association.** This is a route-level relationship between the
  roads a route runs along and its aggregate OTP. It does not establish that any individual
  trip is late *because* of a wide road; lane count co-varies with downtown/arterial operating
  environments, signal density, and traffic that are not all separately controlled here.
- **City-limits coverage only.** The centerline covers City of Pittsburgh streets, so suburban
  portions of routes are unmeasured. Routes are included only when at least 30% of their shape
  matches a city street; 12 low-coverage routes were excluded. The lane metric describes each
  route's *within-city* roads.
- **CFCC functional class is not usable here.** The dataset's Census Feature Class Codes are
  largely degenerate (A3* lumps ~88% of streets), so functional class was not used as a
  predictor. Only lane count and the A1* limited-access flag were derived.
- **Lane count `0`/null treated as missing.** ~8% of segments lack a usable lane count; these
  are dropped from the length-weighted mean rather than counted as zero-lane roads.
- **Not a causal or independent corroboration of magnitude.** Because city and PennDOT lane
  counts are correlated (r = 0.51), this is a robustness check on the *existence and direction*
  of the effect, not a fully independent second estimate of its size.

## Validation

### Data inputs
1. **Data source verified.** `route_road_city` columns checked against
   `prt_otp_analysis.common.schemas.ROUTE_ROAD_CITY` and validated at load
   (`validate(..., subset=True)`). Centerline fields (`no_lanes`, `cfcc`, `oneway`) confirmed
   against the live ArcGIS service before building (see `data/pgh-centerline/SOURCE.md`).
2. **Geographic/temporal scope matches.** OTP averaged over routes with 12+ months; lane
   metrics matched to the same GTFS route shapes used throughout the project (30 m buffer,
   identical KDTree machinery as Analyses 27/55). City-limits coverage limitation documented.
3. **Null/missing handling.** Lane count `0` and null treated as missing in the length-weighted
   mean (not as zero-lane roads). Routes with match_rate < 0.3 excluded, not imputed.

### Results plausibility
4. **Aggregates sanity-checked.** Mean lane count 2.14 (city) is consistent with a
   predominantly 1-2-lane urban street network and sits just below PennDOT's 2.21 (state roads
   skew wider), exactly as expected when local streets are folded in.
5. **Surprising results investigated.** The result is *not* surprising -- it confirms Analysis
   55 with an independent dataset, which was the goal. The direction (more lanes -> lower OTP)
   matches the established finding.
6. **Direction of effects checked.** Negative lane-count -> OTP slope reproduces Analysis 55;
   rail dummy positive; stop count and span negative -- all consistent with prior structural
   models.

### Statistical diagnostics
7. **Multicollinearity checked.** VIF reported for all predictors; max is span_km at 3.66.
   City lane count VIF = 1.12. No predictor exceeds 5.
8. **Small-sample routes flagged.** Minimum 12 months of OTP and match_rate >= 0.3 enforced;
   n = 77 routes (75 bus, 2 rail). The 2-route rail subset is noted, not over-interpreted.
9. **Ecological framing.** Results described as route/area-level associations throughout; no
   individual-trip causal claim is made.
