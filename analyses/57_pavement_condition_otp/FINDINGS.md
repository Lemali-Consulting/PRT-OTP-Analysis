# Findings: Pavement Condition and OTP

## Summary
Analyses 55 and 56 showed that **road width** (lane count) robustly tracks on-time
performance. This analysis tested whether **road quality** -- pavement roughness, the
International Roughness Index (IRI) -- adds anything beyond that. The answer is a clean
**null**: once road width is controlled, pavement roughness has **no** detectable
association with OTP (F = 2.68, p = 0.11; adjusted R² rises only 0.562 → 0.575). The
weak raw hint that rougher roads run a little later (r = −0.14, not significant) is
explained by a confound -- rough pavement sits on the same wide arterials we already
know run late (IRI vs lane count r = +0.33, p = 0.009). The road-type signal is about
**geometry** (how a road channels traffic and stops), not the physical condition of the
surface. This is a useful negative result: repaving a corridor would not, on this
evidence, be expected to improve schedule reliability.

## Key Numbers
- **IRI vs OTP (bivariate):** r = −0.144, p = 0.259 (n = 63 routes) -- **not significant**.
- **The confound is real:** IRI vs lane count r = +0.325, p = 0.009. Rougher NHS pavement is on the wider arterials.
- **IRI over the structural baseline (no width control):** F = 3.74, p = 0.058 -- marginal, adj R² 0.240 → 0.275.
- **IRI net of lane count (the decisive test):** F = 2.68, **p = 0.107 -- not significant**. Adj R² 0.562 → 0.575 (+0.013).
- **Lane count, by contrast, dominates:** β = −0.68, p < 0.0001; adding it lifts adj R² 0.240 → 0.562 (F = 42.9).
- **No collinearity excuse:** in the full model VIF = 1.78 for IRI and 1.57 for lane count (all predictors < 5). IRI had independent variance available and still added nothing.
- **Coverage:** 63 of 92 routes clear NHS match_rate ≥ 0.3; median NHS coverage 52%. IRI range 104–215 in/mi (mean 161).

## Observations
- **Pavement roughness does not survive the road-width control.** The headline question
  was whether road *quality* explains OTP beyond road *geometry*. It does not. Lane count
  absorbs essentially all of the road-related signal; IRI's marginal contribution after
  controlling for width is statistically indistinguishable from zero.
- **The raw IRI hint is a confound, not a finding.** Bivariately IRI is weakly negative
  (rougher → later) but not significant, and it co-varies with lane count (r = +0.33).
  This is exactly the trap flagged before the analysis: the roughest roads are busy
  arterials. Treating the raw correlation as a pavement effect would have been wrong.
- **`poor_share` runs the "wrong" way and is not robust.** The share of a route on
  poor-rated pavement is weakly *positively* correlated with OTP (r = +0.29, p = 0.02) --
  i.e., more poor pavement, slightly *better* on-time. This sign flip (opposite to the
  continuous IRI measure) is a hallmark of a confounded bivariate, not a real protective
  effect of bad roads; it is reported descriptively and excluded from the regression.
- **Rail dropped out of the sample, as expected.** All 63 included routes are bus. The
  light-rail lines (BLUE, RED, SILVER) run on their own right-of-way, not NHS roads, so
  they fall below the coverage threshold -- a sanity check that the spatial match behaves.
- **This complements, not contradicts, Analyses 55/56.** Those found road width matters;
  this finds that, given width, surface condition does not. Together they sharpen the
  mechanism: the road-type effect operates through arterial geometry and the traffic/stop
  environment it implies, not through ride quality.

## Caveats
- **Area-level (ecological) association.** This is a route-level relationship between the
  roads a route runs along and its aggregate OTP, not an individual-trip causal claim.
- **NHS-only coverage.** The pavement layer covers the National Highway System
  (interstates and principal arterials) only, so each route's IRI characterizes its
  major-arterial running, not its local-street segments. 29 routes with < 30% NHS
  coverage were excluded; the included routes have median 52% coverage.
- **A null is not proof of no effect.** With n = 63 the analysis is powered to detect a
  moderate independent IRI effect; a small one could be missed. The point estimate is
  small and the same sign as the (confounded) bivariate, so a large hidden effect is
  unlikely, but this rules out a *strong* pavement→OTP relationship, not a tiny one.
- **IRI measures roughness, not all pavement distress.** Potholes, patching, and
  work-zone repaving -- which could plausibly affect buses more acutely than average
  roughness -- are not captured by a length-weighted IRI mean.
- **Static snapshot.** Pavement condition and OTP are each aggregated over time, not
  matched month-to-month, so this cannot detect whether a repaving event changed a
  route's reliability.

## Validation

### Data inputs
1. **Data source verified.** `route_road_pavement` columns checked against
   `prt_otp_analysis.common.schemas.ROUTE_ROAD_PAVEMENT` and validated at load
   (`validate(..., subset=True)`). Pavement fields (`ROUGH_INDX`, `OVERALL_PV`,
   `IRI_RATING`) confirmed against the live SPC service before building (see
   `data/spc-pavement/SOURCE.md`).
2. **Geographic/temporal scope matches.** OTP averaged over routes with 12+ months; IRI
   matched to the same GTFS route shapes used throughout the project (30 m buffer,
   identical KDTree machinery as Analyses 27/55/56). The lane-count control comes from
   `route_road_class` (Analysis 55) on the same routes; all 63 pavement-matched routes
   also clear the lane match threshold, so Q1 and Q2 use one identical sample.
3. **Null/missing handling.** IRI is filtered to `> 0` at query time; OPI `0` treated as
   missing. Routes with NHS match_rate < 0.3 excluded, not imputed.

### Results plausibility
4. **Aggregates sanity-checked.** Mean IRI 161 in/mi (range 104–215) is consistent with
   FAIR-to-POOR urban arterial pavement; the roughest routes (71A–D, 88, 61A) are known
   busy corridors. Values are in the expected band for NHS roads.
5. **Surprising results investigated.** The result is *not* surprising and is the honest
   outcome: the raw IRI hint was anticipated to be a road-width confound, and it is. The
   `poor_share` sign flip was investigated and attributed to confounding, not reported as
   a protective effect.
6. **Direction of effects checked.** Lane count reproduces the Analysis 55/56 negative
   sign and dominates; stop count and span negative; n_munis positive -- all consistent
   with prior structural models.

### Statistical diagnostics
7. **Multicollinearity checked.** VIF reported for all predictors in the full model; max
   is is_premium_bus at 3.34. IRI = 1.78, lane count = 1.57. No predictor exceeds 5, so
   the null IRI result is not a collinearity artifact.
8. **Small-sample routes flagged.** Minimum 12 months of OTP and NHS match_rate ≥ 0.3
   enforced; n = 63 routes (all bus). Constant dummy columns (is_rail, with no rail in
   the sample) are dropped before fitting so the design matrix stays well-conditioned.
9. **Ecological framing.** Results described as route/area-level associations throughout;
   no individual-trip causal claim is made.
