# Findings: Near-Side vs. Far-Side Stop Placement

## Summary
PRT bus stops at signalized intersections are overwhelmingly placed on the
**near side** — before the traffic light in the direction of travel. Among the
1,549 stops located within 50 m of an OSM traffic signal, **83% are near-side**
(1,250) and only **17% are far-side** (262). The remaining 76% of PRT stops
(4,915) are mid-block — not adjacent to a signal at all. Near-side fraction has
a weak, non-significant negative correlation with route OTP (r = −0.15,
p = 0.21), consistent with the hypothesis that near-side stops add delay but
not distinguishable from noise at the route level given how little variation
there is across routes.

## Key Numbers
- **6,464 total stops** analyzed (GTFS, bus only — 4 station nodes excluded).
- **1,549 stops (24%)** within 50 m of an OSM traffic signal ("at intersection").
- Among those: **1,250 near-side (83%)**, **262 far-side (17%)**, **37 ambiguous (<3%)**.
- **4,915 stops (76%)** are mid-block — no signal within 50 m.
- **76 routes** had ≥ 3 classifiable signalized stops and OTP data.
- Near-side fraction by route ranges from **33% to 100%** (median ~88%).
- OTP correlation: r = −0.15 (p = 0.21), Spearman ρ = −0.09 (p = 0.45) — not significant.

## Observations
- **Near-side is the overwhelming default.** Across nearly every PRT route,
  buses stop before the signal, not after. The near-side fraction drops below
  70% only for a handful of routes. This is consistent with older US transit
  practice — near-side stops were historically preferred because the bus can
  open doors while waiting for a red, allowing simultaneous boarding/signal-wait.
  Modern transit operations guidance favors far-side because the bus clears the
  intersection before stopping (no double-stop), benefits from a rolling start
  on the green, and keeps the bus out of the box during the red.
- **The OTP correlation is weak and non-significant.** This does not mean
  near-side placement is harmless — the mechanism is plausible, and the lack of
  signal is best explained by two factors: (1) near-side fraction varies little
  across routes (most routes are 80–100% near-side, offering little statistical
  leverage), and (2) the Analysis 51 structural predictors (signal density, stop
  count, route length) already absorb most of the variance, leaving little for
  placement type to explain at the route level. A stop-level or trip-level
  analysis with actual dwell/departure data would be needed to test the
  mechanism directly.
- **Far-side stops cluster on newer or rebuilt corridors.** Routes with higher
  far-side fractions (near-side fraction ~33–50%) tend to be routes that have
  seen more recent infrastructure investment or run on busier arterials where
  signals were added or retimed more recently. This is not formally tested here.
- **Most stops are mid-block.** 76% of PRT stops have no signal within 50 m.
  Pittsburgh's dense, hilly street grid means many stops are in the middle of
  short block faces, away from intersections — reducing the operational
  relevance of near/far placement for the majority of the network.

## Discussion
This is a descriptive analysis: it establishes *what* the current placement mix
looks like, not whether changing placement would improve OTP. The practical
implication is that if PRT or City of Pittsburgh were to invest in stop
relocation or signal retiming as part of a transit priority program, the
near-side-to-far-side conversion case is strongest on routes where (a) near-side
fraction is high, (b) signal density is high (Analysis 51), and (c) OTP is
already low — the dense East End local routes (71B, 81, 83, 82) score on all
three dimensions.

The Analysis 51 finding that signal *density* predicts OTP independently of stop
count remains the more actionable result. Near-side placement adds a plausible
incremental delay per stop, but the bigger issue is that these routes encounter
many signals at all — each one adding a stochastic cycle wait regardless of
whether the stop is before or after it.

## Caveats
- **Single-direction classification.** Each stop is classified using its
  canonical shape (most-served direction). A stop serving both inbound and
  outbound trips may be near-side in one direction and far-side in the other.
  The classification reflects the dominant direction only.
- **OSM signal proximity ≠ same-street signal.** The 50 m match finds the
  nearest signal node, which may be on a crossing street rather than the bus's
  travel direction. In practice this affects corner stops where a signal governs
  the perpendicular road rather than the arterial the bus runs on.
- **OSM signal coverage is crowd-sourced.** The 2,820 county-wide signals are
  in the expected range, but completeness is higher in the City of Pittsburgh
  than in outer suburbs. Suburban stops near signals may appear as mid-block
  simply due to incomplete OSM coverage.
- **Lat/lon projection.** Shape projection uses Shapely on geographic
  coordinates (not projected), which is approximate. For the purpose of
  determining *order* along a route (near vs. far), this approximation is
  acceptable; the ambiguous threshold (5 m) filters co-located cases.
- **Ecological framing.** All OTP results are route-level associations. No
  trip-level or rider-level causal claims are made.

## Validation
1. **Data source verified.** Stops from `data/GTFS/stops.txt` (6,464 bus stops
   after excluding 4 station nodes). Signals from
   `data/osm-signals/traffic_signals_raw.json` (2,820 nodes; matches Analysis 51
   count). OTP from `otp_monthly` table, same query as prior analyses.
2. **Scope match.** GTFS stops and OSM signals both cover Allegheny County.
   OTP is averaged across all months per route (no temporal filter applied —
   consistent with route-level correlation approach).
3. **Null handling.** Stops without a canonical shape (no `stop_times` match)
   are excluded from near/far classification but counted as mid-block in
   system-wide totals. The 37 ambiguous stops are excluded from the near/far
   ratio and from the OTP correlation.
4. **Aggregate sanity check.** Total signalized stops (1,549) is 24% of all
   stops — plausible given that many PRT stops are on block faces away from
   intersections. 83% near-side is high but consistent with literature on older
   US bus networks. Far-side fraction (17%) is in the range reported for
   networks that have not undergone systematic stop placement policy.
5. **Surprising result check.** The 83% near-side finding is striking but
   explainable: PRT's stop infrastructure largely predates modern far-side
   guidance, and Pittsburgh's grid makes mid-block placement common, so
   intersection stops disproportionately reflect legacy near-side siting.
6. **Direction of effects.** The OTP correlation is in the expected direction
   (negative: more near-side → slightly lower OTP), even if non-significant.
   A positive coefficient would have been a red flag.
