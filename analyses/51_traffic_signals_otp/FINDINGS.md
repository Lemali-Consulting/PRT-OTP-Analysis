# Findings: Traffic Signals and OTP

## Summary
Traffic-signal density is a **strong, independent predictor of on-time
performance**. Routes that pass more traffic signals per mile run measurably
later: adding signal density to the six-feature structural model lifts explained
OTP variance from 47% to 60% (adjusted R-squared 0.43 to 0.57), and signal
density remains highly significant after controlling for stop count, route
length, mode, and municipal reach (F-test p < 0.0001). Each additional signal
per route-km is associated with roughly **1.75 percentage points lower OTP**.
This contrasts sharply with Analysis 27, which found that traffic *volume*
(AADT) had no effect — it is the fixed, repeated stop-and-wait of signals, not
how busy the road is, that tracks with delay.

**Independently confirmed by PRT's authoritative records.** PRT supplied a
per-stop signal classification (the `stop_signals` table). The share of a route's
stops that sit at a signal — a completely independent measure of signal exposure
— predicts OTP just as strongly (r = −0.50; +13.9 R-squared points beyond the
structural model, F = 29.9, p < 0.0001) and agrees with the OpenStreetMap
density measure (r = +0.61). When both are entered together they remain
significant and non-collinear (VIF ≈ 2.4 each), so the conclusion does not hinge
on the crowd-sourced OSM data.

## Key Numbers
- **92 routes** analyzed (89 bus, 3 rail) with 12+ months of OTP data and matched
  signal data.
- **2,820 OpenStreetMap traffic signals** county-wide were matched to GTFS route
  shapes within a 30 m buffer.
- Signal density ranges **0.89 to 7.83 signals/km** (median ~3.2).
- Bivariate correlation: signal density vs OTP **r = -0.38** (p = 0.0002).
- Base structural model R-squared **0.472** → expanded model **0.602**
  (adjusted 0.435 → 0.569); nested **F-test p < 0.0001**.
- Expanded-model signal-density coefficient **-0.0175** (beta weight -0.42,
  p < 0.0001) — about **-1.75 pp OTP per +1 signal/km**.
- **VIF for signal density = 1.35** (all predictors < 5) — no multicollinearity.
- Bus-only: base R-squared 0.379 → 0.532 (F = 26.9, p < 0.0001, beta -0.45).

### Authoritative cross-validation (PRT `stop_signals`)
- **PRT signalized-stop share vs OSM signal density: r = +0.61** (p < 0.0001);
  PRT signalized-stop count vs OSM signal count: **r = +0.76**. The two
  independent signal-exposure measures agree.
- PRT signalized-stop share vs OTP: **r = −0.50** (p < 0.0001) — the
  stop-normalized, honest predictor. (Raw count r = −0.70, but it tracks
  stop_count and is confounded, exactly as raw OSM `n_signals` is.)
- Authoritative model (base + sig_stop_share): R-squared **0.472 → 0.611**
  (+0.139, F = 29.9, p < 0.0001), beta −0.44 — slightly stronger than the OSM
  density model (+0.130).
- Combined model (base + density + share): R-squared **0.635**; both signal
  measures stay significant (density p = 0.022, share p = 0.008) with **VIF ≈ 2.4
  each** — distinct, non-redundant facets of signal exposure.

## Observations
- **Raw signal count overstates the effect.** Raw `n_signals` correlates with
  OTP at r = -0.65, but it also correlates with route length at r = +0.47 — a
  long route passes more signals *and* tends to run later. Dividing by route
  length isolates the signal effect: signal *density* correlates with OTP at the
  more modest r = -0.38. The regression therefore uses density, not count.
- **Signal density is nearly orthogonal to stop count** (r = -0.04). Stops and
  signals are two separate delay mechanisms — a route can have many stops and
  few signals, or vice versa — and the model picks up both: in the bus-only
  expanded model stop count (beta -0.48) and signal density (beta -0.45) are
  comparably strong, independent predictors.
- **Density still correlates with other geometry** (span -0.32, municipal reach
  -0.39, premium-bus -0.33): suburban and express routes run on faster roads
  with fewer signals. But the VIF of 1.35 confirms enough independent variation
  remains for a stable coefficient.
- **The densest-signal routes are inner-city local bus.** The top of the list is
  71B Highland Park (7.83 signals/km, 59% OTP), 81 Oak Hill, 83 Bedford Hill,
  82 Lincoln — all dense East End / Hill District local routes. The sparsest are
  suburban routes such as 79 East Hills (0.89/km, 71% OTP) and 14 Ohio Valley.
- **Contrast with traffic volume (Analysis 27).** AADT had no effect on OTP after
  structural controls; signal density clearly does. Signals impose a fixed,
  stochastic delay every cycle regardless of how heavy traffic is, which is a
  more plausible mechanism for the kind of variance OTP measures.
