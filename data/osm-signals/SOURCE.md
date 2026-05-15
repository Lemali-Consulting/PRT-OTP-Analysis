# OpenStreetMap Traffic Signal Data Source

**API Endpoint:** `https://overpass-api.de/api/interpreter`

**Query:** Overpass QL request for nodes tagged `highway=traffic_signals` within
the Allegheny County bounding box `(40.18, -80.37, 40.68, -79.69)` (south, west,
north, east in WGS84).

```
[out:json][timeout:120];
node["highway"="traffic_signals"](40.18,-80.37,40.68,-79.69);
out body;
```

**Fields used:**
- `lat`, `lon` -- node coordinates in WGS84

**Notes:** OpenStreetMap traffic-signal coverage is crowd-sourced and may be
incomplete or lag real-world signal installation. Coincident nodes are
deduplicated to ~1 m precision.

**Access date:** May 2026
