# Findings: Mode Comparison

## Summary

Light rail consistently outperforms bus by a wide margin, and the difference is **statistically significant** (Mann-Whitney U = 6,563, p < 0.001). Among bus routes, dedicated right-of-way (busway) routes perform nearly as well as rail, and limited-stop variants beat their local counterparts.

## Key Numbers

| Mode / Type | Avg OTP (unweighted) | Avg OTP (trip-weighted) | Route Count |
|-------------|---------------------|------------------------|-------------|
| RAIL | 84% | 84% | 3 |
| Busway (P1, P3, G2) | 71--76% | -- | 3 |
| Flyer (P/G/O prefix) | ~70% | -- | ~16 |
| Limited (L suffix) | ~72% | -- | varies |
| Express (X suffix) | ~70% | -- | varies |
| Local bus | 63--69% | -- | ~60 |

### Statistical Tests

- **Mann-Whitney U test (RAIL vs BUS monthly OTP):** U = 6,563, p < 0.001 (n = 83 months each). Rail median monthly OTP = 86.1%, bus median = 69.2%. The difference is highly significant.
- **Paired route comparison (2 pairs: 51/51L, 53/53L):** Limited variants average **+3.5 percentage points** over their local counterparts (paired t-test: t = 7.37, p < 0.001, 95% CI: [+2.5, +4.4 pp], n = 85 paired monthly observations across 2 pairs). While the test is significant, the sample of only 2 route pairs limits the generalizability of this finding.
- **Trip-weighted mode average:** Bus trip-weighted OTP (66.8%) is about 2 pp below the unweighted average (68.9%), confirming that high-frequency bus routes tend to perform worse. Rail is nearly the same weighted (83.8%) vs unweighted (84.1%).

## Observations

- Busway routes (P1, P3, G2) perform nearly as well as rail, consistent with the dedicated-right-of-way hypothesis.
- The previous classification grouped all P/G-prefix routes as "busway," which incorrectly included flyer routes like P17 (Lincoln Park Flyer), P78 (Oakmont Flyer), G3 (Moon Flyer), and G31 (Bridgeville Flyer). The corrected classification identifies only P1, P2, P3, and G2 as true busway routes.
- Only 2 local/limited pairs were found in the data (routes with matching base IDs). More pairs would strengthen the comparison.
- The RAIL--BUS gap has been roughly stable over time -- both modes declined in parallel, suggesting system-wide factors rather than mode-specific ones.
- The INCLINE mode has no OTP data and was excluded.

## Caveats

- Five UNKNOWN-mode routes (37, 42, P2, RLSH, SWL) were excluded from the analysis. P2 (East Busway Short) is plausibly a BUS/busway route, but its mode is listed as UNKNOWN in the database and it also lacks `route_stops` data.
- Bus route classification uses route ID naming conventions. True busway routes are identified as P1, P2, P3, G2; all other P/G/O-prefix routes are classified as flyers. Some routes may still be misclassified if their ID doesn't follow the standard pattern.
- Rail has only 3 routes (RED, BLUE, SLVR), so its average is sensitive to any single route's performance. The Mann-Whitney test has adequate statistical power due to 83 months of observations, but the underlying data comes from only 3 routes.
- The mode-level unweighted average treats each route equally regardless of trip volume. The trip-weighted version provides a ridership-adjusted perspective.
- Route composition varies across months (68--96 routes reporting). No balanced-panel filter is applied, so the set of routes contributing to each month's average is not fixed.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) -- 6 issues (1 significant). Replaced "significantly outperforms" with formal Mann-Whitney U test, added paired t-test with 95% CI, excluded UNKNOWN-mode routes, fixed classify_bus_route to correctly distinguish busway from flyer routes, added trip-weighted mode comparison, and documented composition variability.
