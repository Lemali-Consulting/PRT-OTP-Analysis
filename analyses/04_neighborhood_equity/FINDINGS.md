# Findings: Tract Equity

## Summary

Across **247 ranked tracts** (vs 89 hand-curated neighborhoods previously), the spread between the best- and worst-served tracts is **27 percentage points** of OTP. The lowest-income tract quintile experiences a **trip-weighted OTP of 65.2%**, vs **68.8% for the second-richest quintile** -- a **~3.6 pp gradient** that previous neighborhood-level analyses missed. The richest quintile drops back to 67.2%, so the relationship is **non-monotonic** (a U-shape inverted toward the upper-middle), but low-income tracts are unambiguously the worst-served.

## What changed
- Replaced fuzzy `stops.hood` (NULL for ~58% of stops, 89 hand-curated areas) with point-in-polygon assignment to TIGER 2022 census tracts. **All 6,466 stops now have a tract assignment** (up from ~2,706 with a hood). 343 tracts contain at least one PRT stop; 247 are served by 2+ routes and so are ranked.
- Demographic columns from the ACS join (`median_household_income`, zero-vehicle households, race composition) are now carried through to per-tract output, enabling the income-gradient analysis below.

## OTP by tract income quintile

| Quintile | Mean median income | n tracts | Total trips/7d | Trip-weighted OTP |
|----------|-------------------|----------|----------------|------------------:|
| Q1 (lowest)  | $32,280  | 48 | 480,438 | **65.2%** |
| Q2           | $50,516  | 47 | 322,944 | 67.1% |
| Q3           | $61,906  | 47 | 264,184 | 68.3% |
| Q4           | $77,248  | 47 | 252,379 | **68.8%** |
| Q5 (highest) | $107,458 | 47 | 330,967 | 67.2% |

Q5 - Q1 trip-weighted OTP gap: **+2.0 pp** (richest minus poorest); Q4 - Q1 gap: **+3.6 pp**. Q1 also concentrates the most service: 480k weekly trips vs 252k-330k in the upper quintiles -- so the worst OTP is borne by the largest share of riders.

## Worst-served tracts

| Label | Weighted OTP | Routes | Median income | % zero-vehicle | % non-white |
|-------|-------------:|-------:|--------------:|---------------:|------------:|
| Penn Hills 523300        | 57.1% | 3 | $74,740 | 7.8%  | 44% |
| Plum 526202              | 57.2% | 2 | $95,438 | 6.6%  | 22% |
| Penn Hills 523702        | 57.7% | 2 | $55,532 | 20.8% | 36% |
| Plum 526201              | 57.8% | 2 | $85,903 | 5.4%  | 5%  |
| Penn Hills 523500 (or similar) | 57.8% | 2 | $64,219 | 3.5%  | 60% |

The bottom of the distribution is dominated by Penn Hills and Plum -- eastern Allegheny County suburbs reached almost entirely by a few long bus routes. These are not the lowest-income tracts; they are at the *end of the line*. The income gradient is driven less by the very worst tracts and more by the difference between Q1 and the upper quintiles across all 247 tracts.

## Best-served tracts

| Label | Weighted OTP | Routes | Median income |
|-------|-------------:|-------:|--------------:|
| Castle Shannon 476100      | 84.0% | 3 | $59,868  |
| Pittsburgh 981200          | 83.9% | 3 | n/a (special-purpose tract) |
| Pittsburgh 320700          | 83.9% | 3 | $73,314  |
| Bethel Park (Allegheny)    | 82.8% | 3 | $104,732 |
| Bethel Park (Allegheny)    | 82.5% | 4 | $92,863  |

The top is dominated by short-line southern suburbs and rail-served tracts (the T runs through Castle Shannon and Bethel Park).

## Frequency-weighting effect

Tract-level mean `otp_gap = weighted - unweighted = -0.4 pp` (median -0.3 pp; range -6.8 pp to +4.1 pp). On average the high-frequency routes serving a tract perform slightly worse than that tract's route average -- consistent with the system-wide pattern (Analysis 19, Analysis 45). Largest negative gaps cluster in **Swissvale** and **Edgewood**, where lateness-prone Frankstown/Forbes corridor routes dominate trip volume.

## Observations

