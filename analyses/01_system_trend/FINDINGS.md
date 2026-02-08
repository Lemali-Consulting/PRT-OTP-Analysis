# Findings: System-Wide OTP Trend

## Summary

PRT on-time performance has **declined** over the 2019--2025 window and has not recovered to pre-COVID levels.

## Key Numbers

- **2019 baseline:** ~69% weighted OTP (93 routes reporting)
- **COVID spike:** 75% in March 2020 (low ridership improved adherence)
- **Post-COVID trough:** 58% in September 2022
- **Current level:** 61--63% weighted OTP (late 2025)

## Observations

- The unweighted average runs 2--3 percentage points above the weighted average, meaning high-frequency routes (carrying the most riders) tend to perform worse than low-frequency ones.
- Year-over-year change was consistently negative from mid-2021 through late 2022, then stabilized near zero -- the system stopped declining but hasn't improved.
- Route count has been stable at 93 throughout the period, so the decline isn't explained by adding harder-to-serve routes.

## Caveats

- Trip weights come from current `route_stops` data, not historical. If route frequency changed significantly over time, the weighting may not perfectly reflect past ridership.
- The OTP definition ("on-time") is not specified in the source data -- the threshold could be 1 minute, 5 minutes, or something else.
