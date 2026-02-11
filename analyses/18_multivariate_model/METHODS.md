# Methods: Multivariate OTP Model

## Question
How much of OTP variation can we explain with available structural variables? Which factors matter most when all are considered simultaneously? Previous analyses found effects for stop count (Analysis 07), mode (Analysis 02), and geographic span (Analysis 12), but these were tested individually. A multivariate model quantifies relative importance and reveals how much variance remains unexplained.

## Approach
- For each route with OTP data, assemble features: stop count, geographic span (km), mode (BUS/RAIL dummy), bus subtype (local/limited/express/busway/flyer dummies), weekend service ratio, and number of municipalities served.
- Fit an OLS regression with average OTP as the dependent variable.
- Report R-squared, adjusted R-squared, and per-feature coefficients with p-values.
- Use standardized coefficients (beta weights) to compare relative importance across features with different scales.
- Generate a coefficient plot and a predicted-vs-actual scatter plot.

## Data
- `otp_monthly` -- monthly OTP per route (averaged)
- `route_stops` -- stop count, trip counts per route
- `stops` -- lat/lon for span calculation, muni for jurisdiction count
- `routes` -- mode classification

## Output
- `output/model_coefficients.csv` -- feature, coefficient, std error, p-value, beta weight
- `output/coefficient_plot.png` -- horizontal bar chart of standardized coefficients
- `output/predicted_vs_actual.png` -- scatter plot with 1:1 line
