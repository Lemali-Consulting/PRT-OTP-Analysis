# Findings

Summary of results from 11 analyses of PRT on-time performance data (January 2019 -- November 2025, 98 routes, 7,651 monthly observations).

## 1. System-Wide Trend (Analysis 01)

PRT on-time performance has **declined over the seven-year window**. Trip-weighted system OTP started around 69% in early 2019, spiked briefly to 75% in March 2020 (COVID-era low ridership), then fell steadily to a trough of 58% in September 2022. It has since stabilized in the **61--63% range** through late 2025, but has not recovered to pre-COVID levels.

The unweighted average (treating all routes equally) consistently runs 2--3 percentage points above the weighted average, meaning high-frequency routes -- the ones carrying the most riders -- tend to perform worse than low-frequency ones.

## 2. Mode Comparison (Analysis 02)

Light rail (RAIL) **significantly outperforms bus**, averaging 84% OTP vs 69% for BUS system-wide. The Incline has no OTP data (see Analysis 09). Among bus subtypes:

| Bus Type | Avg OTP | Notes |
|----------|---------|-------|
| Busway (P/G prefix) | 71--76% | Dedicated right-of-way helps |
| Limited (L suffix) | ~72% | Fewer stops than local counterparts |
| Express (X suffix) | ~70% | Highway-dependent, variable |
| Local | 63--69% | Largest category, lowest performance |

Two paired-route comparisons were found (local vs limited variants sharing a corridor). On average, the limited variant outperforms its local counterpart by **+3.5 percentage points**, confirming that fewer stops improves schedule adherence.

The RAIL--BUS gap has been roughly stable over time, suggesting that the system-wide OTP decline affects both modes proportionally.

## 3. Route Ranking (Analysis 03)

94 routes had enough data (12+ months) to rank. Rankings use **trailing 12-month average OTP** to reflect current performance, and **post-2022 slope** to capture recent trajectory without COVID distortion. 4 routes were excluded for insufficient data.

**Best performers (by trailing 12-month OTP):**

| Route | Mode | Recent OTP | All-Time OTP |
|-------|------|-----------|-------------|
| G2 - West Busway | BUS | 88.4% | 81.7% |
| 18 - Manchester | BUS | 87.5% | 88.4% |
| P1 - East Busway-All Stops | BUS | 83.9% | 84.5% |
| 39 - Brookline | BUS | 82.6% | 78.9% |

**Worst performers:**

| Route | Mode | Recent OTP | All-Time OTP |
|-------|------|-----------|-------------|
| 71B - Highland Park | BUS | 41.9% | 58.8% |
| 61C - McKeesport-Homestead | BUS | 44.8% | 56.8% |
| 65 - Squirrel Hill | BUS | 46.5% | 61.5% |
| 58 - Greenfield | BUS | 49.8% | 60.8% |

**Most improving** (post-2022): P78 - Oakmont Flyer (+6.6 pp/yr), 71D - Hamilton (+4.1 pp/yr).
**Most declining** (post-2022): SWL - Outbound to SHJ (-10.5 pp/yr), 65 - Squirrel Hill (-8.3 pp/yr).

3 routes were flagged as **high-volatility** (standard deviation more than 2x the median), indicating wild month-to-month swings rather than stable performance.

## 4. Neighborhood Equity (Analysis 04)

89 Pittsburgh-area neighborhoods were analyzed (3,760 of 6,466 stops excluded due to missing neighborhood data). There is a **25 percentage-point spread** between the best- and worst-served neighborhoods:

**Worst-served neighborhoods:**
- Regent Square: 58.7%
- Bluff: 59.2%
- Crawford-Roberts: 61.4%
- Squirrel Hill North: 61.6%

**Best-served neighborhoods:**
- Overbrook: 83.9%
- Beechview: 80.7%
- Brookline: 79.2%
- Sheraden: 79.0%

The best-performing neighborhoods tend to be served by rail or busway routes (Overbrook and Beechview are on the light rail T line). The worst-performing neighborhoods are served primarily by high-frequency local bus routes with many stops. The equity gap between the top and bottom quintiles has remained roughly stable over time -- all quintiles rise and fall together with the system, meaning the disparity is structural rather than worsening.

## 5. Anomaly Investigation (Analysis 05)

842 anomalous months were flagged across 94 routes using a rolling z-score method with a **lagged window** (current month excluded from baseline, preventing self-dampening of z-scores). The routes with the most anomalies:

| Route | Anomalies | Notes |
|-------|-----------|-------|
| 79 - East Hills | 18 | Persistent instability |
| 19L - Emsworth Limited | 16 | Limited-stop route |
| RED - Castle Shannon via Beechview | 15 | Rail line with high variability |
| 54 - North Side-Oakland-South Side | 15 | Long cross-city route |
| 28X - Airport Flyer | 14 | Express route |

