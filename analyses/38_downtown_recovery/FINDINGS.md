# Findings: Downtown Recovery Gap

## Summary
Downtown dependence is a statistically significant predictor of worse ridership recovery, partially supporting PRT's claim that weak downtown business activity drags system-wide ridership. Routes with higher shares of pre-pandemic downtown boardings show worse recovery trajectories. However, the effect is modest (Spearman rho = -0.29) and explains only a fraction of the system-wide gap — even routes with minimal downtown exposure remain well below 2019 levels.

## Key Numbers
- **Spearman correlation** between downtown boardings share and 2024 recovery: rho = -0.29, p = 0.005.
- **High downtown dependence** (top tercile, 31 routes, median 53% downtown share): median 2024 recovery = 53.4% of 2019.
- **Medium downtown dependence** (32 routes, median 41% downtown share): median recovery = 47.3%.
- **Low downtown dependence** (31 routes, median 15% downtown share): median recovery = 63.8%.
- **Kruskal-Wallis** across terciles: H = 8.64, p = 0.013.
- Only the **Medium vs Low** pairwise comparison is significant after Bonferroni correction (p = 0.02). High vs Low approaches significance (p = 0.11) but does not clear the threshold.

## Observations
- **PRT's claim is directionally correct but insufficient as a full explanation.** The negative correlation confirms that downtown-oriented routes have recovered less ridership. But the effect is modest — downtown dependence alone accounts for roughly 8% of the variance in recovery (rho-squared ~ 0.08).
- **Even non-downtown routes are far from recovery.** The low-dependence tercile sits at median 63.8% of 2019, meaning routes with almost no downtown exposure still lost over a third of their riders. This is not purely a downtown story.
- **The medium tercile recovered worst, not the high tercile.** This appears driven by commuter express routes (flyers like P12, P67, P71, P76) and express services (Y1, O1, G3) that fall in the medium range for downtown stop share but serve exactly the demographic most likely to shift to remote work. These routes lost 70-85% of ridership.
- **Large local routes in the high tercile held up better than expected.** Routes like 6, 12, 17, 81, 83 have >50% downtown share but recovered to 65-79% — likely because they serve diverse trip purposes (shopping, medical, transfers) beyond commuting.
- **The best-recovering routes are high-ridership trunk lines with low downtown shares:** 61A (84%), 61C (79%), 71B (80%), 59 (90%). These serve corridor travel that is less sensitive to office occupancy.
- **The trajectory chart shows all three groups tracking closely until mid-2021**, after which the low-dependence group pulls ahead. This timing aligns with the return of non-commute travel (errands, school, medical) while office occupancy remained depressed.

## Caveats
- **Downtown share is computed from pre-pandemic stop-level data (FY2019)**, not current patterns. Routes may have shifted service since 2019.
- **The stop-level CSV provides boarding counts, not trip purpose.** A downtown boarding could be a commuter, a shopper, a transfer, or a medical visitor. We cannot isolate the "office worker" effect directly.
- **Ecological inference limitation.** Route-level associations do not prove that individual downtown commuters failed to return — only that routes serving more downtown stops recovered less ridership in aggregate.
- **Ridership data ends Oct 2024.** More recent recovery may differ.
- **The 2 km downtown radius captures the Golden Triangle and adjacent areas** (e.g., Strip District edge, North Shore). A tighter boundary around the CBD might sharpen the signal.

## Validation
1. **Data source verified.** Downtown scores computed from `wprdc_stop_data.csv` (stop-level ridership with coordinates). Recovery trajectories from `ridership_monthly` (route-level weekday ridership). Both checked against prior analyses (33, 21).
2. **Geographic scope matches.** Downtown centroid and 2 km radius match analysis 33's definition. Pre-pandemic baseline (2019) matches analysis 21 and 37.
3. **Null handling.** Routes with zero 2019 baseline excluded from indexing. Stop records with null lat/lon excluded from downtown scoring.
4. **Aggregates sanity-checked.** System-wide recovery around 55-60% is consistent with analysis 37's finding of 57.6% via NTD data. Individual route recoveries match analysis 21's findings.
5. **Direction of effects checked.** More downtown dependence associates with worse recovery — consistent with the remote-work hypothesis. Low-dependence routes recovering better is consistent with known patterns of non-commute ridership being more resilient.
6. **Small-sample routes present.** Some routes (O5, 7, 71, 18) have very low baselines (<200 avg daily riders). These contribute equally to tercile medians despite less reliable estimates.
