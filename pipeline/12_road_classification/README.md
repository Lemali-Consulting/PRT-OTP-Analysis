# 12 - Road Classification Overlay

Fetches PennDOT RMSSEG road attributes (lane count, functional class, posted speed, median type) and spatially matches them to GTFS route geometry. Writes `route_road_class` into `prt.db` with length-weighted road-type metrics per route.
