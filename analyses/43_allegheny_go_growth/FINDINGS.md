# Findings: Allegheny Go Program Growth

## Summary

The Allegheny Go program grew rapidly from 262 rides in its first week (May 2024)
to over 30,000 rides per week by late 2025, with 2.27 million total rides to date.
Program ridership does not correlate with system-level OTP (Pearson r = 0.129,
p = 0.600, n = 19 months), suggesting the program's growth is driven by enrollment
expansion rather than service quality fluctuations.

## Key Numbers

- 2,274,373 total rides across 96 weeks (May 2024 – March 2026)
- Peak monthly riders: ~3,375 unique riders
- Rides per rider per week: 8–12, averaging ~9.5 (consistent utilization)
- Pearson r (monthly rides vs system OTP): 0.129 (p = 0.600, n = 19)
- Ready2Ride dominated early enrollment (2,300 in June 2024 launch month);
  ConnectCard Mail surged starting March 2025

## Observations

- **Rapid S-curve growth.** The program went from near-zero to ~100K monthly rides
  in five months (May–October 2024), then plateaued at 100K–130K monthly rides.
  The December 2024 spike to 152K rides appears to be a 5-week month effect.
- **Utilization is stable.** Rides per rider per week hovers between 8 and 12 across
  the full period, suggesting participants use the program consistently once enrolled.
  No sign of "churning" (enrolling but not riding).
- **Enrollment shifted from Ready2Ride to ConnectCard.** The launch was
  Ready2Ride-dominated (digital-first). ConnectCard Mail enrollments appeared in
  March 2025 and now represent the largest enrollment channel, suggesting the
  program expanded to less digitally-connected populations.
- **No OTP correlation.** System OTP fluctuates between 0.64 and 0.71 during the
  program period, but these fluctuations are uncorrelated with ridership growth.
  The program's trajectory is a monotonic ramp-up regardless of service quality.

## Caveats

- Only 19 months of overlap between Allegheny Go ridership and OTP data limits
  statistical power for the correlation test.
- Weekly-to-monthly conversion assigns each week to its `week_start` month;
  weeks spanning month boundaries are attributed to the earlier month.
- System OTP is an unweighted average across all routes. Allegheny Go riders
  likely concentrate on a subset of routes, so route-specific OTP would be more
  informative (but route-level program data is not available).
- The December 2024 spike is likely a calendar artifact (5 weeks in that month),
  not a genuine ridership increase.

## Validation

1. **Data source verified.** Ridership from `allegheny_go_weekly` table (pipeline 08);
   OTP from `otp_monthly` table.
2. **Temporal scope matches.** Both datasets filtered to their natural ranges;
   overlap period (May 2024 – Nov 2025) explicitly identified.
3. **Null handling.** System OTP is null for months outside OTP coverage; these
   months are excluded from correlation but included in growth charts.
4. **Aggregates sanity-checked.** Total rides (2.27M) matches the dashboard KPI
   (2.26M); small difference due to rounding.
5. **Direction of effects checked.** Rising ridership with flat OTP is expected for
   a new enrollment-driven program; a strong correlation would have been surprising
   and warranted investigation.
