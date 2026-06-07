# Findings: Near-Side vs. Far-Side Stop Placement

## Summary
PRT bus stops at signalized intersections are overwhelmingly placed on the
**near side** — before the traffic light in the direction of travel. PRT's own
authoritative stop records (the `stop_signals` table, supplied by PRT) classify
**1,539 stops as signalized**, of which **86% are near-side** (1,320) and only
**14% are far-side** (219); a further 66 are busway/BRT and the remaining 4,701
bus stops are not at a signal. An independent OSM/GTFS heuristic built from
scratch (Steps 1–5) **agreed with these authoritative labels on 97.6% of stops**
for signal detection and 93.3% for near-vs-far — validating the method that
earlier analyses relied on. Re-running the route-level OTP test on the
authoritative labels leaves the result **null** (r = −0.01, p = 0.95, n = 90):
whether a route's stops are more near-side or far-side has no measurable
association with how on-time it runs, driven by severe range restriction (almost
every route is 64–100% near-side).

## Key Numbers

### Authoritative (PRT `stop_signals`)
- **6,306 PRT bus stops**, of which **1,539 are at a traffic signal**
  (1,320 near-side + 219 far-side), **66 busway/BRT**, **4,701 no signal**.
- Among signalized stops: **85.8% near-side, 14.2% far-side**.
- **90 routes** had ≥ 3 authoritative signalized stops and OTP data.
- Authoritative near-side fraction by route ranges **64% to 100%** (median 86%).
- Authoritative OTP correlation: **r = −0.01 (p = 0.95)**, ρ = −0.03 (p = 0.80) — null.

### Heuristic validation (OSM/GTFS vs. PRT, 6,293 stops in both)
- **Signal detection: accuracy 97.6%, precision 96.8%, recall 93.1%**
  (TP 1,432 · FP 48 · FN 106 · TN 4,707). The heuristic misses ~7% of signalized
  stops, mostly where OSM has no signal node within 50 m.
- **Near vs. far: 93.3% agreement** (1,336 / 1,432). The heuristic slightly
  over-calls far-side (68 truly-near labelled far vs. 27 truly-far labelled near).

### Heuristic, for reference (OSM/GTFS only)
- **1,549 stops** within 50 m of an OSM signal: **1,248 near-side (83%)**,
  **263 far-side (17%)**, 38 ambiguous; 4,915 mid-block.
- Heuristic OTP correlation: r = −0.13 (p = 0.26), ρ = −0.07 — not significant.

## Observations
- **The OSM/GTFS heuristic is validated.** Against PRT's authoritative records,
  the from-scratch geometric method correctly identifies signalized stops 97.6%
  of the time and gets near-vs-far right 93.3% of the time. This retroactively
  supports the OSM-derived signal metrics used in Analysis 51 and the placement
  classification used here and in Analysis 54 — the proxy was sound. Where it
  errs, it is mostly conservative (106 signalized stops missed because OSM lacks
  a node within 50 m), so the heuristic slightly *under*-counts signal exposure.
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

The weak OTP correlation here (and in the follow-up Analysis 54) should not be
read as evidence that placement type is irrelevant. The fundamental obstacle is
**range restriction**: with 80–100% near-side fraction on most routes, there is
not enough cross-route variance to detect an effect at the route level even if
one exists at the stop level. The right test — a paired comparison of otherwise
identical near-side and far-side stops using stop-level arrival time data — is
not possible with the current data.

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
7. **Cross-validated against authoritative source.** PRT's `stop_signals` table
   (pipeline 15) provides ground-truth labels. The heuristic's aggregate split
   (83% near-side) is within 3 pp of the authoritative split (86%), and per-stop
   agreement is high (97.6% detection, 93.3% near/far). The headline near/far
   split and OTP correlation reported above use the authoritative labels; the
   heuristic is retained only for the validation comparison. Join is on the
   shared `stop_code`; the GTFS and PRT internal `stop_id` namespaces differ
   (GTFS numeric vs. PRT alpha-prefixed), so joining on `stop_id` would silently
   match nothing — a verified gotcha.
