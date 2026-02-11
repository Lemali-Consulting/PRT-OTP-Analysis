# Findings: Route Geographic Span vs OTP

## Summary

Geographic span (the maximum distance between any two stops on a route) is a **moderate negative predictor** of OTP within bus routes (r = -0.38, p < 0.001), but stop count remains the stronger predictor after controlling for the other. Partial correlation analysis disentangles the two: stop count predicts OTP even after controlling for span (partial r = -0.41, p < 0.001), while span's independent contribution is smaller (partial r = -0.23, p = 0.03).

## Key Numbers

- **Span vs OTP (bus only, primary):** Pearson r = -0.38 (p < 0.001, n = 89), Spearman rho = -0.37 (p < 0.001)
- **Span vs OTP (all routes, secondary):** r = -0.32 (p = 0.002, n = 92) -- includes Simpson's paradox risk
- **Stop density vs OTP (bus only):** r = 0.04 (p = 0.71) -- not significant
- **Span vs OTP | stop count (bus, partial):** r = -0.23 (p = 0.03)
- **Stop count vs OTP | span (bus, partial):** r = -0.41 (p < 0.001)
- **Span-stop count collinearity:** r = 0.41

## Observations

- The bus-only correlation (r = -0.38) is actually *stronger* than the all-mode correlation (r = -0.32). The pooled-mode result was muted by Simpson's paradox -- rail routes have moderate span but high OTP, pulling the all-mode trend line toward zero.
- Span and stop count are moderately correlated (r = 0.41), but not so strongly as to make partial correlation unreliable.
- After controlling for stop count, span still has a small but significant independent effect -- longer routes face additional challenges beyond just having more stops (longer exposure to traffic, more variance in conditions).
- However, stop count's partial correlation (-0.41) is nearly twice span's (-0.23), confirming that the **number of stops matters more than the distance covered**.
- Stop density (stops per km) shows no correlation with OTP at all (r = 0.04), meaning that tightly-packed stops are no worse than widely-spaced stops once total count and distance are accounted for.

## Implication

Both stop count and route distance independently degrade OTP, but stop consolidation is the higher-leverage intervention. Shortening routes would help modestly, but eliminating stops on existing routes would have roughly twice the impact per unit of change.

## Caveats

- Geographic span (max pairwise distance) is a crude proxy for actual route length. GTFS shape data would provide a more accurate route-length measurement.
- Routes with fewer than 12 months of data are excluded to reduce noise.

## Review History

- 2026-02-10: [RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md](../../RED-TEAM-REPORTS/2026-02-10-analyses-12-18.md) — 4 issues (1 significant). Bus-only correlations now primary; Spearman added.
