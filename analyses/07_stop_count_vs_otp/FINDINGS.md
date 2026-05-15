# Findings: Stop Count vs OTP

## Summary

There is a **moderately strong negative correlation** between the number of stops on a route and its average OTP. This finding holds for both all routes and bus-only analysis, ruling out Simpson's paradox as a confounder.

## Key Numbers

- **All routes: Pearson r = -0.53** (p < 0.001, n = 92)
- **Bus only: Pearson r = -0.50** (p < 0.001, n = 89)
- **Bus only: Spearman r = -0.49** (p < 0.001)
- **Bus only, excluding 2 high-leverage routes (59, 77): Pearson r = -0.52** (p < 0.001, n = 87)
- Routes with < 50 stops: typically 80%+ OTP
- Routes with 150+ stops: typically below 60% OTP

Routes with fewer than 12 months of OTP data are excluded to avoid noisy averages from sparse observations.

## Observations

- The bus-only correlation (r = -0.50) is nearly as strong as the all-routes correlation (r = -0.53), confirming that the effect is not driven by the BUS/RAIL mode split (Simpson's paradox). Stop count predicts OTP within the bus mode alone.
- The Spearman rank correlation (r = -0.49) is consistent with the Pearson, indicating the relationship is approximately monotonic without being driven by outliers or non-linearity.
- Every stop adds dwell time (boarding/alighting), traffic signal delay, and schedule recovery risk. The cumulative effect is substantial.
- Busway and rail routes tend to have fewer stops and dedicated right-of-way, giving them a double advantage.
- **Route 59 (Mon Valley) is the extreme stop-count route**: 334 stops, 76 more than the next-highest route, winding through 17 Mon Valley municipalities. It is a high-leverage point on the scatter (leverage ~9x the average) and sits well *above* the trendline -- 0.69 OTP versus the ~0.56 the bus trend predicts at 334 stops. Despite the most stops in the system, it performs better than the model expects, likely because a dwell-heavy urban route carries a generously padded schedule. Its stop count is genuine, not a data artifact: every stop is served by the same single trip pattern (no branch-union inflation).
- Route 77 (Penn Hills), at 258 stops, is the *worst-performing* high-stop route (0.56 OTP) -- the clearest illustration of the negative relationship. Unlike Route 59, it runs several branches, so its stop count is a union across patterns no single trip serves.
- Excluding the two high-leverage routes (59 and 77) leaves the bus correlation essentially unchanged (r = -0.50 -> -0.52), so the headline relationship is not an artifact of the extreme-stop routes. Route 59 alone slightly *masks* the relationship: dropping just that point strengthens the bus Pearson to r = -0.55.

## Implication

Stop consolidation -- reducing the number of stops on long routes -- is a common transit strategy for improving schedule adherence. This data strongly supports that approach for PRT's worst-performing routes.

## Caveats

- Correlation is not causation. Routes with many stops also tend to serve congested corridors, cover longer distances, and carry more passengers -- all of which independently affect OTP.
- **Temporal mismatch:** Stop counts come from the current `route_stops` snapshot while OTP is averaged across all historical months (2019--2025). Routes that changed stop configurations during this period have a mismatch between their current stop count and earlier OTP observations. This is inherent to the available data and cannot be corrected without historical stop-count snapshots.

## Validation

- **Surprising point investigated (checklist #5).** Route 59's 334 stops -- 30% above the next-highest route -- was audited before being written up. In `route_stops` all 332 of its stops share an identical `trips_7d` of 162, indicating a single service pattern with no branch-union inflation; its stops span 17 contiguous Mon Valley municipalities. The count is a genuine long route, not a join error.
- **Outlier influence checked (checklist #5, #8).** The bus regression has two high-leverage routes by the `h > 3*(2/n)` rule (59 and 77). The leverage-robustness check recomputes the bus Pearson with them removed (r = -0.52, n = 87); the headline finding is stable. Both extreme-stop routes are annotated on the chart.
- **Small-sample routes flagged (checklist #8).** Routes with fewer than 12 months of OTP data are excluded (`HAVING COUNT(*) >= 12`).
- **Ecological framing (checklist #9).** Results are route-level associations between stop count and average OTP; no individual-trip or individual-rider claims are made.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) — 6 issues (0 significant). Added 12-month minimum filter, temporal mismatch note in METHODS.md, `all_n` tracking, replaced manual regression with `linregress`, added min-n guard, updated METHODS.md for Pearson+Spearman.