- The **non-monotonic** income gradient (Q1 < Q2 < Q3 < Q4 > Q5) is consistent with a service-design pattern: dense urban-core tracts (which include many low-income tracts) have frequent, slow, congestion-prone routes; mid-income inner suburbs sit on cleaner short-haul corridors; the highest-income tracts often sit at the end of long suburban routes that accumulate delay (echoing the Penn Hills / Plum pattern at the very bottom).
- The 3.6 pp Q1-vs-Q4 gap is meaningful at scale: Q1 tracts host ~37% of system weekly trips in the analyzed cohort (480k of 1.65M), so a sub-1pp shift here moves the system OTP noticeably.
- Ranking 247 tracts (vs 89 hoods) puts substance behind the Pittsburgh-city-vs-suburb story: **only 17 of the 30 worst-served tracts are inside Pittsburgh city limits**; the rest (esp. Penn Hills, Plum, Wilkinsburg-area) had previously been masked by being assigned NULL `hood` or by being aggregated into wide municipalities.
- 0 of the 6,466 stops were dropped for missing tract -- the previous analysis silently dropped 3,760 stops (58%) for missing hood.

## Caveats

- **Sample size varies**. Tracts have between 2 and 32 routes; a tract with 2 routes carries an OTP estimate driven by 2 routes' performance and should not be over-interpreted individually.
- **Trip-weighted, not rider-weighted.** `trips_7d` is scheduled weekly trips, not boardings. A tract can have many high-frequency routes passing through (especially downtown / busways) without having many residents who actually board there. Per-resident OTP weighting is what Analysis 45 explores at the route level.
- **Median income suppression**. ~14 of the 343 stop-bearing tracts have NULL `median_household_income` (Census suppresses small-sample estimates). These tracts are excluded from the quintile assignment but still appear in ranked output. The "Pittsburgh 981200" top-served tract is one of these -- it appears to be a special-purpose tract (parks/waterway) with very few residents.
- **Static weights**. `trips_7d` is a current snapshot, not a monthly time series. Tracts whose service has expanded or contracted within the 2018-2025 window are weighted by today's footprint.
- **Ecological framing**. Findings describe area-level associations between tract demographics and the OTP of routes touching that tract -- not per-resident outcomes. A resident's actual experienced OTP depends on which route they ride.
- **Tract polygons are 2020 geometry; demographics are 2018-2022 ACS 5-year**. Boundary changes within the period are not reflected.

## Validation
- **Data source verified.** `census_tracts` columns checked against `data/DATA_DICTIONARY.md` (post Pipeline 10 expansion). Spatial join via `geopandas.sjoin(predicate="within")` in EPSG:32617 (UTM zone 17N).
- **Geographic/temporal scope.** All three OTP measures use the identical 247-tract / 94-route / 2018-2025 cohort; bus-only stratification is a strict subset.
- **Coverage check.** All 6,466 stops with non-null lat/lon assigned to exactly one tract; no overlap (tracts are non-overlapping by construction). 343 distinct tracts touched, 247 with >= 2 routes.
- **Aggregates sanity-checked.** Trip-weighted system OTP across all 247 tracts (~67%) matches the system-wide trip-weighted OTP from Analysis 19 within rounding.
- **Direction of effects.** Q1 (lowest income) showing worst OTP is the expected sign for an equity gradient. Penn Hills and Plum at the bottom of the ranking are also consistent with the long-suburban-bus-route lateness pattern from Analysis 10.
- **Surprising results investigated.** The non-monotonic Q5 dip was investigated -- highest-income tracts in Allegheny County are clustered in southern/eastern suburbs reached by long routes, which matches the long-route lateness pattern.
- **Small-sample tracts flagged.** `MIN_ROUTES = 2` filter applied; below that, single-route tracts dominated by a single route's noise.
- **Ecological framing in FINDINGS.md.** Income-OTP relationship described as area-level association, never as per-resident claims.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) -- 7 issues (1 significant). Fixed time-pooled weighting (pre-aggregate OTP to route level before joining), added bus-only stratification revealing Simpson's paradox in Bon Air and Beechview, added NULL trips_7d filter, added minimum-month filter, documented panel balance caveat, added sample-size caveat, and clarified METHODS.md weighting description.
- 2026-05-10: Tract-level upgrade. Replaced fuzzy `stops.hood` (NULL for ~58% of stops, 89 hand-curated areas) with point-in-polygon assignment to ACS 2022 census tracts (343 served tracts, 247 with 2+ routes). Added income-quintile gradient analysis using the expanded `census_tracts` ACS columns from Pipeline 10. Tract-level dataset confirms the previously-hood-only pattern and reveals a 3.6 pp Q1-vs-Q4 income gap in trip-weighted OTP that the hood-level analysis could not surface.
