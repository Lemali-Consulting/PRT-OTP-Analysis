# Additional Data Requests

The multivariate model (Analysis 18) explains 47% of OTP variance using structural route characteristics (stop count, geographic span, mode). The remaining 53% reflects operational and environmental factors absent from this dataset. This document identifies the most valuable additional data sources, ordered by expected analytical impact.

---

## High Priority

These would directly address the largest gaps in the current analysis.

### 1. Automatic Vehicle Location (AVL) data -- stop-level arrival times

**What:** Timestamped vehicle arrivals at each stop, ideally with scheduled vs actual times.

**Why:** The single biggest limitation of this project is that OTP is measured at the route-month level. Every analysis that projects OTP onto stops or neighborhoods (Analyses 04, 08, 15, 16) commits an ecological fallacy -- a route's average OTP is not uniform across its stops. AVL data would reveal *where along each route* delays accumulate, transforming descriptive findings into actionable diagnostics.

**What it would enable:**
- True stop-level OTP (which stops are chronic delay points?)
- Delay propagation analysis (does a delay at stop 5 cascade through the rest of the route?)
- Dwell time decomposition (boarding time vs signal time vs traffic time)
- Schedule adherence profiles (early running vs late running by time of day)

**Likely source:** PRT's internal CAD/AVL system. May be available via FOIA or data sharing agreement. Some agencies publish this as part of GTFS-Realtime archives.

---

### 2. Historical GTFS schedule feeds (2019--2025)

**What:** Archived GTFS static feeds for each service period, containing stop_times, trips, calendar, and shapes.

**Why:** The current `route_stops` table is a single snapshot applied across 7 years of OTP data. Service levels changed dramatically (COVID cuts, post-COVID restructuring). This creates a static-weights problem flagged in METHODOLOGY-ISSUES.md (Issues 1, 2) and limits the multivariate model to current-period features only.

**What it would enable:**
- Time-varying trip counts for proper weighting of system trends (Analysis 01)
- Detection of service changes that explain OTP anomalies (Analysis 05)
- Route-level schedule changes as an independent variable in the multivariate model
- Precise route length from GTFS shapes (more accurate than stop-to-stop span)
- Scheduled running time per route, enabling a "schedule slack" predictor

