# Executive Summary: PRT On-Time Performance Analysis

**30 analyses | 98 routes | 7,651 monthly observations | January 2019 -- November 2025**

---

## The Bottom Line

Pittsburgh Regional Transit's on-time performance has declined from **69% to 63%** since 2019 and has not recovered to pre-COVID levels. The decline is real, system-wide, and structural -- it is not an artifact of how performance is measured, which routes are included, or how the data is weighted. Half of the variation in route-level OTP can be explained by route geometry (stop count, route length, and whether the route has dedicated right-of-way). The other half is likely driven by operational factors -- schedule design, staffing, and peak-hour traffic -- that are not observable in the available data.

---

## What Drives OTP

### Confirmed predictors (~50% of variance explained)

| Factor | Effect | Evidence |
|--------|--------|----------|
| **Stop count** | Each additional stop degrades OTP; routes with 150+ stops rarely exceed 60% | Strongest single predictor (r = -0.53). Survives bus-only stratification. |
| **Dedicated right-of-way** | Rail: 84% OTP. Busway: 74%. Local bus: 66%. | 18--25 pp advantage over mixed-traffic routes. |
| **Route length** | Longer corridors accumulate more delay | Independent of stop count (partial r = -0.23), but roughly half the impact. |
| **Road type** | Routes on wider arterials perform better | Truck share proxies for road classification (beta = +0.26, p = 0.006). |
| **Garage assignment** | Collier routes outperform East Liberty by +5.4 pp after structural controls | Suggests corridor-level or operational differences between garages. |
| **Seasonality** | January is best (+2.8 pp); September is worst (-3.9 pp) | Counterintuitively, cold months are better -- likely due to lower demand, not weather. |

### Confirmed non-predictors (ruled out)

| Factor | Result | Analyses |
|--------|--------|----------|
| Trip frequency | No effect -- running more or fewer trips doesn't change OTP | 10, 30 |
| Schedule changes | +0.6 pp mean shift, no difference by type (increase vs cut vs neutral) | 29 |
| Ridership volume | Not significant after controlling for route structure | 26 |
| Total traffic volume (AADT) | Null -- 24-hour averages don't capture peak-hour congestion | 27 |
| Transfer hub status | Apparent penalty is a composition effect, not causal | 16 |
| Weather | Interchangeable with seasonal dummies; no route-level discriminating power | 28 |
| Weekend service ratio | Null | 17 |

### Likely causes of remaining ~50% (unmeasured)

1. **Schedule padding** -- If scheduled running times are too tight for actual conditions, routes will consistently run late. This is the most likely single factor and would explain the garage effect.
2. **Driver staffing** -- Post-COVID shortages are well-documented and would explain the post-2022 plateau.
3. **Peak-hour congestion** -- AADT (24-hour average) was null, but rush-hour speeds on bus corridors would be a stronger test.
4. **Vehicle reliability** -- Fleet age and mechanical breakdowns cause cascading delays.
5. **Signal timing and transit signal priority** -- Corridors with TSP should outperform those without.

---

## The COVID Story

COVID produced the largest service disruption in the dataset. Key findings:

- **OTP spiked to 77%** in March 2020 as ridership collapsed and buses ran on empty roads.
- **Weekday ridership fell 43%** and has not recovered. Saturday is at 91% of pre-COVID levels; weekday at just 65%.
- **OTP declined to 60%** by September 2022, then stabilized in the 63--65% range.
- **No route subtype recovered significantly better** than others (Kruskal-Wallis p = 0.24). Regression to the mean explains much of the apparent divergence (r = -0.25, p = 0.02).
- Specific eastern-corridor local bus routes (71B, 58, 65) have deteriorated 15--21 pp beyond what regression to the mean predicts -- these are genuine problem routes.
- The system's total **delay burden decreased** post-COVID -- not because OTP improved, but because there are fewer riders to be delayed.

---

## Equity

Geographic inequity in OTP is **structural, not worsening**. All neighborhoods rise and fall together with the system trend.

- **Best-served areas** are on rail or busway corridors: Castle Shannon (84%), Overbrook (84%), Beechview (81%).
- **Worst-served areas** depend on long local bus routes: Plum (59%), Regent Square (59%), Bluff (59%).
- The gap is **25 pp** (all modes) or **20 pp** (bus only). It is driven by mode and route geometry, not by geography per se.
- **33% of bus ridership** is carried by the lowest-OTP quintile (18 routes averaging 61% OTP) -- targeting these routes would yield the highest human impact per intervention.
- OTP rank is a **poor proxy for human impact**: Route 51 ranks 55th by OTP but 2nd by delay burden due to high ridership. Route 77 has the worst OTP but ranks only 18th by burden.

