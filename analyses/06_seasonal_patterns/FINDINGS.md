# Findings: Seasonal Patterns

## Summary

PRT shows a consistent seasonal cycle with **winter months outperforming summer/fall**. The system-wide seasonal swing is about 7 percentage points. Most individual routes have modest seasonal amplitude (under 15%).

## System-Wide Seasonal Profile

| Month | Weighted OTP | Deviation |
|-------|-------------|-----------|
| January | 70.3% | Best |
| February | 68.0% | |
| March | 69.2% | |
| April | 66.3% | |
| May | 64.6% | |
| June | 64.3% | |
| July | 66.8% | |
| August | 65.4% | |
| September | 63.7% | Worst |
| October | 64.5% | |
| November | 65.0% | |
| December | 66.6% | |

## Observations

- The winter advantage is somewhat counterintuitive -- one might expect snow and ice to worsen OTP. Possible explanations: lower ridership reduces dwell time; fewer construction detours; school breaks reduce congestion.
- September and October are consistently the worst months, possibly due to the return of school-year traffic and late-summer construction.
- The route with the largest seasonal amplitude is SWL (69%), but this is an outlier driven by only 13 months of data. The next-highest amplitudes (Route 15 at 14.4%, P2 at 14.1%) are more representative.
- The heatmap of the top 20 most-seasonal routes shows no single month dominates as "worst" across all routes -- the pattern varies by route, though fall months are generally weaker.

## Caveats

- Seasonal decomposition uses a simple moving-average method, not a formal STL decomposition. Results are directionally correct but not statistically rigorous.
- Only 6--7 years of data means each month-of-year average is based on 6--7 observations, limiting statistical power.
