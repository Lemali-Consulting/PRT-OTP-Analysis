# Findings: Neighborhood Equity

## Summary

There is a **25 percentage-point spread** in OTP between the best- and worst-served neighborhoods. The disparity is structural and stable over time -- all neighborhoods rise and fall together with the system.

## Worst-Served Neighborhoods

| Neighborhood | Municipality | OTP | Routes |
|-------------|-------------|-----|--------|
| Regent Square | Pittsburgh | 58.7% | 4 |
| Bluff | Pittsburgh | 59.2% | 16 |
| Crawford-Roberts | Pittsburgh | 61.4% | 7 |
| Squirrel Hill North | Pittsburgh | 61.6% | 12 |
| Point Breeze | Pittsburgh | 61.9% | 11 |

## Best-Served Neighborhoods

| Neighborhood | Municipality | OTP | Routes |
|-------------|-------------|-----|--------|
| Overbrook | Pittsburgh | 83.9% | 3 |
| Beechview | Pittsburgh | 80.7% | 3 |
| Brookline | Pittsburgh | 79.2% | 4 |
| Sheraden | Pittsburgh | 79.0% | 6 |
| Windgap | Pittsburgh | 78.9% | 2 |

## Frequency-Weighting Effect

Comparing trip-weighted OTP to unweighted (equal weight per route) reveals where high-frequency service diverges from the route average:

- **Mean gap**: -0.27% (small on average -- the two measures broadly agree).
- **Range**: -6.1% to +5.7% (meaningful divergence for individual neighborhoods).

| Neighborhood | Weighted | Unweighted | Gap |
|-------------|----------|------------|-----|
| Carrick | 71.0% | 77.1% | -6.1% |
| Troy Hill | 72.4% | 66.8% | +5.7% |
| Regent Square | 58.7% | 64.1% | -5.4% |

- **Negative gap** (Carrick, Regent Square): high-frequency routes underperform relative to infrequent ones. Riders experience worse OTP than the simple route average suggests.
- **Positive gap** (Troy Hill): high-frequency routes are more reliable, so the rider experience is better than the route average implies.

## Observations

- Best-performing neighborhoods are served by light rail (Overbrook, Beechview are on the T line) or short bus routes.
- Worst-performing neighborhoods depend on long local bus routes with many stops (e.g., routes 61C, 71B, 77).
- The quintile gap (Q5 - Q1) tracks roughly in parallel over time, meaning the equity disparity is baked into route structure rather than worsening.
- 89 neighborhoods analyzed; 3,760 of 6,466 stops were excluded because they lacked a neighborhood assignment in the data.

## Caveats

- OTP is weighted by current `trips_7d`, not historical ridership. Neighborhoods where service was cut would show current-frequency weights, not past ones.
- The `hood` field had some invalid values (e.g., "0") that were filtered out.
- A neighborhood's OTP reflects the routes that pass through it, not the experience of residents who may transfer between routes.
- The unweighted measure treats each route equally regardless of how many trips it runs, which can overstate the importance of infrequent routes.
