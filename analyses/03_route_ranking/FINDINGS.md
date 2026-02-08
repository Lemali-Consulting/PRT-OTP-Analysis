# Findings: Route Ranking

## Summary

94 routes had sufficient data to rank. The best performers are busway and rail routes; the worst are long local bus routes with high stop counts. 3 routes were flagged as high-volatility.

## Top 5 Routes (by average OTP)

| Route | Mode | Avg OTP | Stops |
|-------|------|---------|-------|
| 18 - Manchester | BUS | 88.4% | 43 |
| BLUE - SouthHills Village | RAIL | 85.1% | 45 |
| P3 - East Busway-Oakland | BUS | 84.7% | 40 |
| SLVR - Library via Overbrook | RAIL | 84.7% | 58 |
| P1 - East Busway-All Stops | BUS | 84.5% | 24 |

## Bottom 5 Routes (by average OTP)

| Route | Mode | Avg OTP | Stops |
|-------|------|---------|-------|
| 77 - Penn Hills | BUS | 55.8% | 258 |
| 61C - McKeesport-Homestead | BUS | 56.8% | 158 |
| 71B - Highland Park | BUS | 58.8% | 102 |
| 1 - Freeport Road | BUS | 61.6% | 221 |
| 65 - Squirrel Hill | BUS | 61.5% | 135 |

## Observations

- The most **improving** route is P2 (East Busway Short), though it has been discontinued since September 2023.
- The most **declining** route is SWL (Outbound to SHJ), though it has only 13 months of data.
- High-volatility routes (std > 2x median) include SWL, which has extreme month-to-month swings.
- 4 routes were excluded from ranking for having fewer than 12 months of data (37, 42, 53, and one other).

## Caveats

- Linear slope treats all months equally and doesn't account for structural breaks (e.g., COVID, route restructuring).
- Stop counts come from current data; historical stop counts may have differed.
