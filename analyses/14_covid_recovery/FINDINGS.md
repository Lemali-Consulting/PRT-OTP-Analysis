# Findings: COVID Recovery Trajectories

## Summary

The system-wide OTP decline since COVID is **unevenly distributed**. Of 92 routes with data in both periods, 43 improved and 49 declined, with a median delta of -0.9 pp and a mean delta of -2.1 pp. However, a **significant regression-to-the-mean effect** (r = -0.25, p = 0.02) means that much of the apparent divergence between "improved" and "declined" routes is a statistical artifact: routes with extreme baselines naturally regress toward the mean.

## Key Numbers

- **92 routes** with data in both pre-COVID (2019-01 to 2020-02) and current (2024-12 to 2025-11) periods
- **43 improved**, **49 declined**
- Median recovery delta: **-0.9 pp**
- Mean recovery delta: **-2.1 pp**
- Regression-to-the-mean: **r = -0.25** (p = 0.02) -- routes with high baselines tended to decline; routes with low baselines tended to improve
- Kruskal-Wallis test across subtypes: **H = 5.5, p = 0.24** -- no significant difference between route types
- Stop count vs recovery (bus): r = -0.11, p = 0.32 -- not significant

## Most Improved / Most Declined

**Most improved:**

| Route | Baseline | Current | Delta |
|-------|----------|---------|-------|
| P7 - McKeesport Flyer | 58.7% | 75.8% | +17.1 pp |
| G2 - West Busway | 75.4% | 88.4% | +13.0 pp |
| 21 - Coraopolis | 67.8% | 80.2% | +12.4 pp |

**Most declined:**

| Route | Baseline | Current | Delta |
|-------|----------|---------|-------|
| 71B - Highland Park | 63.0% | 41.9% | -21.1 pp |
| 58 - Greenfield | 70.4% | 49.8% | -20.6 pp |
| 65 - Squirrel Hill | 65.5% | 46.5% | -19.0 pp |

## Observations

- The **regression-to-the-mean test is significant** (r = -0.25, p = 0.02): routes that started with below-average OTP tended to improve, and routes that started above-average tended to decline. This does not mean the recovery differences are entirely artifactual, but it means the extreme cases (P7 improving +17 pp from a 58.7% baseline, or Route 6 declining -17.8 pp from an 80.5% baseline) are partially explained by statistical regression rather than operational changes.
- The **Kruskal-Wallis test across subtypes is not significant** (p = 0.24), meaning there is no statistically defensible evidence that premium routes recovered better than local routes *as a group*. The observation that the top improvers are flyers/busway routes may reflect cherry-picking the extremes rather than a systematic pattern.
- That said, the most-declined routes are genuinely concentrated in Pittsburgh's eastern neighborhoods (Highland Park, Greenfield, Squirrel Hill), and these declines are large enough to be concerning regardless of the RTM effect.

## Implication

The recovery picture is more nuanced than "premium routes improved, local routes declined." RTM explains a substantial fraction of the divergence. The policy-relevant finding is narrower: specific local bus routes in the eastern corridor have deteriorated badly (15-21 pp below pre-COVID levels), and this decline exceeds what RTM alone would predict.

## Caveats

- Regression to the mean is not the only explanation. Operational changes (schedule modifications, staffing shifts) may have genuinely affected some routes more than others.
- The current period is the trailing 12 months of available data (2024-12 to 2025-11), which may not represent a stable equilibrium.
- The pre-COVID baseline (2019-01 to 2020-02) includes months of varying performance; a longer baseline would be more stable.
