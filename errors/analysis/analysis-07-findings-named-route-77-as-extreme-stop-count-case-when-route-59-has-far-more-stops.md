---
title: Analysis 07 FINDINGS named route 77 as extreme stop-count case when route 59 has far more stops
date: 2026-05-15T18:12:25Z
---

## What happened

The Observations section of `analyses/07_stop_count_vs_otp/FINDINGS.md` stated:
"Route 77 (Penn Hills) is an extreme case: 258 stops and among the worst OTP in
the system." Route 77 is *not* the extreme stop-count route. Route 59 (Mon
Valley) has 334 stops -- 76 more than Route 77 and 30% above the next-highest
route -- and is the lone point on the far right of the scatter, well separated
from the cluster.

The narrative was inaccurate in two ways:

1. It named the wrong route as the stop-count extreme.
2. By only discussing a route that fits the negative-correlation story
   (Route 77: many stops, bad OTP), it skipped the route that *contradicts* the
   simple narrative. Route 59 has the most stops in the system yet runs at
   0.69 OTP -- about 13 percentage points (2.3 residual SDs) *above* the bus
   trendline, which predicts ~0.56 at 334 stops.

No numbers in the analysis were wrong -- the correlations and CSV were correct.
The error was purely in the written interpretation, which under-reported a
high-leverage, trend-defying route.

## How it was discovered

A review of the Analysis 07 scatter plot showed an isolated point at x=334 far
to the right of all others. Sorting `output/stop_count_otp.csv` by stop count
confirmed Route 59 (334) sat above Route 77 (258). Leverage analysis showed
Route 59 has hat-matrix leverage h=0.19 -- roughly 9x the average and well past
the 3*(2/n) high-leverage cutoff. Dropping it strengthens the bus Pearson
correlation from -0.498 to -0.551, i.e. the point was slightly masking the
relationship the analysis reports.

A data-quality check confirmed Route 59's 334-stop count is genuine, not a
join or branch-union artifact: all 332 of its stops carry an identical
`trips_7d` of 162 in `route_stops` (a single service pattern), and the stops
span 17 contiguous Mon Valley municipalities. (By contrast Route 77 has six-plus
distinct `trips_7d` tiers, so its 258 stops are a union across branches.)

## What was done

- Corrected `FINDINGS.md` (local and root): Route 59 is now identified as the
  extreme stop-count route, with its above-trend OTP explained and its stop
  count confirmed genuine. Route 77 is reframed as the worst-performing
  high-stop route rather than the stop-count extreme.
- Added a leverage-robustness check to `main.py` (`_high_leverage` helper):
  the bus Pearson correlation is recomputed after dropping high-leverage routes
  (flagged by `h > 3*(2/n)`). It excludes routes 59 and 77, giving r=-0.52
  (n=87) -- confirming the headline finding is not an artifact of the
  extreme-stop routes. The result is reported in `main.py` output and in both
  FINDINGS files.
- Annotated routes 59 and 77 on the scatter chart so the influential points are
  visible to readers.
- Documented the leverage check in `METHODS.md` and added a `## Validation`
  section to the local `FINDINGS.md`.

## Relevant commits

Fixed in the same commit that records this report; see `git log` for
`analyses/07_stop_count_vs_otp/`.
