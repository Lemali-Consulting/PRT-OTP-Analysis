# Step 13: City Centerline Overlay ETL

Builds the `route_road_city` table by spatially joining GTFS route shapes to the
City of Pittsburgh street centerline (lane count, one-way flag, road class). Unlike
the PennDOT RMSSEG overlay (step 12, state roads only), the centerline includes
local 1-2 lane streets, providing an independent road-width measure for Analysis 56.

Run: `uv run python pipeline/13_city_centerline/main.py`
