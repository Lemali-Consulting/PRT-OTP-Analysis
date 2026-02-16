# Additional Data Requests

The multivariate model (Analysis 18) explains 47% of OTP variance using structural route characteristics (stop count, geographic span, mode). The remaining 53% reflects operational and environmental factors absent from this dataset. This document identifies the most valuable additional data sources, ordered by expected analytical impact.

**Update (Feb 2026):** Four items have been obtained and analyzed since initial writing. See "Obtained" section below for results.

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

### 3. Construction and detour records

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

### 5. On-time performance definition and measurement methodology

**What:** PRT's internal documentation of how OTP is calculated -- threshold (e.g., 0-5 min late), measurement points (all stops vs timepoints vs origin/destination), and data source (AVL, manual, GPS).

**Why:** DATA_DICTIONARY.md flags that the "on-time" definition is unspecified. Different thresholds and measurement points would produce different numbers. Understanding the methodology would improve interpretation of all 27 analyses.

**Likely source:** PRT performance standards documentation, board presentations, or FTA reporting guidelines.

### 6. Vehicle fleet data (age, type, capacity)

**What:** Bus/rail vehicle assignments by route, including vehicle age and type.

**Why:** Older vehicles may break down more often, and vehicle capacity affects dwell time. This is a second-order effect unlikely to dominate, but could explain residual variance for specific routes.

**Likely source:** PRT fleet inventory (often published in capital plans or NTD reports).

### 7. Signal priority and transit infrastructure data

**What:** Locations of transit signal priority (TSP), bus-only lanes, queue jumps, and other infrastructure investments.

**Why:** Analysis 02 showed that dedicated right-of-way is the strongest mode-level predictor. Granular infrastructure data would let us test whether TSP or bus lanes produce measurable OTP improvements at specific locations.

**Likely source:** PRT or City of Pittsburgh traffic engineering department. Some TSP locations are documented in regional transportation plans.

---

## Obtained Data (completed)

These items have been acquired and analyzed. Summarized here for reference.

### Ridership data (originally #3)

**Obtained:** Route-level monthly average weekday ridership from PRT open data (Jan 2017 -- Oct 2024), loaded into `ridership_monthly` table.

**Result:** Ridership does not add explanatory power to the multivariate model (Analysis 26: F=2.53, p=0.116, R2 change +1.5pp). High ridership does not independently degrade OTP -- poor-performing routes happen to have high ridership because they are long, many-stop corridors. However, ridership enabled Analyses 19-25 (ridership-weighted OTP, delay burden, equity, causality, COVID recovery, day-type trends).

### Traffic volume data (originally #4)

**Obtained:** PennDOT AADT (Annual Average Daily Traffic) for 2,923 Allegheny County road segments via ArcGIS REST API. Spatially joined to GTFS route shapes via KDTree; loaded into `route_traffic` table.

**Result:** AADT is not significant after structural controls (Analysis 27: F=0.011, p=0.92). Truck percentage is significant (p=0.006, +5pp R2), likely proxying for arterial road classification. The null result is attributed to AADT being a 24-hour annual average that does not capture peak-hour congestion. **Time-of-day traffic speed data** (e.g., INRIX) remains the strongest untested congestion variable.

### Weather data (originally #3)

**Obtained:** NOAA GHCND daily weather from Pittsburgh International Airport (station USW00094823) via NCEI Access Data Service v1, covering Jan 2019 -- Dec 2025 (2,557 daily records). Aggregated to monthly and loaded into `weather_monthly` table. Fields: precipitation, snowfall, temperature (max/min), freeze days, hot days, wind speed.

**Result:** Weather shows moderate detrended correlations with system OTP (freeze_days r=+0.57, mean_tmin r=-0.57) but in the counterintuitive direction -- cold months have *better* OTP. Weather is statistically interchangeable with month-of-year dummies (neither adds significantly beyond the other: F=0.92, p=0.48 and F=1.09, p=0.39). At the route-month level, weather explains only 4.5% of within-route OTP variation and is non-significant with cluster-robust SEs. The seasonal pattern reflects lower winter demand/congestion rather than a direct weather impediment.

### Depot/operator assignments (originally #6)

**Obtained:** Garage assignments from the `current_garage` field in ridership data (4 garages: Ross, Collier, East Liberty, West Mifflin).

**Result:** Garage is significant after structural controls (Analysis 23: F=4.55, p=0.005, R2 increase from 0.31 to 0.41). Collier routes run +5.4pp above East Liberty after controls (p<0.001). West Mifflin's poor raw performance is explained by route structure.

---

## Summary Table

| # | Data Source | Primary Gap Addressed | Expected Impact on R² | Availability |
|---|-----------|----------------------|----------------------|-------------|
| 1 | AVL stop-level arrivals | Ecological fallacy in stop/neighborhood analyses | High | FOIA or data agreement |
| 2 | Historical GTFS feeds | Static weights, schedule changes | Medium-High | Public archives |
| 3 | ~~Weather data~~ | ~~Seasonal/anomaly attribution~~ | ~~Medium~~ | **Obtained** (Analysis 28) |
| 4 | Construction/detour records | Anomaly attribution | Low-Medium | Service alerts |
| 5 | OTP definition docs | Interpretation of all analyses | Low (interpretive) | PRT documentation |
| 6 | Vehicle fleet data | Residual variance | Low | NTD or capital plans |
| 7 | Signal priority locations | Infrastructure impact | Low | Traffic engineering |
