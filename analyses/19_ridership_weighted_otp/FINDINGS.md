# Findings: Ridership-Weighted OTP

## Summary
Ridership-weighted system OTP (69.4%) runs **1.6 percentage points higher** than trip-weighted OTP (67.8%), and the difference is statistically significant (paired t = -18.1, p < 0.001; Wilcoxon W = 1, p < 0.001). This means the average PRT rider experiences slightly *better* on-time performance than the trip-weighted system average suggests.

## Key Numbers
- **Unweighted OTP** (all routes equal): 69.9% mean, 70.3% median
- **Trip-weighted OTP** (scheduled frequency): 67.8% mean, 67.8% median
- **Ridership-weighted OTP** (avg daily riders): 69.4% mean, 69.2% median
- **Ridership vs trip-weighted gap**: +1.6 pp (p < 0.001, n = 70 months)
- 93 routes with 12+ months of paired OTP + ridership data
- Overlap period: Jan 2019 -- Oct 2024 (70 months)

## Interpretation
Both weighted series fall *below* the unweighted average, meaning both scheduled trips and actual riders concentrate somewhat on worse-performing routes. However, **trip frequency overstates how much ridership is concentrated on the worst routes**. High-frequency routes tend to have many stops and poor OTP (Analysis 07), but riders don't fill those trips proportionally -- some high-frequency routes carry fewer riders per trip than expected. The result is that the average rider's experience is worse than the average route's OTP, but not as bad as the trip-weighted number implies.

This does *not* mean high-ridership routes have better OTP. It means ridership is distributed more evenly across the OTP spectrum than trip frequency is.

## Observations
- The gap between trip-weighted and ridership-weighted OTP is not constant: it was near zero during COVID (2020), widened to ~3 pp in late 2022, and has stabilized around 1--2 pp since 2023. This likely reflects post-COVID ridership redistribution.
- All three series show the same overall trend: COVID spike, steady decline through late 2022, partial stabilization in 2023--2024.

## Caveats
- Ridership data is weekday average only; the analysis does not capture weekend rider experience.
- `route_stops.trips_7d` is a current snapshot, not a monthly time series -- trip-weighted OTP uses the same weights for all months.
- Routes missing from the ridership dataset (RLSH, SWL) are excluded from all three series for comparability, so the unweighted series here may differ slightly from Analysis 01.
- The ridership CSV ends Oct 2024 while OTP data extends to Nov 2025; the analysis is restricted to the overlap period.
