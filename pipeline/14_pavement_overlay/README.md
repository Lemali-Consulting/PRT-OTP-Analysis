# Step 14: NHS Pavement-Condition Overlay ETL

Builds the `route_road_pavement` table by spatially joining GTFS route shapes to
SPC's National Highway System pavement-condition layer (pavement roughness / IRI,
overall pavement index, poor-condition share). Unlike the road-geometry overlays
(steps 12-13: lane count, functional class), this captures road *quality* for
Analysis 57.

Run: `uv run python pipeline/14_pavement_overlay/main.py`
