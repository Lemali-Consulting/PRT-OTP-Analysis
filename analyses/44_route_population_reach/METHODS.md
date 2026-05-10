# Methods: Route Population Reach

## Question
Which PRT routes serve the most residents? That is, for each route, how many people live within walking distance of any stop on the route, and how do routes rank on this measure?

## Approach
- Build a stop-level point geometry from `stops.latitude` / `stops.longitude` (WGS84, EPSG:4326), reprojected to a meter-based CRS appropriate for Allegheny County (EPSG:32617, UTM 17N).
- Buffer each stop by 400 m (≈¼ mile, the standard transit walkshed for bus stops). For rail stops (mode = `RAIL`, `INCLINE`), use 800 m (≈½ mile).
- Dissolve all buffers belonging to a single route (joined via `route_stops`) into one route-level walkshed polygon, so overlapping stop buffers on the same route are not double-counted.
- Intersect each route walkshed with 2020 census tract polygons (ACS 5-year 2018–2022 vintage, Allegheny County + adjacent counties). For each tract, compute the share of tract land area covered by the walkshed and apportion tract population by that share (areal interpolation).
- Sum apportioned population across tracts to produce a `population_served` value per route.
- Report alongside `stop_count`, `route_length_km`, and `population_per_stop` to distinguish routes that reach many people because they are long vs. because they traverse dense areas.
- Rank routes; produce both a system-wide table and a top-25 chart. Stratify by mode (BUS vs. RAIL/INCLINE) since the buffer radius differs.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `stops` | Stop coordinates and mode | `prt.db` table |
| `route_stops` | Links routes to stops | `prt.db` table |
| `routes` | Route mode (BUS/RAIL/LRT/INCLINE) for buffer-radius selection | `prt.db` table |
| `census_tracts` | 2020 TIGER/Line tract polygons + ACS 5-year (2018–2022) `B01003_001E` total population, Allegheny + Washington + Westmoreland + Beaver + Butler counties. Materialized into `prt.db` by a new ingestion step at `pipeline/10_census_tracts/`. Raw shapefiles + ACS pulls cached under `data/census-tracts/`. | New `prt.db` table (US Census source) |

Filters:
- Exclude stops with NULL lat/lon.
- Exclude tracts with zero land area (water-only tracts).

## Output
- `output/route_population_reach.csv` -- one row per route: `route_id`, `mode`, `stop_count`, `route_length_km`, `walkshed_area_km2`, `population_served`, `population_per_stop`.
- `output/route_population_reach_top25.png` -- horizontal bar chart of the top 25 routes by `population_served`, colored by mode.
- `output/walkshed_map.png` -- map showing the union of all route walksheds over Allegheny County tract population density, for visual sanity-check.
