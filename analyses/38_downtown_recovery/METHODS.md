# Methods: Downtown Recovery Gap

## Question
Does downtown-dependent ridership explain Pittsburgh's poor system-wide recovery relative to peer cities? PRT claims that weak downtown business recovery is a primary driver of the system's lagging ridership. If true, routes that depend heavily on downtown stops should show worse recovery trajectories than routes serving other parts of the network.

## Approach
1. **Compute downtown-dependence score per route.** Using pre-pandemic stop-level ridership, calculate the fraction of each route's weekday boardings that occur at downtown stops (within 2 km of the Golden Triangle centroid at 40.4406, -79.9959 — matching analysis 33's definition).
2. **Classify routes into terciles** by downtown-dependence share: high (top third), medium, and low (bottom third). This avoids arbitrary cutoffs and ensures roughly equal group sizes.
3. **Build monthly ridership recovery trajectories.** Using `ridership_monthly` (weekday data, 2017-01 through 2024-10), index each route's ridership to its 2019 monthly average. Aggregate indexed ridership by downtown-dependence tercile to produce three recovery curves.
4. **Statistical test.** Compare 2024 recovery ratios across the three groups using Kruskal-Wallis (non-parametric, no normality assumption). If significant, apply pairwise Mann-Whitney with Bonferroni correction.
5. **Scatter plot.** Show the relationship between downtown-dependence share (continuous) and 2024 recovery ratio at the route level, with Spearman correlation.
6. **Service type segmentation.** Classify each route by service type using route ID naming conventions (`classify_bus_route`): local (plain numbers), limited (L-suffix), and commuter/express (P/O/G-prefix flyers, X-suffix express, busway). Produce faceted recovery trajectories and scatter plots by service type.
7. **Service type as covariate.** Test whether downtown dependence predicts recovery after controlling for service type using: (a) within-group Spearman correlations for each service type, (b) Kruskal-Wallis across service types, and (c) partial Spearman correlation residualizing both downtown share and recovery on service type rank.

## Data
- `data/bus-stop-usage/wprdc_stop_data.csv` — stop-level ridership with lat/lon. Filtered to `time_period == 'Pre-pandemic'` and `serviceday == 'Weekday'`. Used to compute downtown-dependence scores.
- `ridership_monthly` table — route-level monthly ridership. Filtered to `day_type == 'WEEKDAY'`. Used for recovery trajectories.
- Downtown centroid: (40.4406, -79.9959), radius 2 km (Haversine).

## Output
- `output/recovery_trajectories.png` — Monthly indexed ridership (2019=100) for high/medium/low downtown-dependence terciles.
- `output/scatter_dt_share_vs_recovery.png` — Route-level scatter of downtown share vs. 2024 recovery ratio.
- `output/recovery_by_service_type.png` — Recovery trajectories faceted by service type (local, limited, commuter/express).
- `output/scatter_by_service_type.png` — Downtown share vs. recovery scatter colored by service type.
- `output/route_downtown_scores.csv` — Per-route downtown-dependence scores, service type, and recovery ratios.
- `output/statistical_tests.csv` — Kruskal-Wallis and pairwise test results.
- `output/service_type_tests.csv` — Within-group correlations, Kruskal-Wallis by service type, and partial correlation results.
