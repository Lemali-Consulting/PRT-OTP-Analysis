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

94 routes had enough data (12+ months) to rank. 4 routes were excluded for insufficient data.

**Best performers (by average OTP):**

| Route | Mode | Avg OTP |
|-------|------|---------|
| 18 - Manchester | BUS | 88.4% |
| BLUE - SouthHills Village | RAIL | 85.1% |
| P3 - East Busway-Oakland | BUS | 84.7% |
| SLVR - Library via Overbrook | RAIL | 84.7% |
| P1 - East Busway-All Stops | BUS | 84.5% |

**Worst performers:**

| Route | Mode | Avg OTP |
|-------|------|---------|
| 77 - Penn Hills | BUS | 55.8% |
| 61C - McKeesport-Homestead | BUS | 56.8% |
| 71B - Highland Park | BUS | 58.8% |
| 1 - Freeport Road | BUS | 61.6% |

**Most improving** (steepest positive slope): P2 - East Busway Short, G2 - West Busway.
**Most declining** (steepest negative slope): SWL - Outbound to SHJ, several rail lines.

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

406 anomalous months were flagged across 94 routes (months where OTP deviated more than 2 standard deviations from the 12-month rolling mean). The routes with the most anomalies:

| Route | Anomalies | Notes |
|-------|-----------|-------|
| RED - Castle Shannon via Beechview | 10 | Rail line with high variability |
| BLUE - SouthHills Village | 9 | Rail line |
| 40 - Mount Washington | 8 | Steep terrain |
| 61D - Murray | 8 | Long route |
| 61B - Braddock-Swissvale | 8 | Long route |

The COVID period (March--June 2020) generated positive anomalies across many routes as reduced ridership temporarily improved schedule adherence. The late 2022 cluster of negative anomalies across many routes may indicate a system-wide disruption (staffing, construction, or service restructuring).

## 6. Seasonal Patterns (Analysis 06)

PRT shows a consistent seasonal cycle:
- **Best months:** January (70.3% weighted OTP) and March
- **Worst months:** September (63.7%) and October

This is somewhat counterintuitive -- winter months outperform summer/fall despite weather. Possible explanations: lower ridership in winter reduces dwell time and crowding delays; summer construction seasons create detours; school-year schedules in fall increase congestion.

Most routes have a seasonal amplitude (best month minus worst month) under 15%. The outlier is SWL (Outbound to SHJ) with a 69% amplitude, but this route has only 13 months of data and likely reflects data sparsity rather than true seasonal effects.

## 7. Stop Count vs OTP (Analysis 07)

There is a **moderately strong negative correlation (r = -0.53)** between the number of stops on a route and its average OTP. Routes with fewer than 50 stops consistently achieve 80%+ OTP, while routes with 150+ stops struggle to reach 60%.

This is the clearest structural predictor of OTP in the dataset. Every stop adds dwell time, traffic signal delay, and schedule recovery risk. It explains why busway and limited routes outperform local routes, and suggests that stop consolidation could be an effective OTP improvement strategy.

## 8. Hot-Spot Map (Analysis 08)

6,216 stops were mapped with trip-weighted OTP values. Geographic patterns:
- **Best performance** clusters along the light rail T line (Beechview/Overbrook corridor) and the East Busway (Wilkinsburg to downtown)
- **Worst performance** clusters in the eastern neighborhoods (Penn Hills, Squirrel Hill, Highland Park) where Route 77 and other long local routes operate
- Downtown stops show middling performance -- they are served by many routes, and the average reflects the mix

The worst-performing stops (55.8% OTP) are exclusively served by Route 77 (Penn Hills), the lowest-ranked route in the system.

## 9. Monongahela Incline Investigation (Analysis 09)

The Monongahela Incline (route MI) is a **data pipeline artifact**. It exists in the routes table with mode=INCLINE and has 2 associated stops (Upper and Lower stations, 78 weekday trips), but has **zero entries in the OTP table**. OTP was never measured or reported for this route. The same is true for the Duquesne Incline (route DQI). Both inclines are physically operational and appear in the GTFS feed, but were excluded from whatever OTP measurement system generated this dataset.

## 10. Trip Frequency vs OTP (Analysis 10)

There is a **moderate negative correlation (r = -0.39)** between total weekday stop-visits and OTP. Higher-frequency routes tend to perform worse, but the relationship is weaker than the stop count correlation (r = -0.53).

This is partially confounded: high-frequency routes also tend to have more stops and serve congested corridors. The stop count effect likely drives much of this correlation. After mentally controlling for stop count, the residual frequency effect appears modest -- suggesting that running more trips per se doesn't degrade OTP much, but having a long, complex route does.

## 11. Directional Asymmetry (Analysis 11)

The correlation between directional trip imbalance and OTP is **weak (r = 0.17)** -- essentially no meaningful relationship. Routes 11 (Fineview) and 60 (McKeesport-Walnut) show 100% asymmetry (trips recorded in only one direction), but this is likely a data recording artifact rather than truly one-directional service. Most routes cluster near 0% asymmetry (well-balanced). This hypothesis did not yield actionable findings.

## Key Takeaways

1. **PRT OTP has declined** from ~69% to ~62% since 2019 and has not recovered post-COVID.
2. **Dedicated right-of-way matters most**: rail (84%) and busway (74%) routes dramatically outperform local bus (66%) routes.
3. **Stop count is the strongest predictor** of poor OTP (r = -0.53). Routes with 150+ stops consistently underperform.
4. **Geographic inequity is structural**: neighborhoods served by rail/busway enjoy 80%+ OTP, while those dependent on long local bus routes get 59--62%. The gap is stable, not worsening.
5. **Seasonality is real but modest**: September is the worst month, January the best, with a ~7pp system-wide swing.
6. **Anomalies cluster in time**: COVID (2020) and late 2022 produced system-wide anomaly bursts, suggesting external shocks rather than route-specific problems.
