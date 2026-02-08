# Findings: Route Ranking

## Summary

94 routes had sufficient data (12+ months) to rank. Rankings use **trailing 12-month average OTP** to reflect current performance, and **post-2022 slope** to capture recent trajectory without COVID distortion. 3 routes were flagged as high-volatility.

## Top 5 Routes (by trailing 12-month OTP)

| Route | Mode | Recent OTP | All-Time OTP | Stops |
|-------|------|-----------|-------------|-------|
| G2 - West Busway | BUS | 88.4% | 81.7% | 24 |
| 18 - Manchester | BUS | 87.5% | 88.4% | 43 |
| P1 - East Busway-All Stops | BUS | 83.9% | 84.5% | 24 |
| 39 - Brookline | BUS | 82.6% | 78.9% | 69 |
| 43 - Bailey | BUS | 81.8% | 79.5% | 65 |

## Bottom 5 Routes (by trailing 12-month OTP)

| Route | Mode | Recent OTP | All-Time OTP | Stops |
|-------|------|-----------|-------------|-------|
| 71B - Highland Park | BUS | 41.9% | 58.8% | 107 |
| 61C - McKeesport-Homestead | BUS | 44.8% | 56.8% | 158 |
| 65 - Squirrel Hill | BUS | 46.5% | 61.5% | 70 |
| 58 - Greenfield | BUS | 49.8% | 60.8% | 102 |
| 61B - Braddock-Swissvale | BUS | 50.1% | 58.4% | 137 |

## Post-COVID Trends (2022 onward)

**Most improving** (steepest positive slope):
- P78 - Oakmont Flyer: +6.6 pp/year
- 71D - Hamilton: +4.1 pp/year
- O1 - Ross Flyer: +3.4 pp/year

**Most declining** (steepest negative slope):
- SWL - Outbound to SHJ: -10.5 pp/year
- 65 - Squirrel Hill: -8.3 pp/year
- 71B - Highland Park: -7.2 pp/year

## Observations

- Using trailing 12-month OTP shifts the rankings compared to all-time averages: G2 (West Busway) has improved markedly and now leads, while 71B (Highland Park) and 65 (Squirrel Hill) have deteriorated significantly.
- The post-COVID slope isolates recent trajectory without the structural break caused by the 2020 COVID ridership drop, which dominated full-period slopes.
- High-volatility routes (std > 2x median) include SWL, 15 (Charles), and 65 (Squirrel Hill), which have extreme month-to-month swings.
- 4 routes were excluded from ranking for having fewer than 12 months of data.

## Caveats

- Stop counts come from current data; historical stop counts may have differed.
- Post-COVID slope assumes a roughly linear trajectory from 2022 onward, which may not hold for all routes.
