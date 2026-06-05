# Findings: Stop Position and Near-Side Placement

## Summary
Near-side stop placement is **uniformly distributed along PRT routes** — it is
just as common at the start, middle, and end of a route. The near-side fraction
is virtually flat across all five position quintiles (81–85%, all within 4 pp of
the 83% system average), and a logistic regression of classification on
normalized position yields a negligible coefficient (−0.27, close to zero on the
log-odds scale). Splitting routes into first-half and second-half near-side
fractions does not improve the OTP correlation: both halves give r ≈ −0.12 to
−0.14, no better than the overall near-side fraction from Analysis 53. Position
along the route is not a meaningful moderator of the near-side/OTP relationship.

## Key Numbers
- **1,512 stops** matched to position data (near_side + far_side from Analysis 53).
- Near-side fraction by quintile: **82.9% / 82.8% / 85.0% / 81.3% / 81.4%** —
  range of only 3.7 pp, no systematic trend.
- Logistic regression coefficient on normalized position: **−0.27** (near-zero;
  the model predicts essentially the same near-side probability at every point).
- OTP correlations: overall r = −0.13, first-half r = −0.12, second-half
  r = −0.12. None significant (all p > 0.29, n = 63–64 routes).
- KDE of stop position: near-side and far-side stops have nearly identical
  distributions along the route — both roughly uniform with shallow humps near
  the 20% and 80% marks.

## Observations
- **No position gradient in near-side placement.** The hypothesis that PRT
  might have more far-side stops near terminals (where planners have more
  right-of-way flexibility) or more near-side stops in the busy middle of routes
  is not supported. Near-side is the default at every position.
- **Second-half placement is no better an OTP predictor than first-half.** The
  delay-accumulation argument — that a near-side stop at position 0.9 costs more
  than one at 0.1 — is theoretically sound but not detectable at the route level
  with the data available. The likely reason is the same as in Analysis 53: with
  80–100% near-side fraction everywhere on most routes, there is simply not
  enough variance between routes for either half to explain OTP.
- **Far-side stops have a mild second-half lean.** The KDE shows far-side stops
  slightly more concentrated in the 60–90% position range, while near-side stops
  are modestly more concentrated in the 10–40% range. The difference is subtle
  and not large enough to affect the quintile percentages, but it is consistent
  with the hypothesis that stops converted or planned as far-side tend to appear
  on the outbound half of routes where intersection geometry allows it.

## Discussion
This analysis closes the position-moderation question: knowing *where* along a
route a near-side stop sits does not add predictive power beyond knowing the
overall near-side fraction. The fundamental constraint from Analysis 53 remains
binding — near-side is so dominant (83% system-wide, 80–100% on most individual
routes) that there is very little cross-route variance to correlate with anything.

Testing the near-side/OTP mechanism properly would require stop-level or
trip-level arrival time data (e.g., AVL logs or GTFS-RT archives) to compare
actual dwell and departure times at near-side vs. far-side stops controlling for
time-of-day, headway, and weather.

## Caveats
- **Canonical trip only.** Each stop is assigned to one canonical trip (longest
  shape for its shape_id). Position on other trips may differ slightly.
- **OTP is route-level, not stop-level.** The route OTP used here is the
  monthly average across all stops and all trips; it does not capture within-
  route delay accumulation patterns.
- **Ecological framing.** All correlations are route-level. No stop-level or
  rider-level causal claims are made.

## Validation
1. **Data source verified.** Classifications from
   `analyses/53_stop_signal_placement/output/stop_classifications.csv`; stop
   sequences from `data/GTFS/stop_times.txt`. Position computation checked: the
   range of normalized position is [0, 1] and the quintile counts are
   approximately equal (286, 309, 301, 310, 306).
2. **Null handling.** 37 stops from Analysis 53 had no `stop_times` match after
   joining on shape_id + stop_id; these are silently dropped (inner join).
3. **Flat quintile chart inspected.** The near-constant bars (81–85%) are
   consistent with a near-uniform distribution confirmed by the KDE. A
   systematic gradient of ≥5 pp would have been flagged for investigation.
4. **Direction of logistic coefficient.** The coefficient (−0.27) indicates
   slightly *fewer* near-side stops toward the end of routes, consistent with
   the mild far-side lean seen in the KDE second half. Sign is as expected from
   the KDE; magnitude is too small to be operationally significant.
