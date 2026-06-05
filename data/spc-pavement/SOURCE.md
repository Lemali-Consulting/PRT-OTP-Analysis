# SPC NHS Pavement-Condition Source

**Feature service (ArcGIS REST, queried as paged GeoJSON in WGS84):**
- `https://services3.arcgis.com/MV5wh5WkCMqlwISp/arcgis/rest/services/PM2_Roadways/FeatureServer/0`

**Dataset:** "PM2_Roadways" (layer name `NHS_Pavement_Condition`), published by the
Southwestern Pennsylvania Commission (SPC), the Pittsburgh-region MPO, in its ArcGIS
Online org (`spcgis`). "PM2" refers to FHWA's Pavement and Bridge Condition (TPM /
PM2) performance measures, reported on the National Highway System. Derived from
PennDOT roadway-management (RMS) data. ~6,256 NHS line segments in the region; 5,202
carry a usable roughness reading.

**Fields used:**
- `ROUGH_INDX` -- International Roughness Index (IRI), inches/mile. Higher = rougher.
  Filtered to `> 0` (segments without a measured value are excluded at query time).
- `OVERALL_PV` -- overall pavement index (OPI); higher = better condition. `0` treated
  as missing/unmeasured.
- `IRI_RATING` -- categorical IRI rating (`GOOD` / `FAIR` / `POOR`); `POOR` drives the
  poor-condition share.

**Scope:** **National Highway System only** -- interstates and principal arterials.
Local and minor-collector streets are not in this layer. Bus routes are matched only
along their NHS portions; `match_rate` records the within-buffer NHS fraction of each
route. This is a narrower network than the PennDOT RMSSEG (Analysis 55) and
city-centerline (Analysis 56) layers.

**Geometry:** line features returned in WGS84 via `outSR=4326`, `f=geojson`, paged
1000 features per request. Segment length is computed from the equirectangular
local-meters projection (same as the other road overlays).

**Access date:** June 2026
