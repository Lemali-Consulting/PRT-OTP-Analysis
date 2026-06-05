# Findings: Road Classification and OTP

## Summary
**Road type explains OTP, and lane count is the driver.** Adding a road-type block
(length-weighted lane count, functional class, and posted speed) to the six-feature
structural baseline raises R² from **0.40 to 0.58** (adjusted R² 0.36 → 0.54; joint
F = 11.6, p < 0.001). The single feature doing the work is **lane count**: routes that
run along wider, multi-lane roads are reliably *later*, independent of how many stops
they make or how far they travel. This succeeds where Analysis 27 found a null for
traffic *volume* (AADT), and it more than doubles the explanatory gain that truck
percentage — Analysis 27's best traffic predictor — could provide.

## Key Numbers
- 89 routes analyzed (88 bus, 1 rail) after filtering `match_rate >= 0.3`; all 98 routes matched, none excluded for low coverage (median match rate ~93%).
- Structural baseline (6 features): R² = 0.40, Adj R² = 0.357 — reproduces Analysis 27's baseline exactly.
- **+ lane count alone:** Adj R² = 0.515 (+0.16).
- **+ full road-type block:** R² = 0.583, Adj R² = 0.536 (+0.18 R²); joint F = 11.6, p < 0.001.
- + truck % (Analysis 27's predictor, same sample): R² = 0.451 — well below the road-type block.
- Lane count beta weight = **−0.38** (p < 0.001), tied with span as the strongest predictor in the model.
- Posted speed beta = +0.29 (p = 0.021); functional class not significant (p = 0.11).
- All VIFs ≤ 3.5 (lane count VIF = 1.46). Lane count is **uncorrelated with stop count (r = +0.02) and span (r = −0.08)** — its contribution is genuinely independent.
- Bus-only subset: identical story (Adj R² 0.328 → 0.515, joint F = 11.6, p < 0.001).
- Lane-count range across matched routes: 1.6 – 2.5 weighted lanes.

## Observations
- **More lanes, later buses.** The bivariate correlation between length-weighted lane
  count and OTP is r = −0.47 — the strongest single road-attribute correlate of OTP in
  the project. In the full model it survives at beta = −0.38, p < 0.001.
- **Lanes and speed pull in opposite directions, and that resolves Analysis 27's sign
  puzzle.** Holding lane count fixed, *higher* posted speed is associated with *better*
  OTP (beta +0.29). The coherent reading is that the problematic roads are **congested
  multi-lane urban arterials with low effective speeds** — many lanes, signalized
  intersections, heavy turning and cross-traffic — not high-speed highways. A wide road
  that also moves fast is fine; a wide road that crawls is where buses fall behind.
- **This is what truck % was reaching for.** Analysis 27 found truck percentage was its
  only significant traffic predictor and argued it proxied road type. Replacing the proxy
  with direct road-type measures roughly triples the gain (truck adds +0.05 R²; the
  road-type block adds +0.18), confirming that interpretation and superseding it.
- **Independent of route geometry.** Lane count's near-zero correlation with stop count
  and span (and its low VIF) means it is not just re-encoding "long route" or "many
  stops." It captures a distinct dimension: the *kind of road* the route operates on.

## Discussion
Across Analyses 18, 26, and 27 the model-building narrative had stalled at ~40–47% of OTP
variance explained by route geometry and mode, with traffic volume contributing nothing
and the remainder attributed to operational factors not in the data. This analysis moves
the ceiling: a single, cleanly measured road attribute — how many lanes the route runs
along — lifts explained variance to ~58%.

The mechanism is intuitive once lane count and speed are separated. Pittsburgh's
worst-performing corridors (e.g., routes 71B, 88, 58, the 61-series) thread multi-lane
arterials through dense neighborhoods: more lanes mean more signal phases, more turning
conflicts, more boarding friction at busy stops, and more exposure to incident-driven
backups — all of which degrade schedule adherence even though the road has nominal
capacity. The positive speed coefficient is the tell: where those wide roads actually
carry traffic at speed, buses keep their schedule.

For policy this is more actionable than the AADT null. Lane count and functional class
are fixed, mappable attributes of the road network, so this offers a structural screen
for where transit-priority treatments (signal priority, bus lanes, queue jumps, stop
consolidation on arterials) are most likely to pay off — namely the multi-lane,
low-speed arterial segments, not the quiet neighborhood streets.

## Caveats
- **Ecological, area-level association.** These are route-level relationships between the
  road network a route traverses and its average OTP, not claims about individual trips
  or stops.
- **Lane count is a route-average exposure**, length-weighted over PennDOT segments within
  30 m of the GTFS shape. It does not distinguish where along the route the wide-road
  segments fall, nor time-of-day conditions.
- **PennDOT state-route coverage.** The RMSSEG layers cover state-administered roads;
  purely local streets are underrepresented (the same limitation as Analysis 27). Match
  rates are high (median ~93%), but segments on city-maintained streets may be missing —
  the Pittsburgh city centerline is a documented phase-2 extension.
- **Functional class added little** on its own (p = 0.11); the lane-count and speed
  channels carry the road-type signal, so the headline rests on those two.
- **Correlation, not proven causation.** Lane count plausibly proxies a bundle of
  co-located features (signal density, land use, congestion); the analysis shows it is a
  strong, independent *predictor*, not that adding or removing a lane would change OTP.

## Validation

### Data inputs
1. **Data source verified.** All road-type columns were read from `route_road_class`,
   built by pipeline step 12 (`road_overlay.py`) from the PennDOT `roadwaysegments` and
   `roadwayadmin` ArcGIS layers; field names were taken from the live REST schema, not
   from memory, and documented in `data/penndot-roadclass/SOURCE.md`. The query result is
   validated against the `ROUTE_ROAD_CLASS` schema (`validate(..., subset=True)`).
2. **Geographic/temporal scope matches.** OTP is averaged over routes with 12+ months of
   data; road-type metrics are matched to the same GTFS route shapes and filtered to
   `match_rate >= 0.3`, identical to Analysis 27's inclusion rule. All road data is
   Allegheny County (`CTY_CODE='02'`).
3. **Null/missing handling.** Routes lacking a weighted lane count, functional class,
   speed, or any structural feature are dropped before modeling (none were, beyond the
   match-rate filter). Length-weighting skips segments with missing values rather than
   counting them as zero.

### Results plausibility
4. **Aggregates sanity-checked.** The structural baseline reproduces Analysis 27's R² of
   0.40 exactly on the same sample, confirming the baseline replication is correct.
   Lane-count range (1.6–2.5) and speed range are physically sensible for urban arterials.
5. **Surprising result investigated.** The large R² jump (+0.18) was checked for
   artifact: lane count's VIF is 1.46 and it is essentially uncorrelated with stop count
   (r = +0.02) and span (r = −0.08), so the gain is not collinearity-driven double-counting.
   The bivariate r = −0.47 is consistent with the multivariate beta.
6. **Direction of effects checked.** Known structural relationships retain expected signs
   (more stops → lower OTP; longer span → lower OTP; rail → higher OTP). The lane-count
   sign (more lanes → lower OTP) initially appears to conflict with Analysis 27's positive
   truck-% coefficient, but the simultaneous positive speed coefficient resolves it:
   the signal is congested low-speed arterials, consistent with both findings.

### Statistical diagnostics
7. **Multicollinearity checked.** VIF computed for every predictor in the full model;
   all ≤ 3.5, none above the 5 threshold. Reported in `output/vif_table.csv`.
8. **Small-sample routes flagged.** Route-level OTP requires 12+ months; the match-rate
   floor (0.3) excludes routes with poor road coverage. 89 routes met both criteria.
9. **Ecological framing.** Findings are described as route-level / area-level associations
   throughout; no individual-trip claims are made.
