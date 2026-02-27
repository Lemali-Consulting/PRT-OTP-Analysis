# Methods: Cross-Route Correlation Clustering

## Question
Which routes' OTP values move together over time? Identifying co-moving clusters could reveal shared causal factors -- same corridor, same depot, same traffic bottleneck, or common external shocks.

## Approach
- Build a route x month matrix of OTP values from `otp_monthly`.
- Filter to routes with at least 36 months of data to ensure meaningful correlations.
- Compute pairwise Pearson correlation between every pair of routes' monthly OTP series (using only overlapping months).
- Convert correlation to distance (1 - r) and apply Ward's hierarchical clustering via `scipy.cluster.hierarchy`.
- Cut the dendrogram to produce a manageable number of clusters (target ~5-8).
- Characterize each cluster by mode, average OTP, stop count, and geographic location.
- Visualize with a dendrogram and a clustered correlation heatmap.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | Monthly OTP per route (time series) | `prt.db` table |
| `routes` | Mode and name for labeling | `prt.db` table |
| `route_stops` | Stop count per route for cluster characterization | `prt.db` table |
| `stops` | Geography for cluster characterization | `prt.db` table |

**Notes:** `route_stops` is joined to `stops` to derive stop count and geographic location per route.

## Output
- `output/cluster_membership.csv` -- route-to-cluster assignment with cluster characteristics
- `output/dendrogram.png` -- hierarchical clustering dendrogram
- `output/correlation_heatmap.png` -- pairwise correlation matrix ordered by cluster
