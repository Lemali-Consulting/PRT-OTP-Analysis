# Findings: Directional Asymmetry

## Summary

The correlation between directional trip imbalance and OTP is **weak and not statistically significant** (r = -0.12, p = 0.26). After correcting methodology issues in the original analysis, PRT routes show very little directional asymmetry, and what asymmetry exists does not predict OTP.

## Key Numbers

- **All routes: Pearson r = -0.12** (p = 0.26, n = 90)
- **Bus only: Pearson r = -0.12** (p = 0.28, n = 87)
- **Bus only: Spearman r = -0.17** (p = 0.11)
- Maximum asymmetry index: 0.077 (Route 19L)

## Methodology Note

The original analysis used `SUM(trips_wd)` per direction and excluded stops with `direction = 'IB,OB'`. This inflated asymmetry because IB,OB stops (common on shared corridors) were dropped rather than counted in both directions. Routes 11 and 60 appeared 100% asymmetric because their IB stops were all coded as IB,OB. The corrected analysis uses `MAX(trips_wd)` per direction (peak frequency, not total stop-visits), includes IB,OB stops in both directions, and excludes routes present in only one direction.

## Most Asymmetric Routes

| Route | IB Trips | OB Trips | Asymmetry | OTP |
|-------|----------|----------|-----------|-----|
| 19L - Emsworth Limited | 7 | 6 | 0.077 | 66.0% |
| 67 - Monroeville | 27 | 25 | 0.038 | 60.4% |
| 29 - Robinson | 22 | 21 | 0.023 | 65.1% |

## Observations

- With corrected methodology, PRT routes are remarkably balanced directionally. The most asymmetric route (19L) has only a 7.7% imbalance (7 vs 6 trips), and most routes are at or near 0%.
- The previous finding of routes with 100% asymmetry (Routes 11 and 60) was a data artifact caused by excluding bidirectional (IB,OB) stops. These routes are excluded in the corrected analysis because they lack separate IB and OB data after the fix.
- The slight negative correlation (r = -0.12) suggests marginally worse OTP with more asymmetry, but the effect is too small and not statistically significant.

## Conclusion

Directional imbalance does not predict OTP. PRT routes are sufficiently balanced that this is not a measurable factor in schedule adherence. The hypothesis that scheduling asymmetry creates operational strain is not supported by this data.

## Caveats

- The analysis uses peak trip frequency (`MAX(trips_wd)`) at a single stop per direction, which may not capture all scheduling nuances.
- The `route_stops` data reflects current service, not historical. Historical asymmetry may have differed.
