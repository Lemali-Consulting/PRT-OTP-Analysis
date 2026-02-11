# Findings: Seasonal Patterns

## Summary

PRT shows a consistent seasonal cycle with **winter months outperforming summer/fall**. The system-wide seasonal swing is about 6.8 percentage points after detrending. 93 routes had sufficient data (3+ years) for route-level seasonal analysis.

## System-Wide Seasonal Profile

Computed from a balanced panel of 93 routes (present in all 12 months-of-year) over complete calendar years (2019--2024).

| Month | Weighted OTP | Deviation from Trend |
|-------|-------------|---------------------|
| January | 70.8% | +2.8 pp (Best) |
| February | 68.9% | +1.0 pp |
| March | 69.9% | +2.1 pp |
| April | 68.1% | +0.3 pp |
| May | 67.4% | -0.4 pp |
| June | 66.7% | -1.1 pp |
| July | 68.1% | -0.2 pp |
| August | 67.2% | -1.1 pp |
| September | 64.4% | -3.9 pp (Worst) |
| October | 66.9% | -1.3 pp |
| November | 68.4% | +0.2 pp |
| December | 69.6% | +1.4 pp |

## Methodology Note

Seasonal profiles are computed by first removing a 12-month centered rolling mean (trend), then averaging the detrended residuals by month-of-year. This ensures that long-term trends (e.g., the COVID dip) do not distort the seasonal pattern. Route-level analysis requires at least 3 years of data to ensure each month-of-year is represented multiple times.

**Red-team corrections applied (2026-02-10):**
- Restricted to complete calendar years (2019-01 through 2024-12) to ensure every month-of-year has equal year coverage. Previously, December was missing 2025 data (the worst-performing year), inflating its seasonal average.
- Used a balanced panel of routes present in all 12 months-of-year for the system-wide profile. This excluded 5 routes: 3 winter-only routes with very high OTP (37 Castle Shannon 81%, 42 Potomac 83%, RLSH Red Line Shuttle 98%) and 2 with other gaps (53 Homestead Park, SWL). Their inclusion previously inflated winter averages.
- Note: `trips_7d` weighting is a static snapshot and may not reflect historical service levels. The seasonal pattern holds in both weighted and unweighted averages, so the core finding is robust to weighting choice.

## Most Seasonally Affected Routes (detrended)

| Route | Seasonal Amplitude |
|-------|-------------------|
| 15 - Charles | 15.8% |
| O5 - Thompson Run Flyer via 279 | 15.2% |
| P2 - East Busway Short | 14.8% |

## Observations

- The winter advantage is somewhat counterintuitive -- one might expect snow and ice to worsen OTP. Possible explanations: lower ridership reduces dwell time; fewer construction detours; school breaks reduce congestion.
- September is consistently the worst month (-3.9 pp from trend), possibly due to the return of school-year traffic and late-summer construction.
- After applying the balanced panel filter and complete-years restriction, the seasonal pattern persists with minimal change in magnitude, confirming it is a genuine operational pattern rather than a data artifact.
- Most routes have a seasonal amplitude under 15%. The heatmap of the top 20 routes shows no single month dominates as "worst" across all routes -- the pattern varies, though fall months are generally weaker.

## Caveats

- Seasonal decomposition uses a centered moving-average method to remove trend, not a formal STL decomposition. Results are directionally correct but assume additive seasonality.
- Only 6 years of complete data (2019--2024) means each month-of-year average is based on ~6 detrended observations, limiting statistical power.
- The `trips_7d` weighting reflects a single point-in-time snapshot of service frequency, not historical values. Route frequencies likely changed over the study period (especially during COVID).
