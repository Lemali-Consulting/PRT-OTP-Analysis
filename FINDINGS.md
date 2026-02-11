# Findings

Summary of results from 18 analyses of PRT on-time performance data (January 2019 -- November 2025, 98 routes, 7,651 monthly observations).

## 1. System-Wide Trend (Analysis 01)

PRT on-time performance has **declined over the seven-year window**. Trip-weighted system OTP started around 69% in early 2019, spiked briefly to 75% in March 2020 (COVID-era low ridership), then fell steadily to a trough of 58% in September 2022. It has since stabilized in the **61--63% range** through late 2025, but has not recovered to pre-COVID levels. A bus-only stratification confirms the decline is not an artifact of mixing modes -- the bus-only trend closely tracks the all-mode average (gap averages ~0.5 pp) because bus routes dominate the system (90+ of ~93 reporting).

The unweighted average (treating all routes equally) consistently runs 2--3 percentage points above the weighted average, meaning high-frequency routes -- the ones carrying the most riders -- tend to perform worse than low-frequency ones. Route count ranges from 68 to 96 across months; most months have 93--96, but Nov 2020 is a low outlier at 68. Five routes (37, 42, P2, RLSH, SWL) are excluded from the weighted average due to missing `route_stops` data.

## 2. Mode Comparison (Analysis 02)

Light rail (RAIL) consistently outperforms bus, averaging 84% OTP vs 69% for BUS system-wide (Mann-Whitney U = 6,563, p < 0.001, n = 83 months). Trip-weighted bus OTP (66.8%) is ~2 pp below the unweighted average (68.9%), confirming that higher-frequency bus routes tend to perform worse. The Incline has no OTP data (see Analysis 09). Five UNKNOWN-mode routes are excluded. Among bus subtypes:

| Bus Type | Avg OTP | Notes |
|----------|---------|-------|
| Busway (P1, P3, G2) | 71--76% | Dedicated right-of-way helps |
| Flyer (P/G/O prefix) | ~70% | Park-and-ride express services |
| Limited (L suffix) | ~72% | Fewer stops than local counterparts |
| Express (X suffix) | ~70% | Highway-dependent, variable |
| Local | 63--69% | Largest category, lowest performance |

Two paired-route comparisons were found (51/51L, 53/53L). On average, the limited variant outperforms its local counterpart by **+3.5 percentage points** (paired t-test: t = 7.37, p < 0.001, 95% CI: [+2.5, +4.4 pp], n = 85 paired monthly observations). The sample of only 2 route pairs limits generalizability.

The RAIL--BUS gap has been roughly stable over time, suggesting that the system-wide OTP decline affects both modes proportionally.

## 3. Route Ranking (Analysis 03)

94 routes had enough data (12+ months) to rank. Rankings use **trailing 12-month average OTP** to reflect current performance, and **post-2022 slope** (with 95% CIs via `scipy.stats.linregress`) to capture recent trajectory without COVID distortion. 51 of 94 slopes are statistically significant. 4 routes were excluded for insufficient data. Routes are ranked both overall and within their mode (BUS, RAIL, UNKNOWN).

**Caution -- Regression to the Mean:** Extreme-ranked routes (top/bottom performers, most-improving/declining) are expected to regress toward the mean in subsequent periods. These lists identify current outliers, not necessarily future ones.

**Best performers (by trailing 12-month OTP):**

| Route | Mode | Mode Rank | Recent OTP | All-Time OTP |
|-------|------|-----------|-----------|-------------|
| G2 - West Busway | BUS | 1/89 | 88.4% | 81.7% |
| 18 - Manchester | BUS | 2/89 | 87.5% | 88.4% |
| P1 - East Busway-All Stops | BUS | 3/89 | 83.9% | 84.5% |
| 39 - Brookline | BUS | 4/89 | 82.6% | 78.9% |

**Worst performers:**

