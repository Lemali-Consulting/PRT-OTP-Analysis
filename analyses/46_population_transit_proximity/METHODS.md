# Methods: Population Transit Proximity

## Question
Within Allegheny County, do more densely populated census tracts sit closer
to a PRT transit stop than sparsely populated ones? This is the proximity
counterpart to Analysis 44 (which ranks routes by the population they reach):
here the unit of analysis is the census tract, and the question is whether
the people-dense parts of the county are the best served.

## Approach
1. **Tracts.** Load Allegheny County census tracts (`county_fips = '003'`)
   from the `census_tracts` table via `prt_otp_analysis.walksheds.load_tracts`,
   which returns polygons projected to EPSG:32617 (UTM 17N, meters).
2. **Stops.** Load every PRT stop with valid coordinates from the `stops`
   table and project the points to the same meter-based CRS.
3. **Proximity.** For each tract, compute the straight-line distance from the
   tract polygon centroid to the nearest stop, using a nearest-neighbor
   spatial join (`geopandas.sjoin_nearest`).
4. **Density.** Compute population density as `population / land_area_km2`
   (land area converted from the table's `land_area_m2`).
5. **Correlation.** Test the association between tract population density and
   distance to the nearest stop with a Spearman rank correlation. The expected
   sign is negative — denser tracts closer to transit. A positive sign would
   be a red flag, not a finding.
6. **Density-quartile gradient.** Split tracts into population-density
   quartiles and report the median distance to the nearest stop in each, to
   show the gradient in plain terms.
7. **Coverage.** Classify each tract as within 805 m (≈ 1/2 mile) of a stop
   and report both the share of tracts and the share of county population that
   falls inside that walk-shed.

## Data
- `census_tracts` (`prt.db`) — `geoid`, `county_fips`, `population`,
  `land_area_m2`, tract polygon (`geometry_wkt`). Filtered to Allegheny County.
- `stops` (`prt.db`) — `stop_id`, `lat`, `lon`. Stops with null coordinates
  are excluded.

## Output
- `output/tract_transit_proximity.csv` — per tract: population, density,
  distance to nearest stop, density quartile, and within-805 m flag.
- `output/density_vs_distance.png` — scatter of tract population density
  against distance to the nearest stop, with the Spearman result annotated.
- `output/distance_by_density_quartile.png` — bar chart of median distance to
  the nearest stop by population-density quartile.

## Caveats
- Results are **area-level (ecological) associations**: they describe census
  tracts, not individual residents or their travel behavior.
- Distance is straight-line from the tract centroid, not a network walk.
  Rivers, hillsides, and highways mean the real walk is often longer, and a
  centroid can misrepresent a large or irregularly shaped tract.
- Stop *presence* is not service *quality*: a nearby stop may be served
  infrequently. Proximity is a necessary, not sufficient, condition for useful
  transit access.
