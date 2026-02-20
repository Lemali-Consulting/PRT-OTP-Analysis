# PennDOT AADT Data Source

**API Endpoint:** `https://gis.penndot.gov/arcgis/rest/services/opendata/roadwaytraffic/MapServer/0/query`

**Filter:** `CTY_CODE = '02'` (Allegheny County)

**Fields used:**
- `OBJECTID` -- unique segment identifier
- `CUR_AADT` -- Current Annual Average Daily Traffic count
- `TRK_PCT` -- truck percentage of total traffic
- `SEG_LNGTH_FEET` -- segment length in feet
- `ST_RT_NO` -- state route number
- `CTY_CODE` -- county code (02 = Allegheny)

**Geometry:** Polyline paths returned in EPSG:3857 (Web Mercator), converted to WGS84 for spatial matching.

**Access date:** February 2026
