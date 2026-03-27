# Findings: National Service Cuts (2019 vs 2023)

## Summary

PRT cut 15.0% of vehicle revenue hours between 2019 and 2023, ranking 97th of 150 large US transit agencies (worse than the -10.8% median). However, PRT's ridership dropped 40.8% over the same period — a 25.8 pp gap that strongly suggests the ridership decline is primarily a demand-side problem, not a consequence of service cuts.

## Key Numbers

- **PRT VRH change**: -15.0% (2,382,972 → 2,025,498 hours)
- **PRT UPT change**: -40.8% (64.0M → 37.9M trips)
- **PRT VRH rank**: 97th of 150 (1st = best recovery)
- **National median VRH change**: -10.8%
- **Agencies recovered to 2019 VRH**: 26 of 150 (17%)
- **Supply–demand gap**: 136 of 150 agencies lost more riders than service (below the y=x diagonal)

## Observations

- **PRT's ridership problem is demand-driven.** PRT cut 15% of service hours but lost 41% of riders. The 26 pp gap means roughly two-thirds of the ridership loss occurred independently of service reductions. This pattern holds across virtually all peers and nationally.
- **PRT is mid-pack on service cuts among peers.** Cleveland cut the least (-7.3%), while St. Louis cut the most (-34.2%). PRT sits between Baltimore (-12.0%) and Buffalo (-15.6%).
- **Denver and Minneapolis cut service aggressively.** Both cut 25–27% of VRH, among the steepest cuts in the peer group, but their ridership losses (-39% and -42%) were proportionally smaller relative to the service reductions compared to East Coast peers.
- **Supply–demand gaps vary significantly.** Cleveland maintained 93% of service but lost 30% of riders (23 pp gap). Baltimore cut 12% but lost 38% (27 pp gap). The gap ranges from 12 pp (St. Louis, Denver) to 27 pp (Baltimore) among peers.
- **Service growth does not guarantee ridership recovery.** Of the 26 agencies that grew VRH, only 14 also grew ridership. Sacramento grew VRH by 24% but still lost 17% of riders.
- **Fleet reductions tracked service cuts.** PRT's VOMS (vehicles operated in maximum service) dropped from 942 to 780 (-17.2%), roughly proportional to the VRH cut.

## Discussion

The dominant national pattern is that transit agencies lost far more riders than they cut service. This suggests the post-COVID ridership shortfall is primarily driven by changed travel patterns (remote work, shifted commuting) rather than by service austerity. PRT fits this pattern: even if all 2019 service hours were restored tomorrow, the data suggests ridership would remain well below 2019 levels.

That said, service cuts and ridership loss are not fully independent. Reduced frequency makes transit less attractive, creating a feedback loop: cut service → longer waits → some riders leave → further cuts seem justified. The 15% VRH reduction likely contributed some portion of the 41% ridership loss, but the cross-agency evidence shows the demand shift is the larger driver.

Among peers, the agencies with the smallest service cuts (Cleveland, Baltimore) do not consistently show the best ridership recovery, reinforcing that supply restoration alone is insufficient.

## Caveats

- **System-level aggregation.** The TS2.2 data combines all modes and types of service into a single VRH figure per agency. PRT's bus vs. rail service changes cannot be separated in this dataset.
- **2023 is the latest available year.** The NTD Annual Module lags the monthly data (which goes to 2025). Service and ridership may have changed since 2023.
- **VRH measures scheduled service, not effective service.** An agency could maintain VRH while degrading reliability, frequency, or coverage in ways that don't appear in this metric.
- **No causal claim.** The supply–demand gap does not prove that service cuts had no effect on ridership — only that the ridership decline substantially exceeds what service reductions alone could explain.

## Validation

- **Data source verified.** VRH and UPT from `ntd_annual_service` table, loaded from FTA TS2.2 workbook via pipeline 06.
- **Aggregates sanity-checked.** PRT 2019 UPT (64.0M) matches NTD monthly data aggregation from Analysis 36. Top agencies by VRH (NYCT, NJT, WMATA, CTA) are consistent with known largest US transit systems.
- **Direction of effects checked.** VRH and UPT both declined for most agencies (expected post-COVID). Agencies with positive VRH growth (Sacramento, BART) are known to have expanded service.
- **Surprising results investigated.** BART's +19% VRH growth despite massive ridership losses reflects deliberate service restoration strategy — confirmed by public reporting.
