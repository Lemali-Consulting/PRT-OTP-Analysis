# Findings: Service Level vs OTP Longitudinal

## Summary

Within-route month-over-month changes in scheduled trip frequency have **no significant relationship** with OTP changes after detrending. This null result holds across all routes, bus-only, and in both pre- and post-COVID subperiods.

## Key Numbers

- **2,374 delta observations** from 93 routes over 27 months (Jan 2019 -- Mar 2021)
- **All routes:** slope=0.00002, Pearson r=0.018 (p=0.39), Spearman rho=-0.030 (p=0.15)
- **Bus only (n=2,288):** slope=0.00002, Pearson r=0.023 (p=0.26), Spearman rho=-0.031 (p=0.13)
- **Pre-COVID (n=1,195):** slope=-0.004, r=-0.052 (p=0.07) -- marginally negative
- **Post-COVID (n=1,179):** slope=0.00002, r=0.030 (p=0.31) -- null

## Observations

- The overall effect is essentially zero: a change in daily trip count explains less than 0.1% of the variance in detrended OTP changes.
- This confirms Analysis 10's cross-sectional null finding with a stronger longitudinal design that controls for all time-invariant route characteristics (geography, length, mode).
- The pre-COVID period shows a marginally significant negative slope (r=-0.052, p=0.07), suggesting that adding trips slightly degraded OTP when the system was running near capacity. However, this is borderline and does not survive Bonferroni correction for multiple comparisons.
- The post-COVID period shows no relationship at all, consistent with reduced ridership creating slack in the system.
- The Spearman correlations are consistently negative but not significant, hinting that the relationship (if any) is slightly negative -- more service slightly worsens on-time performance -- but the effect is too small to detect reliably in this sample.

## Discussion

This null result is the most methodologically rigorous frequency-OTP test in the project. Analysis 10 was cross-sectional (comparing different routes at one point in time) and confounded by route characteristics -- long routes have both more trips and worse OTP for structural reasons. This analysis controls for all time-invariant route features by using within-route changes over time, and detrends to remove system-wide shocks. The result is unambiguous: **trip frequency changes do not predict OTP changes within routes**.

The marginally negative pre-COVID slope (r=-0.052, p=0.07) is the one signal worth noting. Before COVID, the system was operating near capacity, and adding trips to an already-constrained route may have slightly degraded schedule adherence -- each additional trip competes for the same road space, layover time, and driver availability. After COVID reduced demand, this constraint relaxed and the effect disappeared. This is consistent with a capacity-constrained model where frequency only matters at the margin when the system is near saturation, and is irrelevant otherwise.

The policy implication reinforces what emerged across Analyses 10, 26, and 29: **scheduled service frequency is not a lever for OTP improvement**. Routes don't get more on-time by running fewer trips, and they don't get less on-time by running more. The ~50% of OTP variance explained by the multivariate model (Analysis 18) comes from structural features (stop count, route length, mode), and the remaining ~50% likely reflects operational factors (schedule padding, driver availability, real-time traffic variability) that are orthogonal to how many trips are scheduled.

The 27-month window is a genuine limitation. A longer panel with more schedule variation -- particularly one that captures the post-2021 period when PRT may have restructured service -- could provide more statistical power. Extending the WPRDC data or obtaining historical GTFS archives would strengthen this null finding or reveal effects that 27 months cannot detect.

## Caveats

- The panel covers only 27 months, limiting statistical power for detecting small effects.
- Month-over-month trip changes are often zero (same pick period), reducing the effective variation in the independent variable.
- OTP is measured monthly while schedule changes can occur mid-month, introducing measurement noise.
- System-wide detrending removes the COVID shock but may also remove genuine correlated service changes (e.g., if all routes cut service and all improved OTP simultaneously).
