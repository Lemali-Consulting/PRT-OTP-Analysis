# Methods: Weather Impact on OTP

## Question

Does weather (precipitation, snow, temperature) explain OTP variance or the counterintuitive seasonal pattern found in Analysis 06 (winter months outperform fall)?

## Approach

Three analysis blocks test weather's explanatory power at different levels:

**Block A -- System-level weather-OTP correlation:**
- Join `weather_monthly` to system-wide monthly OTP (trip-weighted from balanced panel of routes).
- Compute Pearson and Spearman correlations for each weather variable vs system OTP.
- Detrend both series (subtract 12-month rolling mean) to remove shared secular trends, then re-test.
- Fit a multiple regression: system OTP ~ weather variables (controlling for linear trend).

**Block B -- Seasonal decomposition test:**
- Replicate Analysis 06's monthly seasonal profile (month-of-year deviations from trend).
- Add weather controls: does the September trough disappear after adding weather? Does the January peak?
- Compare R2 of month-only model vs month + weather model.
- Key test: if weather fully explains the seasonal pattern, month dummies should lose significance.

**Block C -- Route-level panel regression:**
- Join weather to route-month OTP observations (long format).
- Route fixed effects + weather variables.
- Tests whether weather affects OTP *within* routes over time (not just across routes).

## Data

- `weather_monthly` -- monthly weather aggregates from NOAA GHCND station USW00094823 (Pittsburgh Intl Airport). Built by `src/prt_otp_analysis/weather.py`.
- `otp_monthly` -- route-month OTP observations.
- `routes` -- route metadata (mode, name).
- `route_stops` -- trip counts for weighting.

## Output

- `weather_otp_correlation.csv` -- correlation matrix of weather variables vs system OTP
- `model_comparison.csv` -- regression results for all models
- `weather_otp_timeseries.png` -- weather time series overlaid with system OTP (dual-axis)
- `seasonal_weather_adjusted.png` -- monthly seasonal profile: actual vs weather-adjusted
- `weather_scatter_matrix.png` -- scatter matrix of key weather variables vs detrended system OTP
- `weather_correlation_heatmap.png` -- heatmap of weather variable inter-correlations
