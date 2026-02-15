# Findings: OTP -> Ridership Causality

## Summary
There is **no evidence that OTP declines predict subsequent ridership losses**. After detrending and Bonferroni correction, zero of 93 routes show statistically significant Granger causality from OTP to ridership. The raw cross-correlations are weakly *negative*, suggesting the opposite direction: months with lower ridership tend to have better OTP.

## Key Numbers
- **Granger causality**: 8/93 routes significant at p < 0.05 uncorrected; **0/93 after Bonferroni correction**
- **Median cross-correlation at lag 0**: r = -0.18 (IQR: [-0.41, +0.10])
- **Median cross-correlation at lag 1**: r = -0.15 (IQR: [-0.38, +0.09])
- Cross-correlations are flat across lags 0--6 -- no dominant lag emerges
- 93 routes with 36+ months of paired OTP + ridership data (57--70 months each)
- Both series detrended by subtracting system-wide monthly mean before testing

## Observations
- The p-value histogram is roughly uniform (with a small pile-up near zero), consistent with the null hypothesis being true for most routes.
- Of the 8 nominally significant routes, 3 have best lag = 1 month and the rest are scattered across lags 2--6. No consistent lag structure emerges.
- The weakly negative contemporaneous correlation (median r = -0.18) is consistent with **reverse causality**: months when fewer people ride (summer, holidays) see better OTP because of reduced dwell times and less crowding, not because good OTP attracts riders.

## Discussion
The hypothesis that poor OTP drives riders away is intuitive, but this data cannot confirm it. Several factors may explain the null result:
- **Temporal resolution is too coarse**: monthly data may be too slow to capture rider responses, which could operate at the trip or week level.
- **Riders have limited alternatives**: in a single-provider transit system, riders may tolerate poor OTP because they have no substitute, especially for commute trips.
- **Confounders dominate**: ridership is driven primarily by employment, gas prices, weather, and COVID -- factors far larger than OTP fluctuations. The detrending removes system-wide trends but not route-specific confounders.
- **Reverse causality may mask the effect**: if high ridership causes poor OTP (crowding, dwell times) while poor OTP also causes ridership loss, the two effects partially cancel.

## Caveats
- Granger causality tests linear predictive ability, not true causation. A null result does not prove OTP has no effect on ridership.
- The 70-month overlap period with monthly granularity gives limited statistical power for 6-lag models (effective sample ~60 per route).
- Detrending removes system-wide trends but not route-specific shocks (e.g., service changes, construction).
- Bonferroni correction is conservative; a less strict correction (e.g., Benjamini-Hochberg) might yield a few significant routes, but the overall pattern would remain weak.
