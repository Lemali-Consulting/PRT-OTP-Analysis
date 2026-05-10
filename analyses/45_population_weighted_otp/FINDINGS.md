# Findings: Population-Weighted System OTP

## Summary
The OTP experienced by the average resident-near-a-route is **68.1%** -- about **0.85 percentage points higher than the trip-weighted system OTP (67.3%)** but **1.27 pp lower than the unweighted average (69.4%)**. The population-weighted vs trip-weighted gap is statistically significant (paired t = -15.8, p < 0.001; Wilcoxon W = 20, p < 0.001; n = 83 months). PRT's lateness-prone routes concentrate where many people live, but slightly less than scheduled trip frequency alone would imply.

## Key Numbers
- **Unweighted OTP** (all 92 routes equal): 69.4% mean, 69.7% median
- **Trip-weighted OTP** (`route_stops.trips_7d`): 67.3% mean, 67.4% median
- **Population-weighted OTP** (walkshed residents from Analysis 44): 68.1% mean, 68.4% median
- **Population vs trip-weighted gap**: +0.85 pp (p < 0.001, n = 83 months)
- **Cohort**: 92 routes with >= 12 months of OTP data, Mar 2018 -- Nov 2025
- **Total population_served sum**: 2,273,565 (exceeds the 2,171,546 5-county total because residents within walking distance of multiple routes are counted once per route -- see Caveats)

## Interpretation
Both weighted schemes pull system OTP *down* from the unweighted average, meaning that routes carrying more scheduled trips and routes serving more residents both tend to perform somewhat worse than average. The two effects largely overlap -- high-frequency urban-core routes serve dense population centers -- but they are not identical: population weighting penalizes the system roughly half as much as trip weighting does.

The gap is consistent with what Analysis 19 found for ridership weighting (+1.6 pp above trip-weighted): scheduled trip frequency overstates how concentrated rider exposure actually is on the worst-performing routes. Both ridership and walkshed population are distributed somewhat more evenly across the OTP spectrum than scheduled trips are.

This is an area-level association (which routes serve dense areas, weighted by their OTP), not a per-resident estimate.

## Observations
- The three series move together over time -- all show the COVID OTP spike in 2020 and the steady decline through late 2022, then partial stabilization through 2024-2025.
- The population vs trip-weighted gap is small but extremely stable across the 83-month window, which is why the paired t-test reaches such a large statistic despite a sub-1pp difference.
- The unweighted-vs-trip-weighted gap (~2.1 pp) is wider than the population-vs-trip gap (~0.85 pp), confirming that route trip frequency is more concentrated on lateness-prone routes than walkshed population is.

## Caveats
- **Exposure double-counting.** Residents within walksheds of multiple routes are counted once per route. Population-weighted OTP is the OTP of the average *route-resident exposure*, not the average *resident*. A resident with access to many routes contributes more weight than one served by a single route. Per-resident OTP would require modeling which route each resident actually rides, which we cannot do without trip-level rider data.
- **Static walkshed weights.** `population_served` is computed from current stops and 2018-2022 ACS population; the same per-route weight is applied to every month. Route footprints and demographics that shifted within the window are not reflected.
- **Static trip weights.** `route_stops.trips_7d` is also a current snapshot, not a monthly time series, matching Analysis 19's treatment for comparability.
- **Cohort.** Restricted to 92 routes with >= 12 months of OTP. Routes that exist in the schedule but lack consistent OTP data (e.g., short-lived service) are excluded from all three series.

## Validation
- **Data source verified.** `otp_monthly`, `route_stops`, `stops`, `routes`, and `census_tracts` columns checked against `data/DATA_DICTIONARY.md`. All three table joins use validated `query_to_polars` results.
- **Geographic/temporal scope.** All three weighting schemes use the identical 92-route cohort and identical 83-month window; the only difference is the weight column.
- **Aggregates sanity-checked.** Unweighted system OTP 69.4% mean matches Analysis 01 (system trend) within rounding. Trip-weighted 67.3% matches Analysis 19's trip-weighted 67.8% to within ~0.5 pp -- the small difference is because Analysis 19 restricts to the ridership-overlap window (Jan 2019 - Oct 2024) while this analysis uses the full OTP window.
- **Direction of effects checked.** Trip-weighted < unweighted is the expected sign (high-frequency routes are more lateness-prone, per Analysis 10 frequency-vs-OTP). Population-weighted falling between the two is the expected pattern given that walkshed population correlates with but is less concentrated than trip frequency.
- **Population sum cross-check.** The 2,273,565 cohort population sum exceeding the 2,171,546 5-county total directly confirms multi-route exposure overlap; the ratio (~5% over) is small because most multi-route overlap is concentrated in downtown Pittsburgh, which is a small slice of the 5-county population.
- **Ecological framing.** Findings describe area-level associations (route-level OTP weighted by route-level walkshed population), never per-resident outcomes. Caveat documented above.