---

## What Would (and Wouldn't) Help

### High-leverage interventions (supported by evidence)

- **Stop consolidation on the worst-performing routes.** Stop count is the strongest predictor of poor OTP. Routes like 61C (McKeesport, 45% recent OTP) and 71B (Highland Park, 42%) have 150+ stops and are structurally unable to maintain schedules. Eliminating low-ridership stops would reduce dwell time and signal exposure.
- **Dedicated lanes or signal priority on high-burden corridors.** The 18--25 pp advantage of dedicated right-of-way is the single largest effect in the dataset. Even partial bus lanes on the worst corridors (Forbes/Fifth for routes 61/71, East Busway extensions) would help.
- **Investigate Collier garage practices.** Collier routes outperform by +5.4 pp after controlling for route structure. If this reflects better schedule padding or operational practices, it could be replicated at other garages.
- **Prioritize the 18 Q1 bus routes.** These carry a third of bus ridership at 61% OTP. Any system-wide improvement effort should start here.

### Low-leverage interventions (not supported by evidence)

- **Adding or cutting trips.** Trip frequency has no relationship with OTP in cross-sectional, longitudinal, or event-study designs. Running more buses on a poorly-performing route will produce more late buses, not better OTP.
- **Rerouting to lower-traffic roads.** Total traffic volume (AADT) shows no effect on OTP. The issue is route structure, not road congestion -- at least as measured by annual averages.
- **Schedule restructuring alone.** Pick period transitions show a tiny +0.6 pp effect with no difference by type. Restructuring without addressing underlying stop count or running time issues is unlikely to move the needle.

---

## Data Limitations

This analysis is based on **route-month level OTP** (proportion of trips on-time per route per month). Several limitations constrain what can be concluded:

- **No stop-level OTP.** A route's OTP is uniform across all its stops in this data. We cannot identify which segments or stops cause delays.
- **No definition of "on-time."** The threshold (1 minute? 5 minutes?) is not specified in the source data.
- **Time-varying weights cover only 27 months.** WPRDC scheduled trip counts (Jan 2019 -- Mar 2021) provide month-specific service levels; later months use a static snapshot.
- **No operational data.** Scheduled vs actual running times, driver staffing levels, vehicle assignments, and real-time traffic speeds are not available. These likely explain the remaining ~50% of OTP variance.
- **Monthly aggregation is coarse.** Effects that operate at the trip, hour, or day level (weather events, incidents, peak-hour congestion) are smoothed away.

---

## Methodology

This analysis draws on 10 database tables (OTP, routes, stops, ridership, scheduled trips, weather, traffic) and applies a range of statistical methods across 30 independent analyses: OLS regression, fixed-effects panel models, Granger causality, hierarchical clustering, spatial joins (KDTree), Kruskal-Wallis tests, partial correlations, and rolling z-score anomaly detection. Two significant methodology issues from earlier analyses were corrected: (1) a weight conflation bug that inflated long-route importance, and (2) static weights that retroactively applied current schedules to historical periods. Both were fixed using WPRDC time-varying scheduled trip counts. All analyses, data, and code are reproducible via `uv run python analyses/NN_name/main.py`.

---

*Analysis conducted February 2026. Full technical findings: [FINDINGS.md](FINDINGS.md). Methodology issues and corrections: [docs/METHODOLOGY-ISSUES.md](docs/METHODOLOGY-ISSUES.md).*



# Max Notes

Analysis 22: Prioritizing improvements OTP in routes with high ridership, even if they have higher-than-average OTP, would improve the experience for users, more than improving OTP for lower-ridership users. 

Analysis 23: Some garages, like Collier's, appear to have better OTP than others for reasons not captured in the existing data. 

Analysis 24: Drop in ridership is primarily due to remote and hybrid work.

25: Q1 (worst) bust routes have lowest OTP and highest ridership share -- targeting these would lead to the highest-impact intervention. 

## Data Needed
Need stop-level boarding data to get a stronger sense of whether certain stops are rarely used (and, if they are within 200m of another stop, could easily be consolidated with limited negative impact on ridership)

## Possible Interventions

Add limited-stop overlays instead of removing stops; this would improve OTP.

Invest in weekday reliability improvements -- weekend ridership is recovering normally. 

Target eastern corridor. 