# Methods: Anomaly Investigation

## Question
What explains the sharp OTP drops for routes like Charles, Squirrel Hill, and Spring Garden? Are they real performance issues or data artifacts?

## Approach
- For each route, flag months where OTP deviates more than 2 standard deviations from the route's rolling 12-month mean.
- Catalog all flagged anomalies with route, month, OTP value, and deviation magnitude.
- Cross-reference known events: COVID shutdowns (Mar 2020), PRT service restructurings, construction projects.
- Classify anomalies as likely data issues vs. genuine performance events where possible.

## Data
- `otp_monthly` -- monthly OTP per route
- `routes` -- route metadata

## Output
- `output/anomalies.csv` -- all flagged anomaly months
- `output/anomaly_profiles.png` -- time series for routes with most anomalies
