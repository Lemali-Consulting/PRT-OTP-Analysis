# Methods: Traffic Overlay ETL

## Question
How do we estimate roadway traffic exposure for each transit route?

## Approach
1. Fetch or read cached PennDOT roadway traffic segments for Allegheny County.
2. Load GTFS route geometry and densify segment points.
3. Perform KDTree spatial matching between route points and roadway segments.
4. Aggregate matched segment AADT/truck metrics by route.
5. Rebuild `route_traffic` in `prt.db`.

## Data
- PennDOT ArcGIS roadway traffic layer (AADT/truck share)
- GTFS `shapes.txt` and `trips.txt`
- Cached PennDOT JSON under `data/penndot-traffic/`

## Output
- `route_traffic` table in `data/prt.db`
