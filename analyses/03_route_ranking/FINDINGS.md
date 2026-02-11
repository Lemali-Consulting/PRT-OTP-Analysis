# Findings: Route Ranking

## Summary

94 routes had sufficient data (12+ months) to rank. Rankings use **trailing 12-month average OTP** to reflect current performance, and **post-2022 slope** to capture recent trajectory without COVID distortion. Slopes now include 95% confidence intervals via `scipy.stats.linregress`; 51 of 94 slopes are statistically significant (CI excludes zero). 3 routes were flagged as high-volatility. Routes are ranked both overall and within their mode (BUS, RAIL, UNKNOWN).

## Regression to the Mean

**Caution:** Extreme-ranked routes -- both top/bottom performers and most-improving/declining -- are expected to **regress toward the mean** in subsequent periods. This is a statistical phenomenon, not an operational one: routes that happen to have unusually good or bad stretches will tend to look less extreme next time, even without any intervention. Rankings should be interpreted as snapshots, not predictions. A route appearing at the top or bottom of a list does not necessarily mean it will stay there. Formal empirical Bayes shrinkage could partially correct for this, but is beyond the scope of this analysis. Readers should weight these rankings accordingly, especially for routes with fewer observations or higher volatility.

## Top 5 Routes (by trailing 12-month OTP)

| Route | Mode | Mode Rank | Recent OTP | All-Time OTP | Stops |
|-------|------|-----------|-----------|-------------|-------|
| G2 - West Busway | BUS | 1/89 | 88.4% | 81.7% | 24 |
| 18 - Manchester | BUS | 2/89 | 87.5% | 88.4% | 43 |
| P1 - East Busway-All Stops | BUS | 3/89 | 83.9% | 84.5% | 24 |
| 39 - Brookline | BUS | 4/89 | 82.6% | 78.9% | 69 |
| 43 - Bailey | BUS | 5/89 | 81.8% | 79.5% | 65 |

All top 5 are BUS routes. The 3 RAIL routes rank 9th (SLVR, 78.8%), 12th (BLUE, 77.4%), and 30th (RED, 72.8%) overall.

## Bottom 5 Routes (by trailing 12-month OTP)

| Route | Mode | Mode Rank | Recent OTP | All-Time OTP | Stops |
|-------|------|-----------|-----------|-------------|-------|
| 71B - Highland Park | BUS | 89/89 | 41.9% | 58.8% | 107 |
| 61C - McKeesport-Homestead | BUS | 88/89 | 44.8% | 56.8% | 158 |
| 65 - Squirrel Hill | BUS | 87/89 | 46.5% | 61.5% | 70 |
| 58 - Greenfield | BUS | 86/89 | 49.8% | 60.8% | 102 |
| 61B - Braddock-Swissvale | BUS | 85/89 | 50.1% | 58.4% | 137 |

## Post-COVID Trends (2022 onward)

Slopes are computed via OLS with standard errors. Only statistically significant slopes (95% CI excludes zero) are listed below. 43 of 94 routes have slopes that are **not** statistically significant -- their trend cannot be distinguished from flat.

**Most improving** (statistically significant):
| Route | Slope (pp/yr) | 95% CI | Months |
|-------|--------------|--------|--------|
| P78 - Oakmont Flyer | +6.6 | [+5.0, +8.2] | 47 |
| 71D - Hamilton | +4.1 | [+2.5, +5.7] | 47 |
| O1 - Ross Flyer | +3.4 | [+2.1, +4.6] | 47 |
| 39 - Brookline | +3.2 | [+0.9, +5.5] | 45 |
| G31 - Bridgeville Flyer | +2.6 | [+1.6, +3.6] | 47 |

**Most declining** (statistically significant):
| Route | Slope (pp/yr) | 95% CI | Months |
|-------|--------------|--------|--------|
| 65 - Squirrel Hill | -8.3 | [-11.7, -4.9] | 46 |
| 71B - Highland Park | -7.2 | [-8.8, -5.5] | 47 |
| P12 - Holiday Park Flyer | -5.8 | [-7.4, -4.2] | 47 |
| 81 - Oak Hill | -5.8 | [-7.3, -4.3] | 47 |
| 61C - McKeesport-Homestead | -5.4 | [-6.6, -4.2] | 47 |

**Notable non-significant slopes:** SWL (Outbound to SHJ) has a point estimate of -10.4 pp/yr but its 95% CI is [-34.7, +13.8] due to having only 13 observations over a 21-month span -- the apparent steep decline cannot be statistically distinguished from zero.

## Observation Span

Most routes with slopes have the full 47-month post-2022 span. Two routes have notably narrow observation windows:
- **SWL** (Outbound to SHJ): 13 observations over 21 months
- **P2** (East Busway Short): 21 observations over 21 months (significant slope, but over less than half the full window)

Routes with narrow spans may have slopes that are less representative of sustained trends.

## Observations

- Using trailing 12-month OTP shifts the rankings compared to all-time averages: G2 (West Busway) has improved markedly and now leads, while 71B (Highland Park) and 65 (Squirrel Hill) have deteriorated significantly.
- The post-COVID slope isolates recent trajectory without the structural break caused by the 2020 COVID ridership drop, which dominated full-period slopes.
- High-volatility routes (std > 2x median) include SWL, 15 (Charles), and 65 (Squirrel Hill), which have extreme month-to-month swings.
- 4 routes were excluded from ranking for having fewer than 12 months of data.
- 89 of the 94 ranked routes are BUS, 3 are RAIL, and 2 are UNKNOWN mode. Within-mode ranks are provided in the CSV to allow fair comparisons.

## Missing Stop Count Data

5 routes lack stop count data because they have no entries in the `route_stops` table: SWL (Outbound to SHJ), 37 (Castle Shannon), 42 (Potomac), P2 (East Busway Short), and RLSH (Red Line Shuttle). Stop counts for these routes are reported as null.

## Caveats

- Stop counts come from current data; historical stop counts may have differed.
- Post-COVID slope assumes a roughly linear trajectory from 2022 onward, which may not hold for all routes.
- **Regression to the mean** (see dedicated section above) means that top/bottom rankings and most-improving/declining lists overstate the persistence of extreme performance. These lists identify current outliers, not necessarily future ones.
- Routes with narrow observation spans (SWL, P2) have less reliable slope estimates even when statistically significant.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) — 7 issues (1 significant). Added RTM caveat, slope standard errors and 95% CIs, observation span tracking, within-mode rankings, zero-variance guard, updated METHODS.md for post-2022 period, and documented null stop counts.
