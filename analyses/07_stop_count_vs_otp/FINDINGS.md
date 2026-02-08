# Findings: Stop Count vs OTP

## Summary

There is a **moderately strong negative correlation (r = -0.53)** between the number of stops on a route and its average OTP. This is the clearest structural predictor of poor OTP in the dataset.

## Key Numbers

- **Pearson r = -0.53** (93 routes)
- Routes with < 50 stops: typically 80%+ OTP
- Routes with 150+ stops: typically below 60% OTP

## Observations

- Every stop adds dwell time (boarding/alighting), traffic signal delay, and schedule recovery risk. The cumulative effect is substantial.
- Busway and rail routes tend to have fewer stops and dedicated right-of-way, giving them a double advantage.
- Route 77 (Penn Hills) is the extreme case: 258 stops and the worst OTP in the system (55.8%).
- Route 18 (Manchester) has only 43 stops and the best OTP (88.4%).
- The relationship holds across modes, though rail routes sit in the upper-left quadrant (few stops, high OTP) and local bus routes spread across the lower-right (many stops, low OTP).

## Implication

Stop consolidation -- reducing the number of stops on long routes -- is a common transit strategy for improving schedule adherence. This data strongly supports that approach for PRT's worst-performing routes.

## Caveats

- Correlation is not causation. Routes with many stops also tend to serve congested corridors, cover longer distances, and carry more passengers -- all of which independently affect OTP.
- Stop counts come from current `route_stops` data and may not match historical stop configurations.
