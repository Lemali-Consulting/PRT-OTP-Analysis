# Findings: Trip Frequency vs OTP

## Summary

There is **no meaningful correlation** between peak weekday trip frequency and OTP. The previous finding (r = -0.39) was an artifact of using `SUM(trips_wd)` across stops, which conflated frequency with route length. After correcting to `MAX(trips_wd)` (peak frequency at any single stop), the correlation vanishes.

## Key Numbers

- **All routes: Pearson r = 0.03** (p = 0.81, n = 92) -- essentially zero
- **Bus only: Pearson r = -0.06** (p = 0.55, n = 89)
- **Bus only: Spearman r = -0.11** (p = 0.29)

## Methodology Note

The original analysis summed `trips_wd` across all stops on a route. Because `trips_wd` is recorded per stop, a route with 50 trips per day and 100 stops produces a sum of ~5,000, while a route with 50 trips per day and 20 stops produces ~1,000. This made the metric a proxy for `frequency x stop_count` rather than pure frequency. Using `MAX(trips_wd)` isolates the peak trip frequency at the busiest stop, which is a better measure of how often the route actually runs.

## Observations

- Running more trips per se does not degrade OTP. The previous apparent correlation was entirely driven by the confounding of frequency with route length (stop count).
- This result is consistent with Analysis 07's finding that stop count is the real structural predictor -- once route complexity is removed from the frequency metric, the effect disappears.
- Some of the highest-frequency routes (P1 East Busway, RAIL lines) actually have excellent OTP, because they combine high frequency with few stops and dedicated right-of-way.

## Implication

PRT should not expect OTP penalties from increasing service frequency on existing routes. The capacity to run more trips does not inherently strain schedule adherence. The real lever for improving OTP is route design (stop count, right-of-way), not service volume.

## Caveats

- `trips_wd` in `route_stops` represents current weekday frequency, not historical. Frequency may have changed over the analysis period.
- `MAX(trips_wd)` captures the peak stop, which for short-turn routes may overstate the frequency experienced by riders at outer stops.
- Routes with fewer than 12 months of OTP data are excluded (1 route dropped vs prior version).
- Three correlation tests were run (Pearson all-routes, Pearson bus-only, Spearman bus-only) without multiple-comparison correction. Since all three are non-significant (smallest p = 0.29), correction would not change any conclusion.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) -- 6 issues (1 significant). Updated METHODS.md to reflect MAX(trips_wd) instead of SUM; documented all three correlation tests; added minimum-month filter (HAVING COUNT >= 12); added NULL filter for trips_wd; replaced manual regression with scipy.stats.linregress; noted multiple-test caveat.
