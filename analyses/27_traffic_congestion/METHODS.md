# Methods: Traffic Congestion and OTP

## Question
Does traffic volume (AADT) explain OTP variance beyond stop count, geographic span, and other structural features from the Analysis 18 model?

## Approach
- Replicate the Analysis 18 six-feature OLS model on routes with matched PennDOT traffic data.
- Filter to routes with `match_rate >= 0.3` (sufficient spatial overlap with PennDOT road network).
- Add log-transformed weighted AADT as a seventh predictor. Log transform is used because the effect of traffic on delays is expected to show diminishing returns (doubling from 5,000 to 10,000 AADT matters more than 25,000 to 30,000).
- Compare adjusted R-squared between six-feature and seven-feature models using a nested F-test.
- Fit a second expanded model adding `avg_truck_pct` as an eighth predictor.
- Check VIF for multicollinearity (AADT may correlate with span or stop count).
- Repeat with bus-only subset.
- Generate bivariate scatter (AADT vs OTP), coefficient comparison chart, and partial residual plot.

## Data
- `otp_monthly`: route_id, month, otp (averaged to route-level, 12+ months required)
- `route_traffic`: route_id, weighted_aadt, avg_truck_pct, match_rate (from `traffic_overlay.py`)
- `route_stops`: stop counts, trip frequencies; `stops`: lat/lon for geographic span
- `routes`: route_id, mode for subtype classification

## Output
- `output/model_comparison.csv` -- regression results for all models
- `output/vif_table.csv` -- VIF values for expanded model
- `output/route_traffic_summary.csv` -- per-route traffic data with OTP
- `output/aadt_vs_otp_scatter.png` -- bivariate scatter of AADT vs OTP
- `output/coefficient_comparison.png` -- beta weight comparison between base and expanded models
- `output/partial_residual.png` -- partial residual plot for log_aadt
