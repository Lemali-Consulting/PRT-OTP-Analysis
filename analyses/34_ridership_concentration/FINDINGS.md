# Findings: Ridership Concentration (Pareto)

## Summary
PRT ridership is extremely concentrated: just 2% of stops serve 50% of all weekday riders, and 14% of stops serve 80%. The system-wide Gini coefficient is 0.82, indicating very high inequality in stop-level usage. However, per-route ridership concentration (Gini) has essentially zero correlation with that route's OTP (r = -0.016, p = 0.88), meaning whether a route's riders are clustered at a few stops or spread evenly has no bearing on schedule reliability.

## Key Numbers
- **2.2%** of stops serve **50%** of ridership
- **13.9%** of stops serve **80%** of ridership
- **27.9%** of stops serve **90%** of ridership
- System-wide **Gini = 0.824**
- Per-route Gini range: **0.338 - 0.890** (median 0.649)
- **95** routes with >= 3 stops analyzed
- **90** routes matched to OTP data
- Gini vs OTP (bus-only): **Pearson r = -0.016** (p = 0.879), **Spearman rho = 0.103** (p = 0.339)

## Observations
- **The Pareto curve is steep**: the top ~150 stops (out of 6,700+) account for half of all weekday boardings and alightings. This is more extreme than a classic 80/20 rule -- it's closer to a 2/50 pattern.
- **Most stops see very little usage**: the median stop handles only ~7 riders/day, while the top stops see 2,000-5,800/day. The bottom 70% of stops collectively serve only 10% of ridership.
- **Route-level concentration varies widely**: some routes have Gini as low as 0.34 (relatively even usage across stops) while others reach 0.89 (nearly all ridership at a few stops). Flyer/express routes tend to have higher Gini since ridership clusters at downtown endpoints.
- **Concentration does not predict OTP.** The scatter plot shows no trend at all -- the regression line is essentially flat. Routes with highly concentrated ridership perform no better or worse than those with evenly distributed usage.

## Discussion
The extreme system-wide concentration (Gini = 0.82) reinforces the stop consolidation finding from Analysis 31: most stops contribute very little ridership, and removing the lowest-usage ones would affect few riders while potentially improving OTP by reducing stop count.

The null result for Gini vs OTP is notable. One might hypothesize that routes with concentrated ridership would have better OTP (less dwell time at most stops), but this doesn't hold. This suggests that dwell time at individual stops is not a dominant factor in OTP variance -- the time cost of *stopping* (deceleration, door opening, acceleration) matters more than the time cost of *boarding passengers*. This aligns with the Analysis 07 finding that raw stop count, not passenger volume, drives OTP.

The 2/50 concentration ratio has resource allocation implications: if PRT focused infrastructure investment (shelters, real-time signs, ADA upgrades) on just 150 stops, it would reach half of all riders. The current shelter coverage of 7% (Analysis 32) suggests significant room to target the highest-impact locations.

## Caveats
- Stop-level usage data is from FY2019; current patterns may differ, especially post-pandemic.
- Gini is computed from stop-route combinations, not physical stops. Routes sharing physical stops may inflate the apparent concentration.
- The OTP data covers a longer time range (2019-2025) than the usage snapshot (2019), so the correlation compares static usage structure against time-averaged OTP.
- Very short routes (< 3 stops) are excluded from the Gini analysis, which drops a few incline and shuttle routes.
