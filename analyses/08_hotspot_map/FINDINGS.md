# Findings: Hot-Spot Map

## Important: Derived Metric

Stop-level OTP is a **derived metric**: each stop inherits the average OTP of the routes serving it, weighted by trip frequency (`trips_7d`). It reflects route composition at each stop, not independently measured stop-level performance. A stop served by a single high-OTP route will appear "high-performing" even if that stop is a chronic delay point on that route. Conversely, a stop served by many routes will reflect the blended average of those routes.

## Summary

6,212 stops were mapped with route-weighted OTP (after excluding 2 stops with null/NaN OTP due to zero total trips, and excluding routes with fewer than 12 months of data). Poor performance clusters in **eastern Pittsburgh** (Penn Hills, Squirrel Hill, Highland Park), while the best performance follows the **light rail and busway corridors**.

## Geographic Patterns

- **Best corridors:** The light rail T line (Beechview/Overbrook south to Library) and the East Busway (Wilkinsburg to downtown) form clear green bands on the map, with 80%+ OTP at most stops.
- **Worst corridors:** Eastern neighborhoods served by Route 77 (Penn Hills) show the lowest stop-level OTP at 55.8%. The 61-series routes through McKeesport and Homestead also form a low-OTP cluster.
- **Downtown:** Mixed performance. Stops in the Golden Triangle are served by many routes, so their weighted OTP reflects the system average (~65--70%).

## Mode Context

The best-performing stops (88.4%) are all served exclusively by BUS routes -- specifically Route 18 (Manchester). The high-OTP corridor along the T line reflects rail's structural advantage (dedicated right-of-way), not independently measured stop performance. When interpreting the map:

- **Rail stops** (light rail T line) appear green primarily because RAIL routes average ~84% OTP system-wide. These stops' high performance reflects mode advantage, not stop-specific factors.
- **Busway stops** (East Busway, West Busway) also appear green for similar reasons -- dedicated right-of-way.
- **Genuinely high-performing bus stops** include those on Route 18 (Manchester, 88.4%) and Route 39 (Brookline), which achieve high OTP on mixed-traffic streets.

## Observations

- The worst-performing stops (55.8%) are exclusively served by Route 77, the system's lowest-ranked route.
- The best-performing stops (88.4%) are exclusively served by Route 18 (Manchester) -- a bus route, not rail.
- Stops served by multiple routes tend toward the system mean, since the weighting blends good and bad routes.
- The system average displayed in the chart title (unweighted stop-level average) treats every stop equally regardless of trip volume. A trip-weighted system average would differ slightly.

## Caveats

- The map uses a simple lat/lon scatter, not a true geographic projection. At Pittsburgh's latitude, this introduces minor distortion but the overall shape is recognizable.
- Stops with null or NaN OTP values (2 stops) were **excluded** from the map.
- OTP is averaged across all months (2019--2025), so the map doesn't show temporal changes.
- Routes with fewer than 12 months of OTP data were excluded to avoid projecting noisy estimates onto the map.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) -- 7 issues (1 significant). Documented derived-metric nature of stop OTP, added mode column and bus/rail context, added minimum 12-month filter for route OTP, clarified unweighted system average, corrected NaN claim, fixed hood="0" sentinel, added dropped-stop logging.
