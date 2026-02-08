# Analysis Proposal

Potential analyses using the PRT on-time performance database (`data/prt.db`).

## 1. Temporal / Trend Analysis

### System-wide trend line
Is PRT getting more or less on-time over the 7-year window (2019--2025)? A trip-weighted average (using `trips_7d` from `route_stops`) would be more meaningful than a simple mean across routes, since high-frequency routes affect more riders.

### COVID impact and recovery
OTP visibly shifted in early 2020 -- many routes actually *improved* during low-ridership months. How long did recovery take? Did some routes never return to their pre-COVID baseline?

### Seasonal patterns
Do summer months consistently underperform winter, or vice versa? Construction seasons, weather, and ridership fluctuations could cut both ways. Decomposing each route's OTP into trend + seasonal + residual would reveal this.

### Year-over-year slope per route
Which routes are trending up vs. down? A route that went from 0.80 to 0.65 over 5 years tells a different story than one that has been stable at 0.65 the whole time.

## 2. Route Comparisons

### Mode comparison (BUS vs RAIL vs INCLINE)
Light rail runs on dedicated right-of-way, so it should outperform bus. Does it? By how much? And does the gap change over time?

### Local vs Limited vs Express
Do `L` (limited) and `X`/Flyer routes consistently beat their local counterparts? Routes like 51 vs 51L are natural experiments -- same corridor, different stopping patterns.

### Volatility ranking
Standard deviation of OTP per route. A route averaging 0.70 with low variance is arguably more *reliable* than one averaging 0.75 with wild swings. Ranking routes by consistency (not just average) could surface different insights.

## 3. Geographic / Spatial

### Stop count vs OTP
Do routes with more stops (from `route_stops`) have worse OTP? Each stop is another chance to fall behind schedule. A scatter plot of stop count vs. average OTP would test this.

### Neighborhood equity
Using `hood` and `muni` from the stops table, aggregate OTP by neighborhood. Are certain communities systematically underserved by on-time performance? This is likely the most policy-relevant question in the dataset.

### Hot-spot mapping
Overlay route OTP onto stop locations to visualize where poor performance clusters geographically. Routes with many shared stops in a corridor could reveal bottleneck areas.

## 4. Anomaly Investigation

### Sharp drop forensics
Several routes show dramatic OTP collapses that may reflect route restructuring, detours, or data issues rather than true performance:
- **15 - Charles**: drops to ~0.35 in Jul--Sep 2022, then rebounds to ~0.80
- **65 - Squirrel Hill**: drops to 0.28--0.37 in mid-2023
- **7 - Spring Garden**: value of 0.2863 in Aug 2025

Cross-referencing dates with PRT service changes, construction projects, or detours could explain these. (See also `QUESTIONS.md`.)

### The Monongahela Incline mystery
Row exists in OTP data with zero values. Was it truly never measured, or is this a data pipeline artifact?

## 5. Service Planning Insights

### Trip frequency vs OTP
Using `trips_wd` from `route_stops`, is there a correlation between how often a route runs and how on-time it is? High-frequency routes may suffer more from schedule adherence issues like bunching and cascading delays.

### Inbound vs Outbound asymmetry
OTP data is route-level, but stop and trip data is directional. If a route has significantly more IB than OB trips (or vice versa), does that structural imbalance correlate with worse OTP?

## Suggested priority

1. **System-wide trend** -- the big picture, answers "is PRT getting better or worse?"
2. **Neighborhood equity** -- the most policy-relevant question
3. **Mode and route-type comparisons** -- low-hanging fruit with clear structure
