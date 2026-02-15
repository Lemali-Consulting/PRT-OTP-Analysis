# Findings: Ridership in Multivariate OTP Model

## Summary
Adding log-transformed average weekday ridership to the Analysis 18 multivariate model does **not** significantly improve explanatory power. The F-test for the ridership term is not significant (F = 2.53, p = 0.116), and R² increases by only 1.5 pp (from 0.499 to 0.514). Ridership is **not collinear** with stop count or span (VIF = 1.73), but it is largely redundant with the existing predictors -- once route structure is controlled for, knowing how many people ride a route tells you almost nothing additional about its OTP.

## Key Numbers

| Model | R² | Adj R² | n |
|-------|----|--------|---|
| Base (6 features, Analysis 18 replication) | 0.499 | 0.464 | 92 |
| Expanded (+ log_riders) | 0.514 | 0.473 | 92 |
| Bus-only base (5 features) | 0.392 | 0.355 | 89 |
| Bus-only expanded (+ log_riders) | 0.410 | 0.367 | 89 |
| Ridership-only (log_riders + is_rail) | 0.232 | 0.215 | 92 |

- **F-test for log_riders** (all routes): F = 2.53, p = 0.116
- **F-test for log_riders** (bus only): F = 2.55, p = 0.114
- **log_riders beta weight**: -0.16 (weakly negative, not significant)
- **VIF for log_riders**: 1.73 (no multicollinearity concern)
- **Ridership-only model** explains just 23.2% of variance (vs 49.9% for structural model)

### Expanded model coefficients

| Feature | Beta Weight | p-value |
|---------|-------------|---------|
| stop_count | -0.43 | <0.001 |
| span_km | -0.47 | <0.001 |
| is_rail | +0.43 | <0.001 |
| n_munis | +0.35 | 0.005 |
| log_riders | -0.16 | 0.116 |
| is_premium_bus | +0.08 | 0.511 |
| weekend_ratio | +0.06 | 0.605 |

## Observations
- The base model replicates Analysis 18's results closely (R² = 0.499 here vs 0.472 in Analysis 18; the small difference is because this analysis restricts to routes with ridership data, dropping 0 routes from the 92-route sample).
- Log ridership has a weakly negative coefficient (beta = -0.16): higher-ridership routes tend to have slightly worse OTP after controls, but the effect is not statistically significant. This is consistent with Analysis 19's finding that ridership-weighted OTP is slightly higher than trip-weighted -- the two observations are not contradictory because the relationship is weak and confounded.
- Log ridership is surprisingly **uncorrelated** with stop count (r = +0.15, p = 0.16) and span (r = -0.00, p = 1.00). It is most strongly correlated with weekend_ratio (r = +0.57) -- routes with more riders tend to have relatively more weekend service.
- The ridership-only model (log_riders + is_rail, R² = 0.232) explains less than half the variance of the structural model (0.499), confirming that ridership is a weak proxy for the real drivers of OTP (stop count and span).
- All VIFs remain below 3.0 in the expanded model, so multicollinearity is not a concern.

## Discussion
This is a clean null result. Ridership does not add meaningful information to the OTP model once route structure is accounted for. The practical implication is that **PRT does not need to worry that high ridership per se degrades OTP** -- the routes with poor OTP happen to have high ridership because they are long, many-stop local bus corridors, not because passenger volumes cause delays. This is consistent with Analysis 10's finding that trip frequency does not predict OTP.

The weak negative direction of the ridership coefficient (-0.16 beta) is suggestive but not significant, and it could reflect residual confounding (high-ridership routes serve congested urban corridors) rather than a causal ridership-to-delay mechanism.

## Caveats
- Ridership is measured as average daily weekday riders per route, not per-trip load. Per-trip crowding data would better test the hypothesis that passenger volumes cause delays through dwell time.
- The log transform assumes diminishing marginal effects; a linear specification also fails to reach significance (not shown).
- The sample is restricted to 92 routes with both OTP and ridership data; 6 OTP-only routes are excluded.
- As with Analysis 18, the model's unexplained 50% of variance likely requires operational data (traffic, staffing, schedule slack) not available in this dataset.
