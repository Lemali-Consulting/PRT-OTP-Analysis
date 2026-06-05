# PennDOT RMSSEG Road-Classification Source

**API Endpoints:**
- `https://gis.penndot.gov/arcgis/rest/services/opendata/roadwaysegments/MapServer/0/query`
- `https://gis.penndot.gov/arcgis/rest/services/opendata/roadwayadmin/MapServer/0/query`

**Filter:** `CTY_CODE = '02'` (Allegheny County)

**Fields used:**

*roadwaysegments* (RMSSEG State Roads):
- `OBJECTID` -- unique segment identifier
- `NLF_ID` -- linear-feature id used to join the admin layer
- `SEG_LNGTH_FEET` -- segment length in feet
- `LANE_CNT` -- number of through lanes
- `DIVSR_TYPE` -- median/divider type code (`0` = undivided; any other code = divided)

*roadwayadmin*:
- `NLF_ID` -- linear-feature id (join key)
- `SEG_LNGTH_FEET` -- segment length in feet (length-weighting within an NLF_ID)
- `FHWA_FUNC_CLS` / `FUNC_CLS` -- FHWA functional classification (1 = Interstate ... 7 = Local)
- `SPEED_LIMIT` -- posted speed limit (mph)

**Geometry:** roadwaysegments polyline paths returned in EPSG:3857 (Web Mercator), converted to WGS84 for spatial matching. The admin layer is fetched without geometry and joined by `NLF_ID`.

**Access date:** June 2026
