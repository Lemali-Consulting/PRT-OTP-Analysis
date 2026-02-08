# Findings: Seasonal Patterns

## Summary

PRT shows a consistent seasonal cycle with **winter months outperforming summer/fall**. The system-wide seasonal swing is about 6 percentage points after detrending. 93 routes had sufficient data (3+ years) for route-level seasonal analysis.

## System-Wide Seasonal Profile

| Month | Weighted OTP | Deviation from Trend |
|-------|-------------|---------------------|
| January | 70.3% | Best |
| February | 68.0% | |
| March | 69.2% | |
| April | 66.3% | |
| May | 64.6% | |
| June | 64.3% | |
| July | 66.8% | |
| August | 65.4% | |
| September | 64.0% | Worst |
| October | 64.5% | |
| November | 65.0% | |
| December | 66.6% | |

## Methodology Note

Seasonal profiles are computed by first removing a 12-month centered rolling mean (trend), then averaging the detrended residuals by month-of-year. This ensures that long-term trends (e.g., the COVID dip) do not distort the seasonal pattern. Route-level analysis requires at least 3 years of data to ensure each month-of-year is represented multiple times.

## Most Seasonally Affected Routes (detrended)

| Route | Seasonal Amplitude |
|-------|-------------------|
| O5 - Thompson Run Flyer via 279 | 15.4% |
| P2 - East Busway Short | 14.8% |
| 58 - Greenfield | 13.9% |

## Observations

- The winter advantage is somewhat counterintuitive -- one might expect snow and ice to worsen OTP. Possible explanations: lower ridership reduces dwell time; fewer construction detours; school breaks reduce congestion.
- September and October are consistently the worst months, possibly due to the return of school-year traffic and late-summer construction.
- After applying the minimum 3-year data requirement, the SWL outlier (which previously showed 69% amplitude on only 13 months of data) is excluded, producing a more reliable ranking.
- Most routes have a seasonal amplitude under 15%. The heatmap of the top 20 routes shows no single month dominates as "worst" across all routes -- the pattern varies, though fall months are generally weaker.

## Caveats

- Seasonal decomposition uses a centered moving-average method to remove trend, not a formal STL decomposition. Results are directionally correct but assume additive seasonality.
- Only 6--7 years of data means each month-of-year average is based on 6--7 detrended observations, limiting statistical power.
