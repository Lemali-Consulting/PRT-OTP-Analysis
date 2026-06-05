# City of Pittsburgh Street-Centerline Source

**Download endpoint (ArcGIS Hub, GeoJSON):**
- `https://hub.arcgis.com/api/download/v1/items/db12137760a64e86bc4ea74574c4dd30/geojson?redirect=true&layers=0&where=1=1`

**Underlying feature service:**
- `https://services1.arcgis.com/YZCmUqbcsUpOKfj7/arcgis/rest/services/PavementPublic/FeatureServer/0`

**Dataset:** "Pittsburgh Street Centerline" (City of Pittsburgh open data, `pghgishub-pittsburghpa.opendata.arcgis.com`). ~19,683 line segments covering city streets.

**Fields used:**
- `no_lanes` -- number of travel lanes (`0` and null treated as missing/unknown)
- `cfcc` -- Census Feature Class Code; only the `A1*` (limited-access freeway) prefix is used. The A2/A3/A4 distinctions are largely degenerate in this dataset (A3* lumps ~88% of streets), so they are not used for functional class.
- `oneway` -- one-way flag (`Y`/`FT`/`TF` = one-way)

**Geometry:** line features returned in WGS84 (CRS84); used directly for spatial matching (no Web-Mercator conversion needed). Segment length is computed from the equirectangular local-meters projection.

**Scope:** City of Pittsburgh limits only. Routes that travel outside the city are only partially covered; `match_rate` records the within-buffer fraction.

**Access date:** June 2026
