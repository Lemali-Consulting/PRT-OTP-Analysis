# Methods: Stop Count vs OTP

## Question
Do routes with more stops have worse on-time performance? Each stop is another opportunity to fall behind schedule.

## Approach
- Count distinct stops per route from `route_stops`.
- Compute average OTP per route from `otp_monthly`, requiring at least 12 months of data (`HAVING COUNT(*) >= 12`) to exclude routes with sparse observations.
- Create a scatter plot of stop count vs average OTP, colored by mode.
- Compute Pearson and Spearman correlation coefficients, both for all routes and for bus-only (to check for Simpson's paradox from mixing modes).
- Fit a simple linear regression line (bus-only, via `scipy.stats.linregress`).
- **Leverage-robustness check:** recompute the bus-only Pearson correlation after dropping high-leverage routes -- those whose regression leverage `h = 1/n + (x - mean)^2 / Sxx` exceeds `3 * (2/n)`, the standard rule of thumb for a two-parameter fit. This confirms the correlation is not an artifact of the few extreme-stop-count routes.
- Annotate the two highest-stop-count routes (59 and 77) on the scatter so the influential points are visible to readers.

**Note:** Stop counts come from the current `route_stops` snapshot, while OTP is averaged across all historical months. Routes that changed stop configurations over time will have a mismatch between their current stop count and the OTP values from earlier periods.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `otp_monthly` | Monthly OTP per route | `prt.db` table |
| `route_stops` | Stop count per route | `prt.db` table |
| `routes` | Mode classification | `prt.db` table |

## Output
- `output/stop_count_otp.csv` -- per-route stop count and average OTP
- `output/stop_count_vs_otp.png` -- scatter plot with regression line
