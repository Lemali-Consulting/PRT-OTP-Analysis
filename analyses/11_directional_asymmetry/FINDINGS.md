# Findings: Directional Asymmetry

## Summary

The correlation between directional trip imbalance and OTP is **weak (r = 0.17)**. This hypothesis did not yield actionable findings.

## Key Numbers

- **Pearson r = 0.17** (91 routes)
- Most routes cluster near 0% asymmetry (well-balanced IB/OB)
- 2 routes show 100% asymmetry (data artifact)

## Most Asymmetric Routes

| Route | IB Trips | OB Trips | Asymmetry | OTP |
|-------|----------|----------|-----------|-----|
| 11 - Fineview | 0 | 1,375 | 1.000 | 75.6% |
| 60 - McKeesport-Walnut | 0 | 1,287 | 1.000 | 78.3% |
| 39 - Brookline | 1,140 | 805 | 0.172 | 78.9% |
| P12 - Holiday Park Flyer | 260 | 192 | 0.150 | 66.8% |
| 71A - Negley | 1,953 | 2,457 | 0.114 | 64.5% |

## Observations

- Routes 11 and 60 appear 100% asymmetric because `route_stops` only contains OB trip data for them. This is likely a data recording issue (the IB stops exist but weren't captured), not genuinely one-directional service.
- Excluding those two outliers, the remaining routes show very little asymmetry (max ~17%), and no correlation with OTP.
- The weak positive correlation (r = 0.17) is the opposite of the hypothesis -- slightly asymmetric routes actually perform *slightly better*, not worse. But the effect is too small to be meaningful.

## Conclusion

Directional imbalance, as measured from `route_stops`, does not predict OTP. The hypothesis assumed that scheduling asymmetry creates operational strain, but in practice, PRT routes are sufficiently balanced that this is not a measurable factor.

## Caveats

- Stops with `direction = 'IB,OB'` were excluded from the analysis since they can't be split into directional counts.
- The `route_stops` data reflects current service, not historical. Historical asymmetry may have differed.
