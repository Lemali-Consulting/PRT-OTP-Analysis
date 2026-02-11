# Findings: Multivariate OTP Model

## Summary

A six-feature OLS model explains **47.2% of OTP variance** (adjusted R² = 0.435) across 92 routes. Three features are significant: stop count, geographic span, and rail mode. The model confirms that structural route characteristics explain nearly half of all performance variation, with the remaining 53% attributable to unmeasured factors (traffic, staffing, weather, schedule design).

## Key Numbers

- **R² = 0.472**, **Adjusted R² = 0.435**
- **n = 92 routes**, **k = 6 features**

| Feature | Coefficient | p-value | Beta Weight | Significant? |
|---------|------------|---------|-------------|-------------|
| stop_count | -0.0006 | <0.001 | -0.49 | *** |
| span_km | -0.0049 | <0.001 | -0.47 | *** |
| is_rail | +0.133 | <0.001 | +0.34 | *** |
| n_munis | +0.009 | 0.001 | +0.41 | ** |
| is_premium_bus | +0.007 | 0.70 | +0.05 | |
| weekend_ratio | -0.006 | 0.79 | -0.03 | |

## Observations

- **Stop count** (beta = -0.49) and **geographic span** (beta = -0.47) are the two strongest predictors, with nearly equal standardized effects. Each additional stop costs roughly -0.06 pp OTP; each additional km of span costs roughly -0.49 pp.
- **Rail mode** (beta = +0.34) provides a +13.3 pp OTP advantage over bus after controlling for structural factors. This is partly inherent to rail (dedicated right-of-way) and not fully captured by other features.
- **Number of municipalities** has a surprising positive coefficient (+0.009 per muni, beta = +0.41). This is likely a suppressor effect: after controlling for stop count and span, routes that serve more municipalities tend to be express/busway routes that skip stops, which perform better.
- **Premium bus** (busway/flyer/express/limited) is not significant once stop count and span are controlled -- these routes' advantage is fully explained by having fewer stops and shorter spans, not by their service type per se.
- **Weekend ratio** is not significant, confirming the null finding from Analysis 17.

## Model Interpretation

The 47% R² means that knowing just a route's stop count, length, and mode gets you almost halfway to predicting its OTP. The unexplained 53% likely reflects:
- Traffic conditions and road geometry
- Schedule design (running time padding, layover adequacy)
- Driver staffing and experience
- Passenger volume and dwell time variation
- Weather and construction effects

These factors would require operational data not present in this dataset.

## Caveats

- OLS assumes linear relationships and independent errors. Some non-linearity is visible in the residuals.
- The n_munis coefficient is a suppressor and should not be interpreted as "more municipalities = better OTP."
- With only 92 observations and 6 predictors, the model is at the edge of stable estimation.