**Likely source:** [Mobility Database](https://database.mobilitydata.org/) or [transitfeeds.com](https://transitfeeds.com/) archive PRT's historical GTFS feeds. PRT may also maintain an internal archive.

---

### 3. Ridership data (boardings per route or stop)

**What:** Monthly or daily boardings per route, ideally per stop. Farebox or APC (automatic passenger counter) data.

**Why:** The multivariate model has no demand-side variable. High-ridership routes likely have longer dwell times (more boarding/alighting), more crowding delays, and more variability. Ridership also matters for equity analysis -- a route with 60% OTP carrying 10,000 riders/day has far more impact than one carrying 500.

**What it would enable:**
- Ridership-weighted OTP as a more meaningful system metric
- Dwell time modeling (boardings as a predictor of delay)
- Ridership × OTP as a passenger-impact metric for prioritization
- Demand elasticity: does poor OTP reduce ridership over time?

**Likely source:** PRT publishes aggregate ridership in annual reports. Stop-level APC data would require a data request. NTD (National Transit Database) has route-level ridership for all FTA recipients.

---

## Medium Priority

These would strengthen specific analyses or enable new ones.

### 4. Traffic volume and congestion data

**What:** Average traffic speeds or congestion indices along major corridors, by time of day and month.

**Why:** Analysis 12 showed geographic span independently degrades OTP, suggesting exposure to traffic conditions matters. But "span" is a crude proxy -- a 20 km route through suburbs faces different conditions than a 20 km route through downtown. Corridor-level traffic data would let us test whether congestion explains the residual variance the model can't capture.

**What it would enable:**
- Traffic congestion as a direct predictor in the multivariate model
- Identification of specific corridor bottlenecks
- Time-of-day analysis (peak vs off-peak OTP, if combined with AVL data)

**Likely source:** PennDOT or SPC (Southwestern Pennsylvania Commission) maintain traffic count stations. Google Maps or HERE provide historical traffic data commercially. INRIX publishes corridor-level speed data for many metro areas.

---

### 5. Weather data (daily precipitation, temperature, snow)

**What:** Daily weather observations for the Pittsburgh region (precipitation, snowfall, temperature, ice events).

**Why:** Analysis 06 found that winter months actually outperform fall, which is counterintuitive. Weather data would test whether snow days specifically degrade OTP (even if winter overall is fine due to lower ridership), and whether summer construction + heat events explain the fall trough.

**What it would enable:**
- Weather as a control variable in seasonal analysis
- Extreme weather event attribution for anomaly detection
- Snow/ice impact quantification for operational planning

**Likely source:** NOAA/NWS station data for Pittsburgh International Airport (KPIT), freely available via [weather.gov](https://www.weather.gov/) or the NCEI API.

---

### 6. Operator/depot assignment data

**What:** Which garage/depot operates each route, and ideally staffing levels or operator seniority.

**Why:** Analysis 13 found clusters of routes that co-move in OTP. One plausible explanation is shared depot assignment -- if a depot is short-staffed, all its routes suffer simultaneously. Without depot data, we can't distinguish "shared corridor" effects from "shared workforce" effects.

**What it would enable:**
- Depot-level OTP analysis (are some depots systematically worse?)
- Staffing as a predictor of OTP variation
- Causal interpretation of the correlation clusters from Analysis 13

**Likely source:** PRT internal operations data. Depot-route assignments are sometimes published in service plans or union documents.

---

### 7. Construction and detour records

**What:** Dates, locations, and affected routes for road construction, utility work, and planned detours.

**Why:** Analysis 05 found clusters of negative anomalies in late 2022 that may reflect system-wide disruption. Construction is a major source of OTP degradation but leaves no trace in the current dataset. A construction calendar would enable systematic attribution of anomalies.

**What it would enable:**
- Construction-adjusted OTP baselines
- Anomaly attribution beyond COVID
- Corridor-level impact assessment

**Likely source:** PRT service alerts (archived GTFS-RT or website scrapes). City of Pittsburgh and PennDOT construction permit databases.

---

## Lower Priority

Useful for completeness but unlikely to change major conclusions.

### 8. On-time performance definition and measurement methodology

**What:** PRT's internal documentation of how OTP is calculated -- threshold (e.g., 0-5 min late), measurement points (all stops vs timepoints vs origin/destination), and data source (AVL, manual, GPS).

**Why:** DATA_DICTIONARY.md flags that the "on-time" definition is unspecified. Different thresholds and measurement points would produce different numbers. Understanding the methodology would improve interpretation of all 18 analyses.

**Likely source:** PRT performance standards documentation, board presentations, or FTA reporting guidelines.

### 9. Vehicle fleet data (age, type, capacity)

**What:** Bus/rail vehicle assignments by route, including vehicle age and type.

**Why:** Older vehicles may break down more often, and vehicle capacity affects dwell time. This is a second-order effect unlikely to dominate, but could explain residual variance for specific routes.

**Likely source:** PRT fleet inventory (often published in capital plans or NTD reports).

### 10. Signal priority and transit infrastructure data

**What:** Locations of transit signal priority (TSP), bus-only lanes, queue jumps, and other infrastructure investments.

**Why:** Analysis 02 showed that dedicated right-of-way is the strongest mode-level predictor. Granular infrastructure data would let us test whether TSP or bus lanes produce measurable OTP improvements at specific locations.

**Likely source:** PRT or City of Pittsburgh traffic engineering department. Some TSP locations are documented in regional transportation plans.

---

## Summary Table

| # | Data Source | Primary Gap Addressed | Expected Impact on R² | Availability |
|---|-----------|----------------------|----------------------|-------------|
| 1 | AVL stop-level arrivals | Ecological fallacy in stop/neighborhood analyses | High | FOIA or data agreement |
| 2 | Historical GTFS feeds | Static weights, schedule changes | Medium-High | Public archives |
| 3 | Ridership (boardings) | No demand-side variable | Medium-High | NTD or PRT reports |
| 4 | Traffic/congestion data | Corridor-level conditions | Medium | PennDOT, commercial |
| 5 | Weather data | Seasonal/anomaly attribution | Medium | NOAA (free) |
| 6 | Depot/operator assignments | Cluster causation | Medium | PRT internal |
| 7 | Construction/detour records | Anomaly attribution | Low-Medium | Service alerts |
| 8 | OTP definition docs | Interpretation of all analyses | Low (interpretive) | PRT documentation |
| 9 | Vehicle fleet data | Residual variance | Low | NTD or capital plans |
| 10 | Signal priority locations | Infrastructure impact | Low | Traffic engineering |
