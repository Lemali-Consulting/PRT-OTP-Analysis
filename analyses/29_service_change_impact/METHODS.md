# Methods: Service Change Impact on OTP

## Question
Do schedule changes (transitions between pick periods) correlate with OTP shifts? When PRT restructures service for a route, does OTP improve, decline, or stay the same?

## Approach
- Identify schedule change events: months where a route's `pick_id` changes from the prior month in `scheduled_trips_monthly`.
- For each change event, compute the OTP delta: mean OTP in the 3 months after the change minus mean OTP in the 3 months before.
- Also compute the trip count delta (daily_trips after minus before) to distinguish service increases from cuts.
- Classify events by direction: service increase (more trips), service cut (fewer trips), or neutral (same trips, different schedule).
- Only detect change events between consecutive months (no gaps) to avoid spurious multi-month deltas.
- Test whether OTP deltas differ from zero using both a naive one-sample t-test and a route-clustered t-test (average within route first, then test route means) to account for non-independence of events within routes. Test event-type differences with Kruskal-Wallis.
- Examine the COVID period (Mar--Apr 2020) separately, since it represents the largest service change in the dataset.
- Scatter plot: trip count change vs OTP change at each event, colored by pre/post COVID.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `scheduled_trips_monthly` | Route-level monthly trip counts and pick_id (WEEKDAY day type) | `prt.db` table |
| `otp_monthly` | Monthly OTP per route | `prt.db` table |
| `schedule_periods` | Pick period start/end dates for context | `prt.db` table |

## Output
- `output/service_change_events.csv` -- all detected schedule change events with OTP and trip deltas
- `output/service_change_impact.png` -- scatter plot of trip change vs OTP change
- `output/service_change_summary.csv` -- summary statistics by event type