The COVID period (March--June 2020) generated positive anomalies across many routes as reduced ridership temporarily improved schedule adherence. The late 2022 cluster of negative anomalies across many routes may indicate a system-wide disruption (staffing, construction, or service restructuring).

## 6. Seasonal Patterns (Analysis 06)

PRT shows a consistent seasonal cycle after detrending (removing 12-month rolling mean):
- **Best months:** January (70.3% weighted OTP) and March
- **Worst months:** September (64.0%) and October

This is somewhat counterintuitive -- winter months outperform summer/fall despite weather. Possible explanations: lower ridership in winter reduces dwell time and crowding delays; summer construction seasons create detours; school-year schedules in fall increase congestion.

93 routes had sufficient data (3+ years) for route-level seasonal analysis. Most have a seasonal amplitude under 15%. The most seasonally affected routes are O5 (Thompson Run Flyer, 15.4%), P2 (East Busway Short, 14.8%), and 58 (Greenfield, 13.9%).

## 7. Stop Count vs OTP (Analysis 07)

There is a **moderately strong negative correlation** between the number of stops on a route and its average OTP:

- **All routes: r = -0.53** (p < 0.001, n = 93)
- **Bus only: r = -0.50** (p < 0.001, n = 90)
- **Bus only Spearman: r = -0.48** (p < 0.001)

The bus-only result rules out Simpson's paradox -- the effect is not an artifact of mixing BUS and RAIL modes. Routes with fewer than 50 stops consistently achieve 80%+ OTP, while routes with 150+ stops struggle to reach 60%. This is the clearest structural predictor of OTP in the dataset.

## 8. Hot-Spot Map (Analysis 08)

6,216 stops were mapped with trip-weighted OTP values. Geographic patterns:
- **Best performance** clusters along the light rail T line (Beechview/Overbrook corridor) and the East Busway (Wilkinsburg to downtown)
- **Worst performance** clusters in the eastern neighborhoods (Penn Hills, Squirrel Hill, Highland Park) where Route 77 and other long local routes operate
- Downtown stops show middling performance -- they are served by many routes, and the average reflects the mix

The worst-performing stops (55.8% OTP) are exclusively served by Route 77 (Penn Hills), the lowest-ranked route in the system.

## 9. Monongahela Incline Investigation (Analysis 09)

The Monongahela Incline (route MI) is a **data pipeline artifact**. It exists in the routes table with mode=INCLINE and has 2 associated stops (Upper and Lower stations, 78 weekday trips), but has **zero entries in the OTP table**. OTP was never measured or reported for this route. The same is true for the Duquesne Incline (route DQI). Both inclines are physically operational and appear in the GTFS feed, but were excluded from whatever OTP measurement system generated this dataset.

## 10. Trip Frequency vs OTP (Analysis 10)

There is **no meaningful correlation** between peak weekday trip frequency and OTP:

- **All routes: r = 0.02** (p = 0.85, n = 93)
- **Bus only: r = -0.07** (p = 0.51, n = 90)
- **Bus only Spearman: r = -0.12** (p = 0.24)

The previous finding (r = -0.39) was an artifact of using `SUM(trips_wd)` across all stops, which conflated trip frequency with route length (stop count). After correcting to `MAX(trips_wd)` (peak frequency at any single stop), the correlation vanishes entirely. Running more trips per se does not degrade OTP -- the real driver is route complexity (stop count), not service volume.

## 11. Directional Asymmetry (Analysis 11)

The correlation between directional trip imbalance and OTP is **weak and not statistically significant** (r = -0.12, p = 0.26, n = 90). After correcting the methodology to include bidirectional (IB,OB) stops in both directions and exclude one-direction-only routes, PRT routes show very little asymmetry -- the most asymmetric route (19L) has only a 7.7% imbalance (7 vs 6 trips). The previous finding of routes with 100% asymmetry (Routes 11 and 60) was a data artifact. This hypothesis did not yield actionable findings.

## Key Takeaways

1. **PRT OTP has declined** from ~69% to ~62% since 2019 and has not recovered post-COVID.
2. **Dedicated right-of-way matters most**: rail (84%) and busway (74%) routes dramatically outperform local bus (66%) routes.
3. **Stop count is the strongest predictor** of poor OTP (r = -0.53 all routes, r = -0.50 bus-only). Routes with 150+ stops consistently underperform. This finding survives bus-only stratification, ruling out Simpson's paradox.
4. **Trip frequency does not predict OTP** once properly measured. The previous apparent correlation was an artifact of confounding frequency with route length.
5. **Geographic inequity is structural**: neighborhoods served by rail/busway enjoy 80%+ OTP, while those dependent on long local bus routes get 59--62%. The gap is stable, not worsening.
6. **Seasonality is real but modest**: September is the worst month, January the best, with a ~6pp system-wide swing after detrending.
7. **Anomalies cluster in time**: COVID (2020) and late 2022 produced system-wide anomaly bursts, suggesting external shocks rather than route-specific problems.
