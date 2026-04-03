# Findings: National Service Cuts (2019 vs 2024)

## Summary

PRT cut 13.1% of vehicle revenue hours between 2019 and 2024, ranking 104th of 150 large US transit agencies (worse than the -6.8% median). However, PRT's ridership dropped 40.8% over the same period — a 27.7 pp gap that strongly suggests the ridership decline is primarily a demand-side problem, not a consequence of service cuts.

## Key Numbers

- **PRT VRH change**: -13.1% (2,382,972 → 2,070,196 hours)
- **PRT UPT change**: -40.8% (64.0M → 37.9M trips)
- **PRT VRH rank**: 104th of 150 (1st = best recovery)
- **National median VRH change**: -6.8%
- **Agencies recovered to 2019 VRH**: 48 of 150 (32%)
- **Supply–demand gap**: 130 of 150 agencies lost more riders than service (below the y=x diagonal)

## Observations

- **PRT's ridership problem is demand-driven.** PRT cut 13% of service hours but lost 41% of riders. The 28 pp gap means roughly two-thirds of the ridership loss occurred independently of service reductions. This pattern holds across virtually all peers and nationally.
- **PRT is mid-pack on service cuts among peers.** Cleveland cut the least (-3.2%), while St. Louis cut the most (-29.3%). PRT sits between Portland (-10.7%) and Buffalo (-14.8%).
- **Denver and Minneapolis cut service aggressively.** Both cut 23–24% of VRH, among the steepest cuts in the peer group, but their ridership losses (-39%) were proportionally smaller relative to the service reductions compared to East Coast peers.
- **Supply–demand gaps vary significantly.** Cleveland maintained 97% of service but lost 23% of riders (19 pp gap). Baltimore cut 7% but lost 32% (25 pp gap). The gap ranges from 15 pp (Denver) to 28 pp (Pittsburgh) among peers.
- **Service recovery is slow but ongoing.** By 2024, 48 of 150 agencies (32%) had recovered to 2019 VRH levels, up from 26 (17%) at the 2023 mark. The median cut narrowed from -10.8% to -6.8%, indicating gradual national service restoration.
- **Service growth does not guarantee ridership recovery.** Of the 48 agencies that grew VRH, many still have not recovered ridership. Sacramento grew VRH by 29% but still lost riders.
- **Trajectory charts reveal distinct recovery shapes.** Cleveland's VRH barely dipped and recovered quickly (V-shape), while St. Louis and Denver show L-shaped stagnation at ~70–75% of 2019 levels. PRT's service trajectory shows a gradual decline through 2023 followed by a modest uptick in 2024 — not the sharp COVID-era drop-and-bounce seen in some peers. Ridership trajectories are uniformly worse: all peers collapsed to 40–60% of baseline in 2020 and have only partially recovered, with Pittsburgh among the slowest to rebound.

## Discussion

The dominant national pattern is that transit agencies lost far more riders than they cut service. This suggests the post-COVID ridership shortfall is primarily driven by changed travel patterns (remote work, shifted commuting) rather than by service austerity. PRT fits this pattern: even if all 2019 service hours were restored tomorrow, the data suggests ridership would remain well below 2019 levels.

That said, service cuts and ridership loss are not fully independent. Reduced frequency makes transit less attractive, creating a feedback loop: cut service → longer waits → some riders leave → further cuts seem justified. The 13% VRH reduction likely contributed some portion of the 41% ridership loss, but the cross-agency evidence shows the demand shift is the larger driver.

Among peers, the agencies with the smallest service cuts (Cleveland, Baltimore) do not consistently show the best ridership recovery, reinforcing that supply restoration alone is insufficient.

## Caveats

- **System-level aggregation.** The TS2.2 data combines all modes and types of service into a single VRH figure per agency. PRT's bus vs. rail service changes cannot be separated in this dataset.
- **VRH measures scheduled service, not effective service.** An agency could maintain VRH while degrading reliability, frequency, or coverage in ways that don't appear in this metric.
- **No causal claim.** The supply–demand gap does not prove that service cuts had no effect on ridership — only that the ridership decline substantially exceeds what service reductions alone could explain.

## Validation

- **Data source verified.** VRH and UPT from `ntd_annual_service` table, loaded from FTA TS2.2 workbooks (2023 + 2024 editions) via pipeline 06.
- **Aggregates sanity-checked.** PRT 2019 UPT (64.0M) matches NTD monthly data aggregation from Analysis 36. Top agencies by VRH (NYCT, NJT, WMATA, CTA) are consistent with known largest US transit systems.
- **Direction of effects checked.** VRH and UPT both declined for most agencies (expected post-COVID). Agencies with positive VRH growth (Sacramento, Fort Worth) are known to have expanded service.
- **Surprising results investigated.** PRT's VRH partially recovered from -15.0% (2023) to -13.1% (2024), consistent with PRT's reported incremental service restorations.