| Route | Mode | Mode Rank | Recent OTP | All-Time OTP |
|-------|------|-----------|-----------|-------------|
| 71B - Highland Park | BUS | 89/89 | 41.9% | 58.8% |
| 61C - McKeesport-Homestead | BUS | 88/89 | 44.8% | 56.8% |
| 65 - Squirrel Hill | BUS | 87/89 | 46.5% | 61.5% |
| 58 - Greenfield | BUS | 86/89 | 49.8% | 60.8% |

**Most improving** (post-2022, statistically significant): P78 - Oakmont Flyer (+6.6 pp/yr, CI [+5.0, +8.2]), 71D - Hamilton (+4.1 pp/yr, CI [+2.5, +5.7]).
**Most declining** (post-2022, statistically significant): 65 - Squirrel Hill (-8.3 pp/yr, CI [-11.7, -4.9]), 71B - Highland Park (-7.2 pp/yr, CI [-8.8, -5.5]). Note: SWL (Outbound to SHJ) has a point estimate of -10.4 pp/yr but its CI includes zero due to only 13 observations over 21 months.

3 routes were flagged as **high-volatility** (standard deviation more than 2x the median), indicating wild month-to-month swings rather than stable performance. 5 routes lack stop count data due to missing `route_stops` entries.

## 4. Neighborhood Equity (Analysis 04)

89 Pittsburgh-area neighborhoods were analyzed (3,760 of 6,466 stops excluded due to missing neighborhood data). OTP is now computed from **route-level averages** (each route weighted once regardless of how many months of data it has), weighted by trip frequency, with a minimum 12-month data requirement. There is a **25 percentage-point spread** between the best- and worst-served neighborhoods (all modes pooled), narrowing to **20 pp** for bus-only:

**Worst-served neighborhoods:**
- Regent Square: 58.8%
- Bluff: 59.2%
- Crawford-Roberts: 61.4%
- Squirrel Hill North: 61.6%

**Best-served neighborhoods:**
- Overbrook: 83.9% (bus-only: 78.9%)
- Beechview: 80.7% (bus-only: 75.5%)
- Brookline: 79.2% (bus-only: 78.7%)
- Sheraden: 79.0% (bus-only: 79.0%)

**Bus-only stratification** reveals Simpson's paradox: Bon Air drops from rank 13 (pooled) to rank 53 (bus-only) because its high pooled OTP is driven by rail, not bus service. Beechview similarly drops 9 positions. The bottom neighborhoods are all-bus and unaffected.

The best-performing neighborhoods tend to be served by rail or busway routes (Overbrook and Beechview are on the light rail T line). The worst-performing neighborhoods are served primarily by high-frequency local bus routes with many stops. Neighborhood OTP estimates vary in precision (1 to 74 routes per neighborhood), so the 25 pp spread should be interpreted with that context. The equity gap between the top and bottom quintiles has remained roughly stable over time -- all quintiles rise and fall together with the system, meaning the disparity is structural rather than worsening.

## 5. Anomaly Investigation (Analysis 05)

842 anomalous months were flagged across 94 routes using a two-sided rolling z-score method with a **lagged window** (current month excluded from baseline, preventing self-dampening of z-scores). Both drops and spikes are detected. The routes with the most anomalies:

| Route | Anomalies | Notes |
|-------|-----------|-------|
| 79 - East Hills | 18 | Persistent instability |
| 19L - Emsworth Limited | 16 | Limited-stop route |
| RED - Castle Shannon via Beechview | 15 | Rail line with high variability |
| 54 - North Side-Oakland-South Side | 15 | Long cross-city route |
| 28X - Airport Flyer | 14 | Express route |

Anomaly rates vary by mode: BUS 11.8%, RAIL 14.3%, UNKNOWN 15.5%. RAIL's higher rate reflects its normally-consistent performance -- even moderate dips trigger the 2-sigma threshold. With 7,076 evaluated observations, the expected false-positive rate under normality is ~322 (~4.6%); the actual 842 anomalies (2.6x expected) indicates most are genuine, though ~300-350 could be chance alone. The lagged window also introduces trend bias: declining routes are more likely to trigger negative anomalies because the baseline is always slightly stale. 4 routes with fewer than 7 months of data are excluded from detection.