- **PRT's authoritative records independently confirm the result.** The OSM
  signal exposure was never ground-truthed before. PRT's per-stop classification
  gives a second, independent measure (what fraction of a route's stops are at a
  signal); it correlates with the OSM measure (r = +0.61) and predicts OTP just
  as strongly (r = −0.50, +13.9 R-squared points). The two measures are not
  redundant (VIF ≈ 2.4 when combined): OSM density counts every signal the route
  *passes* (including at non-stop intersections), while the PRT share counts
  signals where the bus actually *stops* — two facets of the same delay story.

## Discussion
The result reinforces the cumulative picture from Analyses 18, 26 and 27 that
OTP is largely a function of route *structure*. Signal density adds a genuinely
new structural axis: it is not captured by stop count (the two are orthogonal)
and it explains a meaningful slice of variance the earlier models missed
(+13 R-squared points). For policy, the lever is transit-signal priority (TSP)
and corridor signal-timing coordination on the dense East End local routes,
rather than rerouting — the densest-signal routes are exactly the high-ridership
city corridors where rerouting is not an option. The effect is an area-level
association, not a trip-level causal estimate; it identifies where signal
treatment is most likely to help, not the exact OTP gain a specific TSP project
would deliver.

## Caveats
- **OpenStreetMap signal coverage is crowd-sourced.** The 2,820 county-wide
  signals fall in the plausible range for Allegheny County (~2,500–3,000), but
  coverage completeness may vary, likely better in the City of Pittsburgh than
  in outer suburbs.
- **Density numerator/denominator mismatch.** `n_signals` counts unique signals
  along the union of all of a route's GTFS shape variants (both directions, all
  patterns), while `length_km` is the route's single longest shape. Where the
  two directions use different parallel streets this modestly inflates density.
  Most PRT routes run both directions on the same arterials, limiting the effect.
- **Raw signal count is mechanically tied to route length** and is reported
  descriptively only; it is never used as a regression predictor.
- **Ecological framing.** All results are route-level associations between signal
  density and average OTP. No trip-level or rider-level causal claims are made.
- **OLS assumes linear, independent errors.** With 92 observations and 7
  predictors the model is reasonably but not generously powered.

## Validation
- **Data source verified (checklist #1).** `route_signals` is produced by
  pipeline step `11_signal_overlay`; its columns were validated against the
  `ROUTE_SIGNALS` schema with `validate(..., subset=True)`. GTFS and OTP columns
  reuse the same queries as Analysis 27.
- **Scope match (checklist #2).** All routes are filtered to 12+ months of OTP
  and inner-joined to `route_signals`; signals and routes both cover Allegheny
  County. 92 of 98 signal-matched routes clear the 12-month OTP threshold.
- **Null handling (checklist #3).** `signal_density` is non-null for every route
  (all routes have non-zero shape length); `drop_nulls` guards the structural
  features. No routes were silently dropped.
- **Aggregate sanity check (checklist #4).** Total OSM signal count (2,820) was
  compared against the known Allegheny County signal inventory order of
  magnitude (~2,500–3,000) and is consistent. Per-route densities (0.9–7.8/km)
  imply a signal every 130–1,100 m, plausible for city arterials vs suburban
  roads.
- **Direction of effect (checklist #6).** More signals per km is associated with
  *lower* OTP — the expected sign. A positive coefficient would have been a red
  flag.
- **Multicollinearity checked (checklist #7).** VIF is reported for every
  expanded-model predictor; the maximum is 2.66 and signal density is 1.35. No
  predictor exceeds the VIF > 5 flag threshold.
- **Small-sample routes flagged (checklist #8).** Routes with fewer than 12
  months of OTP data are excluded via `HAVING COUNT(*) >= 12`. The
  `route_signals.match_rate` field is *not* used as a filter — unlike the
  PennDOT road-network match rate in Analysis 27, it is proportional to signal
  density and is not a coverage-quality signal.
- **Surprising-result check (checklist #5).** The headline (signal density
  matters where traffic volume did not) was checked for plausibility: signals
  impose fixed per-cycle delay, a sound mechanism, and the raw-count vs density
  diagnostic confirmed the relationship is not a route-length artifact.
- **Ecological framing (checklist #9).** Documented in Caveats and Discussion;
  results are described as route-level associations throughout.
- **Cross-validated against an authoritative source (checklist #5).** The OSM
  signal-density measure was checked against PRT's `stop_signals` records
  (pipeline 15). The two agree (r = +0.61 share vs density; r = +0.76 counts),
  and the authoritative measure reproduces the OTP relationship independently.
  Aggregation joins `stop_signals` → `route_stops` on the PRT internal `stop_id`
  (E-code namespace, shared between those two tables); the OSM/GTFS join in
  Analysis 53 instead keys on `stop_code` — the two stop-id namespaces differ.
