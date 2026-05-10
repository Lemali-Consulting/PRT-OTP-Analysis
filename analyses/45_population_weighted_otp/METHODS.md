# Methods: Population-Weighted System OTP

## Question
What OTP does the average **resident** of PRT's service area experience, and how does it differ from the OTP of the average **route** (unweighted) or the average **scheduled trip** (trip-weighted, Analysis 19)? Service that runs reliably on lightly-populated routes should not look as good as service that runs reliably where many people live.

## Approach
- For each route, compute `population_served` = ACS tract population within walking distance of any of its stops (400 m for bus, 800 m for rail/incline), areal-interpolated against tract polygons. Same construction as Analysis 44; both analyses call the shared `prt_otp_analysis.walksheds.route_population_served()` helper.
- Restrict to routes with >= 12 months of OTP observations, matching the Analysis 19 cohort so the three weighting schemes are comparable.
- For each month, compute three system OTP series:
  1. **Unweighted**: simple mean of route OTPs.
  2. **Trip-weighted**: `sum(otp_i * trips_7d_i) / sum(trips_7d_i)` with `trips_7d` from `route_stops` (static scheduled-frequency weight).
  3. **Population-weighted**: `sum(otp_i * population_served_i) / sum(population_served_i)` (static walkshed-population weight).
- Compute summary statistics (mean, median, std, min, max) for each scheme.
- Test whether population-weighted differs significantly from trip-weighted via paired t-test and Wilcoxon signed-rank across months.
- Plot the three monthly series with a COVID marker.

**Caveat -- exposure double-counting.** Residents within the walksheds of multiple routes are counted once per route. The population-weighted OTP is therefore the OTP experienced by the *average exposure*, not the *average resident*. A resident with access to many bus routes contributes more weight than one served by a single route. This matches how a rider would perceive the system but does not estimate per-resident OTP; that would require modeling which route(s) each resident actually rides.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | Route, month, OTP | `prt.db` table |
| `route_stops` | `trips_7d` for trip-weighted baseline | `prt.db` table |
| `stops`, `routes` | For walkshed construction | `prt.db` tables |
| `census_tracts` | ACS 5-year (2018-2022) tract population, TIGER 2022 polygons | `prt.db` table (Pipeline 10) |

## Output
- `output/population_weighted_otp_trend.png` -- three-series monthly time plot
- `output/weighting_comparison.csv` -- monthly values for unweighted, trip-weighted, population-weighted
- `output/summary_stats.csv` -- mean/median/std/min/max for each scheme
- `output/route_weights.csv` -- per-route `population_served` and `trips_7d` used as weights, for transparency
