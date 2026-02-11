# Findings: Transfer Hub Performance

## Summary

Higher-connectivity stops appear to have modestly worse OTP in stop-level data, but this finding **does not survive correction for non-independence**. At the route level (independent observations), the correlation between stop connectivity and OTP is not significant (r = -0.15, p = 0.16). The apparent "hub penalty" is a composition effect driven by inflated sample size at the stop level.

## Key Numbers

| Tier | Stops | Mean OTP | Median OTP |
|------|-------|----------|------------|
| Simple (1 route) | 3,875 | 69.5% | 69.2% |
| Medium (2-4 routes) | 2,138 | 66.0% | 65.0% |
| Hub (5+ routes) | 196 | 66.4% | 65.2% |

**Stop-level (n=6,209 -- non-independent, inflated power):**
- Pearson r = -0.17 (p < 0.001)
- Spearman rho = -0.32 (p < 0.001)

**Route-level (n=93 -- independent observations):**
- Pearson r = -0.15 (p = 0.16)

**Route-level, bus only (n=90):**
- Pearson r = -0.09 (p = 0.39)

## Observations

- The stop-level correlations (r = -0.17, rho = -0.32) are statistically significant but **misleading**: the 6,209 "stops" are not independent observations. Stops on the same route share the same underlying OTP, so the effective sample size is closer to ~90 (the number of distinct routes). With n_eff ~ 90, a correlation of r = -0.15 yields p = 0.16, which is not significant.
- The route-level analysis confirms this: average stop connectivity per route has no significant relationship with route OTP (r = -0.15, p = 0.16). Within bus routes only, the relationship is even weaker (r = -0.09, p = 0.39).
- The 3.5 pp tier gap (simple 69.5% vs hub 66.4%) is real in the raw data but reflects a **composition effect**: hubs are served by many routes including poor-performing local bus routes, which drag down the average. The hub location itself is not causing worse OTP.
- The busiest hub (East Busway Penn Station, 27 routes) actually outperforms the system average (72.1%) because it sits on dedicated right-of-way.

## Implication

Being a transfer hub does not independently predict worse OTP. The apparent hub penalty is driven by which routes converge there. Policy should focus on improving the poorly-performing routes themselves, not on the hub locations.

## Caveats

- This analysis uses route-level OTP projected onto stops (ecological fallacy). We don't have stop-level OTP data; a route's on-time performance may vary along its length.
- The route-level analysis uses "average stop connectivity per route," which is itself an approximation. A more direct test would require stop-level arrival data.
