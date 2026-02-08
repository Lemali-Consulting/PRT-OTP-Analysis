# Findings: Hot-Spot Map

## Summary

6,216 stops were mapped with trip-weighted OTP. Poor performance clusters in **eastern Pittsburgh** (Penn Hills, Squirrel Hill, Highland Park), while the best performance follows the **light rail and busway corridors**.

## Geographic Patterns

- **Best corridors:** The light rail T line (Beechview/Overbrook south to Library) and the East Busway (Wilkinsburg to downtown) form clear green bands on the map, with 80%+ OTP at most stops.
- **Worst corridors:** Eastern neighborhoods served by Route 77 (Penn Hills) show the lowest stop-level OTP at 55.8%. The 61-series routes through McKeesport and Homestead also form a low-OTP cluster.
- **Downtown:** Mixed performance. Stops in the Golden Triangle are served by many routes, so their weighted OTP reflects the system average (~65--70%).

## Observations

- The worst-performing stops (55.8%) are exclusively served by Route 77, the system's lowest-ranked route.
- The best-performing stops (88.4%) are exclusively served by Route 18 (Manchester).
- Stops served by multiple routes tend toward the system mean, since the weighting blends good and bad routes.

## Caveats

- The map uses a simple lat/lon scatter, not a true geographic projection. At Pittsburgh's latitude, this introduces minor distortion but the overall shape is recognizable.
- Some stops had invalid or zero-valued `hood` fields and produced NaN OTP values; these were included in the map but may appear as missing-color dots.
- OTP is averaged across all months (2019--2025), so the map doesn't show temporal changes.
