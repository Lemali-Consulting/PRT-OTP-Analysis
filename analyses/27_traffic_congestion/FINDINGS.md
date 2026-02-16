# Findings: Traffic Congestion and OTP

## Summary
Total traffic volume (AADT) does **not** explain OTP variance after controlling for structural features (F=0.011, p=0.92). However, **truck percentage** is a significant predictor (p=0.006), jointly boosting R2 from 0.40 to 0.45. Routes with higher truck traffic perform better on-time, likely because truck-heavy corridors tend to be wider arterials with fewer stops and more predictable traffic flow.

## Key Numbers
- 89 routes analyzed (88 bus, 1 rail) after filtering match_rate >= 0.3
- Base model (6 structural features): R2 = 0.40, Adj R2 = 0.36
- Adding log(AADT): R2 = 0.40 (+0.0001), p = 0.92 -- **not significant**
- Adding log(AADT) + truck_pct: R2 = 0.45 (+0.05), joint F = 3.97, p = 0.023
- Truck percentage beta weight: +0.26 (p = 0.006), third-strongest predictor
- VIF for log_aadt = 1.17 -- no multicollinearity concern
- AADT range across matched routes: 4,181 -- 15,748 vehicles/day
- Top AADT routes: G3 (15,748), 28X (15,328), P12 (15,162)

## Observations
- **Traffic volume is orthogonal to OTP** once structural features are controlled. The bivariate correlation is weak (r = +0.01) and the partial residual plot shows no trend. Routes on high-traffic roads perform similarly to those on quieter ones.
- **Truck percentage captures road type**, not congestion. The positive coefficient (+0.021 OTP per 1% truck share) suggests that truck-heavy routes operate on highways/arterials with infrastructure advantages (dedicated lanes, longer signal phases, wider roads).
- The three excluded routes (BLUE, P1, SLVR) are rail/busway with match_rate < 0.3, confirming that the PennDOT road network does not cover dedicated transit rights-of-way.
- Bus-only subgroup shows the same null result: log_aadt F = 0.011, p = 0.92.
- The spatial match rate is high (median 80%), indicating good coverage of the PennDOT road network for bus routes.

## Discussion

The headline result is a null: traffic volume, the leading candidate for explaining the remaining 50% of OTP variance after structural features, contributes essentially nothing (R2 change of 0.01%). This is not a measurement failure -- the VIF of 1.17 confirms that AADT is nearly orthogonal to stop count and span, so it had every opportunity to capture independent variance. It simply doesn't.

Why not? The most likely explanation is that **AADT measures the wrong thing**. Annual average daily traffic smooths over the peak-hour congestion that actually delays buses. A road carrying 15,000 vehicles/day spread evenly across 24 hours is very different from one carrying the same total with 40% concentrated in two rush-hour peaks. PRT buses operate disproportionately during those peaks, so the congestion they experience is poorly proxied by a 24-hour average. Directional, time-of-day traffic counts -- or better yet, speed/travel-time data from probe vehicles -- would be a more direct test.

The truck percentage finding is the genuine contribution of this analysis. At +0.26 beta weight (third-strongest after stop count and span), truck share adds 5 percentage points of explained variance. But this almost certainly proxies for **road classification** rather than a direct truck-bus interaction. Roads with high truck percentages tend to be state highways and major arterials -- wider, with longer signal cycles, fewer pedestrian crossings, and more predictable traffic flow. The truck_pct variable is effectively encoding "this route runs on a highway" in a way that is_premium_bus failed to capture (since many non-premium routes also use arterial segments for part of their alignment).

This connects to the broader model-building narrative across Analyses 18, 26, and 27. The base model (stop count + span + mode) explains ~40% of variance. Adding n_munis as a suppressor pushes it to ~47%. Adding truck_pct pushes it to ~45% on the traffic-matched subsample. Ridership (Analysis 26) added nothing. The cumulative picture is that **roughly half of OTP variance is explained by route geometry and road type**, and the other half likely requires operational data (schedule padding, driver availability, vehicle condition, real-time traffic conditions) that is not in this dataset.

For policy, the null AADT result is actually useful: it suggests that rerouting buses to lower-traffic roads would not improve OTP, since traffic volume per se is not the problem. The truck_pct finding, if it indeed proxies for road type, suggests that routes spending more of their alignment on arterials (vs. neighborhood streets) perform better -- consistent with the stop count finding, since arterial segments typically have fewer stops per mile.

## Caveats
- AADT is an annual average; it does not capture peak-hour congestion, which is when buses run most frequently and are most affected. Directional or time-of-day traffic data would be a stronger test.
- PennDOT covers state routes; local streets (where many bus routes run) may be underrepresented.
- The truck_pct finding may proxy for road classification rather than a direct causal mechanism.
- The spatial matching uses a 30m buffer, which may associate routes with adjacent parallel roads in dense urban areas.
