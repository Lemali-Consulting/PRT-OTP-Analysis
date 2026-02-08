# Findings: Trip Frequency vs OTP

## Summary

There is a **moderate negative correlation (r = -0.39)** between total weekday stop-visits and OTP. Higher-frequency routes tend to perform worse, but the effect is weaker than the stop count correlation and likely confounded.

## Key Numbers

- **Pearson r = -0.39** (93 routes)
- High-frequency routes (10,000+ weekday stop-visits) average ~63% OTP
- Low-frequency routes (< 2,000 weekday stop-visits) average ~75% OTP

## Observations

- The correlation is weaker than stop count vs OTP (r = -0.53), suggesting that route complexity (number of stops) matters more than service frequency alone.
- High-frequency routes also tend to have more stops and serve congested corridors, making it difficult to isolate the pure frequency effect.
- Some high-frequency routes perform well: P1 (East Busway) has high trip volume but also high OTP, because it runs on dedicated right-of-way with few stops.
- The metric used (total weekday stop-visits = sum of `trips_wd` across all stops) conflates frequency with route length. A route with 50 trips and 100 stops produces the same value as one with 100 trips and 50 stops.

## Implication

Running more trips per se probably doesn't degrade OTP much. The real issue is that PRT's highest-frequency routes are also its longest and most complex. A better metric for isolating the frequency effect would be trips per direction at a single timepoint stop.

## Caveats

- `trips_wd` in `route_stops` represents current weekday frequency, not historical. Frequency may have changed over the analysis period.
- The stop-visit metric double-counts in a way that makes it hard to separate frequency from route length.