The COVID period (March--June 2020) generated positive anomalies across many routes as reduced ridership temporarily improved schedule adherence. The late 2022 cluster of negative anomalies across many routes may indicate a system-wide disruption (staffing, construction, or service restructuring).

## 6. Seasonal Patterns (Analysis 06)

PRT shows a consistent seasonal cycle after detrending (removing 12-month rolling mean), using a balanced panel of 93 routes present in all 12 months-of-year over complete calendar years (2019--2024):
- **Best months:** January (70.8% weighted OTP, +2.8 pp from trend) and March
- **Worst months:** September (64.4%, -3.9 pp) and October

This is somewhat counterintuitive -- winter months outperform summer/fall despite weather. Possible explanations: lower ridership in winter reduces dwell time and crowding delays; summer construction seasons create detours; school-year schedules in fall increase congestion.

93 routes had sufficient data (3+ years) for route-level seasonal analysis. Most have a seasonal amplitude under 15%. The most seasonally affected routes are 15 (Charles, 15.8%), O5 (Thompson Run Flyer, 15.2%), and P2 (East Busway Short, 14.8%). Red-team review confirmed the pattern holds after correcting for route composition bias (winter-only routes with high OTP) and unbalanced year coverage.

## 7. Stop Count vs OTP (Analysis 07)

There is a **moderately strong negative correlation** between the number of stops on a route and its average OTP (routes with fewer than 12 months of data excluded):

- **All routes: r = -0.53** (p < 0.001, n = 92)
- **Bus only: r = -0.50** (p < 0.001, n = 89)
- **Bus only Spearman: r = -0.49** (p < 0.001)

The bus-only result rules out Simpson's paradox -- the effect is not an artifact of mixing BUS and RAIL modes. Routes with fewer than 50 stops consistently achieve 80%+ OTP, while routes with 150+ stops struggle to reach 60%. This is the clearest structural predictor of OTP in the dataset. Note: stop counts come from the current route_stops snapshot while OTP is averaged across all historical months, so routes that changed stop configurations have a temporal mismatch.

## 8. Hot-Spot Map (Analysis 08)

6,212 stops were mapped with route-weighted OTP values (a derived metric: each stop inherits the average OTP of routes serving it, weighted by trip frequency -- not independently measured stop performance). Routes with fewer than 12 months of data are excluded. Geographic patterns:
- **Best performance** clusters along the light rail T line (Beechview/Overbrook corridor) and the East Busway (Wilkinsburg to downtown). Rail stops appear green primarily due to RAIL's ~84% system-wide OTP (mode advantage), not stop-specific factors.
- **Worst performance** clusters in the eastern neighborhoods (Penn Hills, Squirrel Hill, Highland Park) where Route 77 and other long local routes operate
- Downtown stops show middling performance -- they are served by many routes, and the average reflects the mix

The worst-performing stops (55.8% OTP) are exclusively served by Route 77 (Penn Hills). The best-performing stops (88.4%) are served exclusively by Route 18 (Manchester) -- a genuinely high-performing bus route, not rail. The system average in the chart is an unweighted stop-level average.

## 9. Monongahela Incline Investigation (Analysis 09)

The Monongahela Incline (route MI) is a **data pipeline artifact**. It exists in the routes table with mode=INCLINE and has 2 associated stops (Upper and Lower stations, 78 weekday trips), but has **zero entries in the OTP table**. OTP was never measured or reported for this route. The same is true for the Duquesne Incline (route DQI). Both inclines are physically operational and appear in the GTFS feed, but were excluded from whatever OTP measurement system generated this dataset.

## 10. Trip Frequency vs OTP (Analysis 10)

There is **no meaningful correlation** between peak weekday trip frequency and OTP:

- **All routes: r = 0.03** (p = 0.81, n = 92)
- **Bus only: r = -0.06** (p = 0.55, n = 89)
- **Bus only Spearman: r = -0.11** (p = 0.29)

