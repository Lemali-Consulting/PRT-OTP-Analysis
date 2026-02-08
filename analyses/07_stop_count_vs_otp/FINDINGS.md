# Findings: Stop Count vs OTP

## Summary

There is a **moderately strong negative correlation** between the number of stops on a route and its average OTP. This finding holds for both all routes and bus-only analysis, ruling out Simpson's paradox as a confounder.

## Key Numbers

- **All routes: Pearson r = -0.53** (p < 0.001, n = 93)
- **Bus only: Pearson r = -0.50** (p < 0.001, n = 90)
- **Bus only: Spearman r = -0.48** (p < 0.001)
- Routes with < 50 stops: typically 80%+ OTP
- Routes with 150+ stops: typically below 60% OTP

## Observations

- The bus-only correlation (r = -0.50) is nearly as strong as the all-routes correlation (r = -0.53), confirming that the effect is not driven by the BUS/RAIL mode split (Simpson's paradox). Stop count predicts OTP within the bus mode alone.
- The Spearman rank correlation (r = -0.48) is consistent with the Pearson, indicating the relationship is approximately monotonic without being driven by outliers or non-linearity.
- Every stop adds dwell time (boarding/alighting), traffic signal delay, and schedule recovery risk. The cumulative effect is substantial.
- Busway and rail routes tend to have fewer stops and dedicated right-of-way, giving them a double advantage.
- Route 77 (Penn Hills) is an extreme case: 258 stops and among the worst OTP in the system.

## Implication

Stop consolidation -- reducing the number of stops on long routes -- is a common transit strategy for improving schedule adherence. This data strongly supports that approach for PRT's worst-performing routes.

## Caveats

- Correlation is not causation. Routes with many stops also tend to serve congested corridors, cover longer distances, and carry more passengers -- all of which independently affect OTP.
- Stop counts come from current `route_stops` data and may not match historical stop configurations.
