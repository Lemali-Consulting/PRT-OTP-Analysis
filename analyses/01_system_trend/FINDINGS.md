# Findings: System-Wide OTP Trend

## Summary

PRT on-time performance has **declined** over the 2019--2025 window and has not recovered to pre-COVID levels. A bus-only stratification confirms the decline is not an artifact of mixing modes -- bus trends closely track the all-mode average.

## Key Numbers

- **2019 baseline:** ~69% all-mode weighted OTP, ~67% bus-only weighted OTP (93 routes reporting)
- **COVID spike:** 75% all-mode / 74% bus-only in March 2020 (low ridership improved adherence)
- **Post-COVID trough:** 58% all-mode / 57% bus-only in September 2022
- **Current level:** 61--63% all-mode / 62--64% bus-only weighted OTP (late 2025)

## Observations

- The unweighted average runs 2--3 percentage points above the weighted average, meaning high-frequency routes (carrying the most riders) tend to perform worse than low-frequency ones.
- The bus-only trend closely tracks the all-mode trend (gap averages ~0.5 pp), because bus routes (90+ of ~93 reporting) overwhelmingly dominate the system average. Rail's higher OTP (~84%) lifts the all-mode average only slightly.
- Year-over-year change was consistently negative from mid-2021 through late 2022, then stabilized near zero -- the system stopped declining but hasn't improved.
- Route count ranges from 68 to 96 across months. Most months have 93--96 routes, but Nov 2020 is a low outlier at 68 and mid-2025 months (June--July) drop to 77--79. This varying composition does not affect the per-month averaging directly (each month averages whichever routes reported), but it means the set of routes being averaged is not fixed across time.

## Caveats

- Trip weights come from current `route_stops` data, not historical. If route frequency changed significantly over time, the weighting may not perfectly reflect past ridership.
- The OTP definition ("on-time") is not specified in the source data -- the threshold could be 1 minute, 5 minutes, or something else.
- Five routes (37, 42, P2, RLSH, SWL) are excluded from the weighted average because they have no entries in `route_stops`, causing their `trips_7d` to default to 0 via COALESCE. These routes still contribute to the unweighted average. P2 (East Busway Short) has 57 months of data with ~84% OTP, so its exclusion from the weighted average is notable but does not substantially change the system trend.

## Review History
- 2026-02-11: [RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md](../../RED-TEAM-REPORTS/2026-02-11-analyses-01-05-07-11.md) -- 5 issues (1 significant). Added bus-only trend line, fixed METHODS.md data section, documented route count variability (68--96), corrected "stable at 93" claim, and documented excluded routes.
