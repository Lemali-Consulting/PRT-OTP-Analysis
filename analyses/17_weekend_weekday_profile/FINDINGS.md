# Findings: Weekend vs Weekday Service Profile

## Summary

There is **no meaningful correlation** between a route's weekend-to-weekday service ratio and its OTP. Routes that run heavy weekend service perform identically to commuter-oriented weekday-heavy routes.

## Key Numbers

- **Pearson r = -0.03** (p = 0.79, n = 93)
- **Spearman rho = -0.02** (p = 0.84)

| Service Tier | Routes | Mean OTP |
|-------------|--------|----------|
| Weekday-heavy (<0.3) | 27 | 69.8% |
| Balanced (0.3-0.7) | 45 | 68.8% |
| Weekend-heavy (>0.7) | 21 | 70.3% |

## Observations

- The three service tiers are virtually indistinguishable in OTP (69.8%, 68.8%, 70.3%).
- Neither Pearson nor Spearman correlations approach significance.
- This null result makes sense: the weekend service ratio reflects demand patterns and scheduling choices, not route structure. A route with high weekend service isn't inherently harder to run on time.
- Since OTP is reported monthly (not by day-of-week), it aggregates weekday and weekend performance, which may mask day-specific patterns.

## Implication

Weekend vs weekday service intensity is not a useful predictor of OTP. The structural factors identified in other analyses (stop count, mode, route length) dominate.
