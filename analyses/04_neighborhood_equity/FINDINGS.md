# Findings: Neighborhood Equity

## Summary

There is a **25 percentage-point spread** in OTP between the best- and worst-served neighborhoods (all modes pooled). When restricted to **bus-only**, the spread narrows to 20 pp but the bottom neighborhoods remain the same. The disparity is structural and stable over time -- all neighborhoods rise and fall together with the system. OTP is now computed from route-level averages (each route weighted once regardless of how many months of data it has), weighted by trip frequency.

## Worst-Served Neighborhoods

| Neighborhood | Municipality | OTP (pooled) | OTP (bus-only) | Routes |
|-------------|-------------|-------------|---------------|--------|
| Regent Square | Pittsburgh | 58.8% | 58.8% | 4 |
| Bluff | Pittsburgh | 59.2% | 59.2% | 16 |
| Crawford-Roberts | Pittsburgh | 61.4% | 61.4% | 7 |
| Squirrel Hill North | Pittsburgh | 61.6% | 61.6% | 12 |
| Highland Park | Pittsburgh | 61.9% | 61.9% | 5 |

The bottom neighborhoods are served entirely by bus, so their pooled and bus-only OTP are identical.

## Best-Served Neighborhoods

| Neighborhood | Municipality | OTP (pooled) | OTP (bus-only) | Routes (all) | Routes (bus) |
|-------------|-------------|-------------|---------------|-------------|-------------|
| Overbrook | Pittsburgh | 83.9% | 78.9% | 3 | 1 |
| Beechview | Pittsburgh | 80.7% | 75.5% | 3 | 2 |
| Brookline | Pittsburgh | 79.2% | 78.7% | 4 | 2 |
| Sheraden | Pittsburgh | 79.0% | 79.0% | 6 | 6 |
| Windgap | Pittsburgh | 78.9% | 78.9% | 2 | 2 |

## Bus-Only Stratification (Simpson's Paradox Check)

Restricting to BUS-mode routes reveals that some neighborhoods' high pooled OTP is driven by rail:

| Neighborhood | Pooled OTP | Bus-Only OTP | Pooled Rank | Bus Rank | Shift |
|-------------|-----------|-------------|------------|---------|-------|
| Bon Air | 75.3% | 66.7% | 13 | 53 | -40 |
| North Shore | 74.5% | 70.7% | 17 | 36 | -19 |
| Beechview | 80.7% | 75.5% | 2 | 11 | -9 |

**Bon Air** is a clear case of Simpson's paradox: it appears well-served in the pooled analysis (rank 13) but drops to rank 53 (bus-only) because its high pooled OTP is driven almost entirely by rail service. Beechview similarly drops 9 positions.

The bus-only spread (20 pp) is narrower than the pooled spread (25 pp), confirming that rail inflates the apparent equity of neighborhoods it serves.

## Frequency-Weighting Effect

Comparing trip-weighted OTP to unweighted (equal weight per route) reveals where high-frequency service diverges from the route average:

- **Mean gap**: -0.27% (small on average -- the two measures broadly agree).
- **Range**: -6.1% to +5.7% (meaningful divergence for individual neighborhoods).

| Neighborhood | Weighted | Unweighted | Gap |
|-------------|----------|------------|-----|
| Carrick | 71.1% | 77.2% | -6.1% |
| Troy Hill | 72.4% | 66.7% | +5.7% |
| Regent Square | 58.8% | 64.1% | -5.4% |

- **Negative gap** (Carrick, Regent Square): high-frequency routes underperform relative to infrequent ones. Riders experience worse OTP than the simple route average suggests.
- **Positive gap** (Troy Hill): high-frequency routes are more reliable, so the rider experience is better than the route average implies.

## Observations

- Best-performing neighborhoods are served by light rail (Overbrook, Beechview are on the T line) or short bus routes.
- Worst-performing neighborhoods depend on long local bus routes with many stops (e.g., routes 61C, 71B, 77).
- The quintile gap (Q5 - Q1) tracks roughly in parallel over time, meaning the equity disparity is baked into route structure rather than worsening.
- 89 neighborhoods analyzed; 3,760 of 6,466 stops were excluded because they lacked a neighborhood assignment in the data.
- Routes with fewer than 12 months of OTP data are excluded from the analysis.

## Caveats

- **Sample size varies widely**: neighborhoods have between 1 and 74 routes. The 25 pp spread should be interpreted with this context -- neighborhoods with only 1-2 routes have OTP estimates driven by a single route's performance, while those with 10+ routes have more stable estimates. A neighborhood served by one bad route will look worse than a neighborhood with a diversified mix.
- **Panel balance (time series)**: The quintile time series uses an unbalanced panel. Neighborhoods gaining or losing routes over time may show OTP changes from composition shifts (a route entering or exiting), not performance changes. This could create artificial trends in the quintile chart, though the overall pattern of parallel movement suggests this effect is small.
- OTP is weighted by current `trips_7d`, not historical ridership. Neighborhoods where service was cut would show current-frequency weights, not past ones.
- The `hood` field had some invalid values (e.g., "0") that were filtered out.
- A neighborhood's OTP reflects the routes that pass through it, not the experience of residents who may transfer between routes.
- The unweighted measure treats each route equally regardless of how many trips it runs, which can overstate the importance of infrequent routes.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) — 7 issues (1 significant). Fixed time-pooled weighting (pre-aggregate OTP to route level before joining), added bus-only stratification revealing Simpson's paradox in Bon Air and Beechview, added NULL trips_7d filter, added minimum-month filter, documented panel balance caveat, added sample-size caveat, and clarified METHODS.md weighting description.
