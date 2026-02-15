# Findings: Ridership Concentration & Equity

## Summary
Ridership is **moderately concentrated on low-OTP routes**. The bottom quintile of routes by OTP (Q1, avg 61.2%) carries **29.6% of all ridership** (32.7% bus-only), far more than its 20% "fair share." Half of all bus ridership is carried by just 33 of 89 routes, all with OTP below 66.8%. The Gini concentration index is modest (0.068 all routes, 0.145 bus-only), indicating the inequity is real but not extreme.

## Key Numbers
- **Gini concentration index**: 0.068 (all routes), 0.145 (bus-only)
- **50% of ridership** carried by 39/93 routes with OTP < 68.0% (all); 33/89 routes with OTP < 66.8% (bus)
- **Q1 (worst OTP quintile)**: 19 routes, avg OTP 61.4%, carries 29.6% of ridership
- **Q5 (best OTP quintile)**: 18 routes, avg OTP 80.9%, carries 23.4% of ridership
- **Q4 (second-best)**: 18 routes, avg OTP 72.5%, carries only 10.2% of ridership
- 93 routes with 12+ months of paired OTP and ridership data

## Observations
- The quintile distribution is U-shaped: Q1 (worst) and Q5 (best) carry the most ridership, while Q3-Q4 (middle) carry the least. This reflects two distinct high-ridership populations: heavily-used local bus routes with poor OTP (Q1) and rail/busway routes with good OTP and high ridership (Q5).
- The bus-only analysis sharpens the inequity: removing rail from Q5 drops its ridership share from 23.4% to 17.6%, while Q1 rises from 29.6% to 32.7%. Nearly a third of bus riders are on the worst-performing quintile of routes.
- The Gini index is low (0.068 all, 0.145 bus) because the concentration is moderate, not extreme. Ridership doesn't pile onto a handful of terrible routes -- it's spread across many poor-to-mediocre routes, with a few high-performing routes also carrying substantial ridership.
- The Lorenz curve bows above the diagonal throughout, confirming that at every point along the OTP spectrum, cumulative ridership exceeds what equal distribution would predict. The departure is most visible in the first 20-40% of routes (worst OTP).

## Discussion
The equity picture is mixed. On one hand, the worst-performing routes carry a disproportionate share of riders -- nearly 30% of ridership on the bottom 20% of routes. On the other hand, the best routes (Q5) also carry substantial ridership, so it is not the case that reliable service is reserved for lightly-used routes. The U-shape reflects PRT's system structure: high-ridership corridors tend to be either long, many-stop local bus routes (which have poor OTP due to route complexity, per Analysis 07) or dedicated right-of-way routes (rail/busway, which have good OTP). Middle-performing routes tend to be lower-ridership suburban and express services.

The bus-only Gini (0.145) is more than double the all-mode Gini (0.068), confirming that rail's presence in Q5 masks a more pronounced equity problem within bus service. If PRT seeks to improve the rider-weighted experience, targeting the Q1 bus routes (avg OTP 61.2%, 32.7% of bus ridership) offers the highest human impact per intervention.

## Caveats
- The Gini index here measures concentration of ridership across OTP ranks, not income inequality. A positive value means riders disproportionately use low-OTP routes; it does not imply any particular policy threshold.
- Ridership is averaged across all months, which weights the pre-COVID period (higher ridership) more heavily. Post-COVID ridership redistribution may have shifted the concentration pattern.
- OTP is route-level, not trip-level. A rider's actual experience depends on which trips they take, not just their route's monthly average.
- The quintile boundaries are sensitive to the number of routes. With 93 routes, each quintile contains 18-19 routes; small changes in route composition could shift the boundaries.
