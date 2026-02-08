# Findings: Anomaly Investigation

## Summary

842 anomalous months were flagged across 94 routes using a rolling z-score method with a **lagged window** (current month excluded from the baseline). Anomalies cluster in time (COVID, late 2022) rather than being randomly distributed, suggesting system-wide shocks.

## Methodology Note

The anomaly detector uses a 12-month rolling window shifted by one month, so the current observation is never included in its own baseline. This prevents self-dampening of z-scores and produces more sensitive detection (842 anomalies vs. 406 with the unshifted approach).

## Routes with Most Anomalies

| Route | Anomalies |
|-------|-----------|
| 79 - East Hills | 18 |
| 19L - Emsworth Limited | 16 |
| RED - Castle Shannon via Beechview | 15 |
| 54 - North Side-Oakland-South Side | 15 |
| 28X - Airport Flyer | 14 |

## Key Anomaly Clusters

- **March--June 2020 (COVID):** Many routes showed *positive* anomalies -- OTP improved because reduced ridership meant less dwell time and fewer delays. This was a temporary artifact, not genuine improvement.
- **Late 2022:** A cluster of negative anomalies across many routes, coinciding with the system-wide OTP trough (58% in September 2022). May indicate staffing shortages, construction, or service restructuring.
- **Route 79 (East Hills):** The most anomaly-prone route, with 18 flagged months, indicating persistent instability in schedule adherence.

## Observations

- The lagged window methodology results in more anomalies being flagged, particularly for routes with gradual trends, since the baseline is always slightly behind.
- Rail routes (RED, BLUE) have many anomalies despite high average OTP because their performance is normally very consistent, so even moderate dips trigger the 2-sigma threshold.
- The z-score method requires at least 6 months of rolling history, so the first few months of each route's data are not evaluated.

## Caveats

- Without external data (PRT service advisories, construction records, staffing reports), anomalies can only be flagged, not explained.
- The known events dictionary is limited to COVID dates. More events could be added with PRT service change records.