The previous finding (r = -0.39) was an artifact of using `SUM(trips_wd)` across all stops, which conflated trip frequency with route length (stop count). After correcting to `MAX(trips_wd)` (peak frequency at any single stop), the correlation vanishes entirely. Running more trips per se does not degrade OTP -- the real driver is route complexity (stop count), not service volume. Routes with fewer than 12 months of OTP data are excluded. Three correlation tests were run without multiple-comparison correction; all are non-significant.

## 11. Directional Asymmetry (Analysis 11)

The correlation between directional trip imbalance and OTP is **weak and not statistically significant** (r = -0.12, p = 0.26, n = 90). After correcting the methodology to include bidirectional (IB,OB) stops in both directions and exclude one-direction-only routes, PRT routes show very little asymmetry -- the most asymmetric route (19L) has only a 7.7% imbalance (7 vs 6 trips). The previous finding of routes with 100% asymmetry (Routes 11 and 60) was a data artifact. Including IB,OB stops in both directions can compress asymmetry toward zero when such a stop has the highest trip count, which is a known limitation. Routes with fewer than 12 months of OTP data are excluded. Three correlation tests were run without multiple-comparison correction; all are non-significant. This hypothesis did not yield actionable findings.

## 12. Route Geographic Span vs OTP (Analysis 12)

Geographic span (max distance between any two stops) is a **moderate negative predictor** of OTP within bus routes (r = -0.38, p < 0.001), stronger than the pooled all-mode result (r = -0.32) which was muted by Simpson's paradox. **Stop count is the stronger factor**:

- Stop count vs OTP controlling for span (bus): **partial r = -0.41** (p < 0.001)
- Span vs OTP controlling for stop count (bus): **partial r = -0.23** (p = 0.03)
- Span and stop count are moderately correlated (r = 0.41) but not collinear

Stop density (stops per km) shows no correlation with OTP (r = 0.04). Both route length and stop count independently degrade OTP, but stop consolidation is the higher-leverage intervention -- roughly twice the impact of shortening routes.

## 13. Cross-Route Correlation Clustering (Analysis 13)

After **detrending** (subtracting system-wide monthly mean), hierarchical clustering on pairwise OTP correlations produced **6 clusters** (silhouette-optimized, k=6, score=0.178). Detrending removes the dominant COVID/seasonal signal. The resulting clusters show moderate separation: the best cluster (9 routes, 74.0% OTP) and worst (23 routes, 66.8% OTP) differ by 7.2 pp. Low silhouette scores indicate the cluster structure is suggestive rather than definitive. Without depot or corridor data, we cannot confirm what drives co-movement.

## 14. COVID Recovery Trajectories (Analysis 14)

Of 92 routes, 43 improved and 49 declined vs pre-COVID baseline (2019-01 to 2020-02 vs 2024-12 to 2025-11). However, a **significant regression-to-the-mean effect** (r = -0.25, p = 0.02) means much of the divergence is statistical rather than operational. The **Kruskal-Wallis test across subtypes is not significant** (p = 0.24), meaning there is no defensible evidence that premium routes recovered better *as a group*.

The most-improved routes (P7 +17 pp, G2 +13 pp) tend to be premium types, while the most-declined (71B -21 pp, 58 -21 pp, 65 -19 pp) are eastern-neighborhood local bus routes. But the extreme cases are partially explained by regression to the mean. The policy-relevant finding is narrower: specific local bus routes in the eastern corridor have deteriorated badly beyond what RTM alone predicts.

## 15. Municipal/County Equity (Analysis 15)

