# Findings: Cross-Route Correlation Clustering

## Summary

After **detrending** (subtracting system-wide monthly mean OTP), hierarchical clustering on pairwise OTP correlations produced **6 clusters** (selected by silhouette score optimization). Detrending removes the dominant COVID/seasonal signal that otherwise causes all routes to appear positively correlated, revealing genuine differential behavior.

## Key Numbers

| Cluster | Routes | Avg OTP | Avg Stops | Character |
|---------|--------|---------|-----------|-----------|
| 1 | 23 | 66.8% | 118 | Lowest-performing cluster, high stop count |
| 2 | 9 | 74.0% | 114 | Best-performing cluster |
| 3 | 27 | 71.8% | 105 | Largest cluster, above-average performance |
| 4 | 11 | 69.4% | 106 | Mid-performing |
| 5 | 13 | 67.5% | 108 | Below-average |
| 6 | 10 | 68.9% | 146 | Highest stop count |

- Silhouette scores ranged from 0.13 to 0.18 (k=6 was optimal at 0.178)
- 0 route pairs excluded for insufficient overlap

## Methodology

- **Detrending**: System-wide monthly mean OTP is subtracted from each route's OTP before computing correlations. This ensures clusters reflect differential route behavior rather than common system-wide trends (COVID, seasonal cycles).
- **Linkage**: Average linkage (valid for non-Euclidean correlation distance), replacing the original Ward's method.
- **Cluster count**: Selected by silhouette score optimization over k=3..10, replacing the hardcoded k=6.
- **Imputation**: Route pairs with insufficient overlap are imputed with median correlation rather than 0.0.

## Observations

- With detrending, the clusters are more evenly sized and differentiated by OTP level.
- The highest stop-count cluster (Cluster 6, 146 avg stops) does not have the worst OTP (68.9%), suggesting that after removing system-wide trends, route complexity alone doesn't determine co-movement.
- Low silhouette scores (0.13-0.18) indicate moderate cluster separation -- routes don't form tightly distinct groups. This is expected given that detrended OTP residuals have limited signal.
- Without depot or corridor data, the clusters remain descriptive -- we can see which routes move together but cannot explain *why*.

## Caveats

- Silhouette scores below 0.25 indicate weak cluster structure. The 6-cluster solution is the best available, but route co-movement may be more continuous than discrete.
- All modes are pooled. With only ~3 rail routes, stratification by mode is not feasible.

## Review History

- 2026-02-10: [RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md](../../RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md) — 5 issues (2 significant). Detrended correlations, average linkage, silhouette-based k selection; cluster composition changed entirely.
