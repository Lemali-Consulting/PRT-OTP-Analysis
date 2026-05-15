# Methods: Signal Overlay ETL

## Question
How many traffic signals does each transit route pass, and what is its signal density?

## Approach
1. Fetch or read cached OpenStreetMap `highway=traffic_signals` nodes for the
   Allegheny County bounding box via the Overpass API.
2. Load GTFS route geometry; compute each route's representative length as the
   length of its longest single GTFS shape (an ordered polyline).
3. Build a KDTree of signal points and, for each densified route shape, count
   the unique signals within 30 m.
4. Compute `signal_density = n_signals / length_km`.
5. Rebuild `route_signals` in `prt.db`.

## Data
- OpenStreetMap Overpass traffic-signal nodes
- GTFS `shapes.txt` and `trips.txt`
- Cached Overpass JSON under `data/osm-signals/`

## Output
- `route_signals` table in `data/prt.db`
