# Methods: Ridership in Multivariate OTP Model

## Question
Does average ridership add explanatory power to the Analysis 18 OLS model (stop count, span, mode, n_munis, premium, weekend ratio) or is it collinear with existing predictors?

## Approach
- Replicate the Analysis 18 six-feature OLS model on routes with ridership data available.
- Add log-transformed average weekday ridership as a seventh predictor. Log transform is used because ridership is right-skewed and the relationship with OTP is expected to be diminishing (doubling from 100 to 200 riders matters more than from 5,000 to 5,100).
- Compare adjusted R² between the six-feature and seven-feature models using a nested F-test.
- Check VIF for the expanded model to assess multicollinearity with stop count and span.
- If ridership is significant, test a reduced model (ridership + mode only) to see if ridership proxies for stop count.
- Report beta weights, p-values, and model comparison statistics.
- Repeat with bus-only subset.

## Data
- `otp_monthly`: route_id, month, otp (averaged to route-level)
- `ridership_monthly`: route_id, month, day_type='WEEKDAY', avg_riders (averaged across all months)
- `route_stops`: route_id, stop_id for stop counts; stops lat/lon for geographic span
- `routes`: route_id, mode for subtype classification
- Overlap period (Jan 2019 -- Oct 2024); exclude routes with fewer than 12 months of paired data.

## Output
- `output/model_comparison.csv` -- side-by-side regression results (base vs expanded vs bus-only)
- `output/vif_table.csv` -- VIF values for expanded model
- `output/coefficient_comparison.png` -- beta weight comparison between base and expanded models
- `output/partial_residual.png` -- partial residual plot for log_ridership
