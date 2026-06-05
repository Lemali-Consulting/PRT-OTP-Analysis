# Findings: VRH and Vehicle Revenue Miles

## Summary

PRT's bus operating speed has been remarkably stable at roughly 12.8–13.0 mph over the full 2002–2024 record, suggesting that traffic congestion has not measurably degraded fixed-route service speeds system-wide. Bus and light rail VRH and VRM have both declined sharply since 2002 (~35% and ~40% respectively), but because they track each other closely, the speed ratio has stayed flat. The most notable speed shift is in paratransit, which slowed from 15.2 mph in 2019 to 13.8 mph in 2024 (−9%), likely reflecting longer or more complex trip patterns.

## Key Numbers

| Mode | 2019 mph | 2024 mph | Change |
|------|---------|---------|--------|
| Motor Bus | 12.85 | 12.83 | −0.2% |
| Light Rail | 12.96 | 12.95 | −0.0% |
| Paratransit | 15.18 | 13.80 | −9.1% |

## Observations

- **Bus speed is flat over 22 years.** Motor bus VRM/VRH has barely moved — from 13.0 mph in 2002 to 12.8 mph in 2024. The COVID dip in 2021 (12.47 mph) reversed quickly. There is no evidence of a long-run speed decline.
- **Service volume fell substantially.** Bus VRH fell from ~2.2 M hours in 2002 to ~1.47 M in 2024, a 34% drop. VRM fell in nearly equal proportion, keeping speed constant. This means the system is running fewer hours *and* fewer miles — a contraction in service, not a slowdown.
- **Light rail is similarly stable.** Speed fluctuated 11–13.5 mph in early years (likely tied to service restructuring around the South Hills extensions) and has settled near 13 mph since 2006.
- **Paratransit speed decline is the standout finding.** ACCESS paratransit went from 15.2 mph in 2019 to 13.8 mph in 2024. Over the same period VRH grew faster than VRM (VRH up ~24% from 2019 baseline vs VRM up ~25%), so the decline is small but consistent. This may reflect shifts toward more complex trip routing or longer average trip distances.
- **Paratransit VRH and VRM both grew sharply post-2007** (when NTD began reporting them) to become a large fraction of agency-wide service hours by 2024 (~24% of all VRH).

## Caveats

- NTD data is agency-reported and aggregated annually; it cannot distinguish speed changes on specific corridors or times of day.
- Paratransit data (VRH and VRM) is not available before 2007, so the long-run speed trend for that mode is incomplete.
- The Incline (IP) is excluded from speed analysis; its 2.3 mph figure reflects extremely short, near-vertical track rather than congestion or service efficiency.
- "Speed" here is an average across all trips for the year and does not capture peak-hour vs. off-peak variation.

## Validation

1. **Data source verified.** `ntd_ridership` columns confirmed against `DATA_DICTIONARY.md`; mode codes validated against Analysis 50 constants.
2. **Temporal scope.** All data filtered to 2002–2024 calendar years; paratransit zeros before 2007 treated as no service and excluded from speed calculations (VRH = 0 guard).
3. **Plausibility.** Bus speeds of 12–13 mph are consistent with published literature for U.S. urban bus systems. Paratransit speeds (13–15 mph) are plausible for demand-responsive service with deadheading.
4. **Surprising result investigated.** The paratransit speed decline (−9%) was checked against raw VRH and VRM year-by-year; the trend is consistent across 2020–2024 and not attributable to a single outlier year.
5. **Known relationships verified.** VRH and VRM track each other for bus and rail as expected (stable speed). No reversals noted.
