# Findings: Incline Investigation

## Summary

The Monongahela Incline is a **data pipeline artifact**. It appears in the route catalog but has zero OTP measurements. OTP was never recorded for either of Pittsburgh's two inclines.

## What the Data Shows

| Table | MI Records | Details |
|-------|-----------|---------|
| `routes` | 1 row | route_id=MI, mode=INCLINE |
| `otp_monthly` | **0 rows** | No OTP data whatsoever |
| `route_stops` | 2 rows | Upper Station, Lower Station (78 weekday trips, 549 weekly) |
| `stops` | 2 Incline stops | W15307 (Upper, Mount Washington), W15308 (Lower, South Shore) |
| `stop_reference` | 4 Incline stops | Both inclines present historically (first_served=1503, last_served=2510) |

## Observations

- Both the Monongahela Incline (MI) and the Duquesne Incline (DQI) exist in the `routes` table with mode=INCLINE, but neither has any OTP data.
- The inclines are physically operational and appear in PRT's GTFS feed with regular service (78 weekday trips).
- The OTP measurement system (whatever generates `routes_by_month.csv`) simply does not cover incline routes. This is likely because inclines run on a fixed schedule with no traffic interference, making OTP measurement less meaningful.
- The ANALYSIS-PROPOSAL.md described this as "zero values" -- in fact, there are no values at all, not even zeros.

## Conclusion

This is not a data quality issue to fix. The inclines were included in the route catalog because they're part of PRT's GTFS feed, but were excluded from OTP measurement, likely by design. No further action needed.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) — 3 issues (0 significant). Expanded OTP query to explicitly check both MI and DQI (substantiating the claim that neither incline has data), updated METHODS.md question wording.
