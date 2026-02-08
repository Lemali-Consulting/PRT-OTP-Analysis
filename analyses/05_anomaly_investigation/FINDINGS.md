# Findings: Anomaly Investigation

## Summary

406 anomalous months were flagged across 94 routes using a rolling z-score method. Anomalies cluster in time (COVID, late 2022) rather than being randomly distributed, suggesting system-wide shocks.

## Routes with Most Anomalies

| Route | Anomalies |
|-------|-----------|
| RED - Castle Shannon via Beechview | 10 |
| BLUE - SouthHills Village | 9 |
| 40 - Mount Washington | 8 |
| 61D - Murray | 8 |
| 61B - Braddock-Swissvale | 8 |

## Key Anomaly Clusters

- **March--June 2020 (COVID):** Many routes showed *positive* anomalies -- OTP improved because reduced ridership meant less dwell time and fewer delays. This was a temporary artifact, not genuine improvement.
- **Late 2022:** A cluster of negative anomalies across many routes, coinciding with the system-wide OTP trough (58% in September 2022). May indicate staffing shortages, construction, or service restructuring.
- **Route 15 (Charles):** Drops to ~35% OTP in July--September 2022, then rebounds to ~80%. Likely a route restructuring or detour, not a gradual decline.
- **Route 65 (Squirrel Hill):** Drops to 28--37% in mid-2023, well below its historical ~65% baseline.

## Observations

- Rail routes (RED, BLUE) have the most anomalies despite having high average OTP. This is because their OTP is normally very consistent, so even moderate dips trigger the 2-sigma threshold.
- The z-score method requires at least 6 months of rolling history, so the first few months of each route's data are not evaluated.

## Caveats

- Without external data (PRT service advisories, construction records, staffing reports), anomalies can only be flagged, not explained.
- The known events dictionary is limited to COVID dates. More events could be added with PRT service change records.
