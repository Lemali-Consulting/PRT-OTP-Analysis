# Methods: Service Change Impact on OTP

## Question
Do schedule changes (transitions between pick periods) correlate with OTP shifts? When PRT restructures service for a route, does OTP improve, decline, or stay the same?

## Approach
- Identify schedule change events: months where a route's `pick_id` changes from the prior month in `scheduled_trips_monthly`.
- For each change event, compute the OTP delta: mean OTP in the 3 months after the change minus mean OTP in the 3 months before.
- Also compute the trip count delta (daily_trips after minus before) to distinguish service increases from cuts.
- Classify events by direction: service increase (more trips), service cut (fewer trips), or neutral (same trips, different schedule).
- Test whether OTP deltas differ from zero (one-sample t-test) and whether they differ by event type (Kruskal-Wallis).
- Examine the COVID period (Mar--Apr 2020) separately, since it represents the largest service change in the dataset.
- Scatter plot: trip count change vs OTP change at each event, colored by pre/post COVID.

## Data
- `scheduled_trips_monthly` -- route-level monthly trip counts and pick_id (WEEKDAY day type)
- `otp_monthly` -- monthly OTP per route
- `schedule_periods` -- pick period start/end dates for context

## Output
- `output/service_change_events.csv` -- all detected schedule change events with OTP and trip deltas
- `output/service_change_impact.png` -- scatter plot of trip change vs OTP change
- `output/service_change_summary.csv` -- summary statistics by event type
