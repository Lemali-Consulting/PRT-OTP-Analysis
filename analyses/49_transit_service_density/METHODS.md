# Methods: Transit Service & Boardings vs Population Density

## Question
Analysis 46 showed that denser Allegheny County census tracts sit closer to a
PRT stop — routes are *placed* near high-density areas. Two follow-up questions:

1. **Service.** Does the *amount* of transit service at a tract scale with its
   population density, or do dense areas just get a nearby stop without
   correspondingly more service?
2. **Boardings.** Do *boardings* follow the same density gradient, or do they
   diverge from residential population density?

The unit of analysis is the census tract, mirroring Analysis 46 so the three
gradients (proximity, service, boardings) are directly comparable.

## Approach
1. **Tracts.** Load Allegheny County tracts (`county_fips = '003'`) from
   `census_tracts` via `prt_otp_analysis.walksheds.load_tracts` (polygons in
   EPSG:32617, meters). Population density = `population / land_area_km2`.
2. **Service.** From `route_stops`, sum `trips_7d` (weekly scheduled trips)
   across all routes and directions at each stop. Point-in-polygon assign each
   stop to its tract and sum to get **weekly scheduled trips serving the tract**.
3. **Boardings.** From the WPRDC bus-stop-usage data, take the pre-pandemic
   weekday snapshot (`datekey = 201909`, `serviceday = Weekday`), sum `avg_ons`
   across routes per physical stop, assign stops to tracts, and sum to get
   **average weekday boardings within the tract**.
4. **Spatial join.** Stops are matched to tracts with a point-in-polygon join
   (`geopandas.sjoin`, `predicate="within"`). Tracts with no stops keep a true
   zero for service and boardings rather than being dropped.
5. **Correlation.** Spearman rank correlation of population density against
   (a) weekly trips and (b) boardings, plus a population-density-quartile
   gradient for each. Expected sign is positive — denser tracts better served.
6. **Divergence (Q2).** Compare boardings against *population* as well as
   density: per-1,000-resident boarding rate by density quartile, a log-log
   regression of boardings on population, and the tracts with the largest
   positive/negative residuals — those that board far above or below what their
   resident population predicts.

## Data
- `census_tracts` (`prt.db`) — `geoid`, `county_fips`, `population`,
  `land_area_m2`, tract polygon. Filtered to Allegheny County.
- `route_stops` (`prt.db`) — `stop_id`, `trips_7d` (weekly scheduled trips).
- `stops` (`prt.db`) — `stop_id`, `lat`, `lon`. Null coordinates excluded.
- `data/bus-stop-usage/wprdc_stop_data.csv` — WPRDC stop-level boardings.
  Slice used: `datekey = 201909`, `serviceday = Weekday` (pre-pandemic);
  `avg_ons` is average daily boardings; the CSV carries its own `latitude`/
  `longitude` per stop.

## Output
- `output/tract_service_boardings.csv` — per tract: population, density,
  weekly trips, boardings, boardings per 1,000 residents, density quartile,
  population-predicted boardings, and regression residual.
- `output/boardings_outlier_tracts.csv` — tracts that board most above and
  below what their population predicts.
- `output/quartile_summary.csv` — per-density-quartile medians.
- `output/density_vs_service.png` — scatter of density vs weekly trips.
- `output/service_by_density_quartile.png` — median weekly trips by quartile.
- `output/density_vs_boardings.png` — scatter of density vs boardings.
- `output/boardings_by_density_quartile.png` — median boardings by quartile.
- `output/boardings_per_capita_by_quartile.png` — median boardings per 1,000
  residents by quartile (the divergence visual).
- `output/boardings_vs_population_residuals.png` — log-log boardings vs
  population with fitted line and labeled outlier tracts.

## Caveats
- Results are **area-level (ecological) associations**: they describe census
  tracts, not individual residents or their travel behavior.
- **Temporal mismatch.** Boardings are September 2019; `route_stops` trip
  counts are the current GTFS snapshot; ACS population is the 2018–2022
  5-year estimate. The analysis assumes the *spatial pattern* of density,
  service, and ridership is reasonably stable across this window even though
  absolute levels are not contemporaneous. This is the largest caveat.
- A boarding is recorded where a *trip starts*, which is weighted toward
  employment and activity centers (Downtown, Oakland) as well as residences —
  so a gap between boardings and residential density is expected, and is the
  point of the divergence analysis rather than a data flaw.
- `weekly_trips` counts scheduled trips, not vehicle capacity or time-of-day
  frequency: many low-frequency stops can sum to the same value as one
  high-frequency stop.
