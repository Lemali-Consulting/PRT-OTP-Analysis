# Findings: Weekday vs Weekend Ridership Trends

## Summary
Weekend ridership has recovered far more strongly than weekday ridership since COVID. As of October 2024, Saturday service is at 90.7% of its January 2019 level while weekday service is at just 64.5%. Weekend's share of total ridership rose from 13.6% pre-COVID to 17.8% post-2023, a +4.2 pp structural shift. The weekend-to-weekday ridership ratio does **not** significantly correlate with route-level OTP (Pearson r = -0.20, p = 0.097).

## Key Numbers
- **Weekday recovery** (Oct 2024 vs Jan 2019): 64.5% -- weekday ridership has not recovered
- **Saturday recovery**: 90.7% -- nearly fully recovered
- **Sunday recovery**: 83.9%
- **Weekend share pre-COVID** (Jan 2019 -- Feb 2020): 13.6%
- **Weekend share post-2023** (Jan 2023 -- Oct 2024): 17.8%
- **Shift**: +4.2 pp toward weekend travel
- 74 routes with 6+ months of all three day types for route-level analysis
- 67 routes with both weekend ratio and OTP data for correlation

## Observations
- The indexed ridership chart shows a dramatic divergence after COVID. All three day types crashed in spring 2020, but Saturday and Sunday rebounded much faster and more completely than weekday service.
- The weekend share chart shows a step-change during COVID (weekend share spiked to ~25% when weekday commuting collapsed) followed by a partial return, stabilizing around 17-18% -- well above the pre-COVID 13-14% level.
- Route-level weekend ratios vary widely: median 0.97 (roughly equal weekend and weekday ridership per day of service), but ranging from 0.29 (route BLSV, heavily weekday-oriented) to 1.85+ for some routes.
- The correlation between weekend ratio and OTP is weakly negative (r = -0.20) but not statistically significant at alpha = 0.05. Routes with higher weekend share do not have meaningfully different OTP.

## Discussion
The 26-percentage-point gap in recovery between weekday (64.5%) and Saturday (90.7%) service is the headline finding. This is consistent with national trends: remote and hybrid work has permanently reduced weekday commuting, while discretionary weekend travel has largely returned. For PRT, this means:

1. **Revenue and planning implications**: The traditional weekday-peak service model serves a shrinking share of total demand. Weekend service, historically treated as reduced-frequency filler, now carries a proportionally larger role.
2. **OTP is not driving the gap**: Weekend-heavy routes do not have significantly different OTP, suggesting the weekday ridership collapse is driven by exogenous factors (remote work) rather than service quality differences between day types.
3. **Seasonal patterns visible**: Both Saturday and Sunday series show strong seasonal swings (summer peaks, winter troughs) that are more pronounced than weekday patterns, consistent with discretionary travel being more weather-sensitive.

## Caveats
- The `avg_riders` field is an average daily ridership for each month, not a total. Multiplying by `day_count` gives an estimate of total monthly riders, but this assumes uniform ridership across all days of a given type within a month.
- The January 2019 baseline is a single month; seasonal effects mean the indexed values fluctuate even in the pre-COVID period. The recovery percentages should be interpreted as approximate.
- Some routes have extreme weekend ratios (e.g., route 68 at 239x) likely due to very low weekday ridership rather than high weekend ridership. These outliers are excluded from the OTP correlation by the 6-month minimum and OTP data join.
- OTP data is not available by day type -- the `otp_monthly` table contains a single OTP value per route per month, so we cannot directly compare weekday vs weekend OTP.
