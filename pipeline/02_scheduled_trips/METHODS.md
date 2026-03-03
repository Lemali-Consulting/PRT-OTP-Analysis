# Methods: Scheduled Trips ETL

## Question
How do we add monthly service-level schedule data needed for longitudinal service and causality analyses?

## Approach
1. Fetch or read cached WPRDC schedule exports.
2. Normalize route IDs, month keys, day type, and schedule period fields.
3. Deduplicate overlapping schedule periods per route/month/day type.
4. Rebuild `scheduled_trips_monthly` and `schedule_periods` in `prt.db`.

## Data
- WPRDC monthly schedule aggregates (`schedule_monthly_agg.csv`)
- WPRDC pick lookup (`paac_pick_lookup.csv`)
- Route IDs from `routes` table in `prt.db`

## Output
- `scheduled_trips_monthly` table in `data/prt.db`
- `schedule_periods` table in `data/prt.db`