81 municipalities analyzed (better coverage than the 89 neighborhoods in Analysis 04). The spread is **24.9 pp**: Castle Shannon borough (84.0%, on T line) to Plum borough (59.1%, long local bus). Suburban median OTP (68.1%) is near the system average -- no systematic suburban disadvantage. Cross-jurisdictional routes perform identically to single-municipality routes (Welch's t-test p = 0.86), confirming that mode and stop count matter more than geography.

## 16. Transfer Hub Performance (Analysis 16)

Stop-level data suggests hubs have modestly worse OTP (simple 69.5% vs hub 66.4%), but the stop-level correlation (r = -0.17) uses **non-independent observations** (n=6,209 stops sharing ~90 underlying route OTP values). At the **route level** (independent, n=93), the correlation is **not significant** (r = -0.15, p = 0.16). Bus-only: r = -0.09, p = 0.39. The apparent "hub penalty" is a **composition effect**: hubs are served by many routes including poor performers, not because hub locations cause worse OTP. The busiest hub (East Busway Penn Station, 27 routes) outperforms the system average (72.1%).

## 17. Weekend vs Weekday Service Profile (Analysis 17)

There is **no correlation** between weekend-to-weekday service ratio and OTP (r = -0.03, p = 0.79). Weekday-heavy routes (69.8%), balanced routes (68.8%), and weekend-heavy routes (70.3%) perform virtually identically. Service profile is not a useful predictor of reliability.

## 18. Multivariate OTP Model (Analysis 18)

A six-feature OLS model explains **47.2% of OTP variance** (adj R² = 0.435, n = 92). Three features are significant:

| Feature | Beta Weight | p-value |
|---------|-------------|---------|
| Stop count | -0.49 | <0.001 |
| Geographic span (km) | -0.47 | <0.001 |
| Rail mode | +0.34 | <0.001 |
| N municipalities (suppressor) | +0.41 | 0.001 |
| Premium bus subtype | +0.05 | 0.70 |
| Weekend ratio | -0.03 | 0.79 |

VIF values for all predictors are below 3, indicating moderate but manageable multicollinearity. The n_munis variable acts as a **suppressor** -- its positive coefficient does not mean crossing more jurisdictions helps OTP, but rather that it partials out shared variance with stop count and span. A reduced model without n_munis yields R² = 0.40; a bus-only model (no rail dummy needed) yields R² = 0.38, confirming the findings generalize within the dominant mode.

Premium bus advantage disappears after controlling for stop count and span -- those routes simply have fewer stops. The unexplained 53% likely reflects traffic, schedule design, staffing, and weather.

## Key Takeaways

1. **PRT OTP has declined** from ~69% to ~62% since 2019 and has not recovered post-COVID.
2. **Dedicated right-of-way matters most**: rail (84%) and busway (74%) routes dramatically outperform local bus (66%) routes.
3. **Stop count is the strongest predictor** of poor OTP (r = -0.53 all routes n=92, r = -0.50 bus-only n=89). Routes with 150+ stops consistently underperform. This finding survives bus-only stratification, ruling out Simpson's paradox.
4. **Route length independently degrades OTP** (partial r = -0.23 after controlling for stop count), but stop count has roughly twice the impact (partial r = -0.41).
5. **A multivariate model explains 47% of variance** using stop count, span, mode, and a suppressor (n_munis). A reduced model with just stop count, span, and mode explains 40%. The remaining variance requires operational data not in this dataset.
6. **The COVID decline is uneven but partially driven by regression to the mean** (r = -0.25, p = 0.02). Routes with extreme pre-COVID baselines naturally regressed toward the mean. There is no statistically significant difference in recovery across route subtypes (Kruskal-Wallis p = 0.24). The policy-relevant finding is narrower: specific local bus routes in the eastern corridor (71B, 58, 65) have deteriorated 15--21 pp beyond what RTM alone predicts.
7. **Geographic inequity is structural**: municipalities on rail/busway get 80%+ OTP; those dependent on long local bus get 59--62%. The gap is driven by mode and route structure, not by geography per se.
8. **Transfer hubs do not independently predict worse OTP.** The raw stop-level gap (-3.5 pp) is a composition effect from poor-performing routes converging at hubs. At the route level, the correlation between hub connectivity and OTP is not significant (r = -0.15, p = 0.16).
9. **Trip frequency, weekend service ratio, and directional asymmetry** do not predict OTP -- null results that narrow the field of actionable levers.
10. **Anomalies and seasonality** are real but modest: September is the worst month, COVID and late 2022 produced system-wide shocks.
