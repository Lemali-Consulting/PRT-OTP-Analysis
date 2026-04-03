# Findings: Operating Cost Drivers

## Key findings

1. **PRT's cost premium is concentrated in vehicle maintenance.** At $3.34 per trip, Pittsburgh's vehicle maintenance cost is the highest among all 8 peers — 47% above the peer average ($2.27). The other three cost categories (vehicle operations, non-vehicle maintenance, general admin) are mid-pack or below average.

2. **General administration is PRT's leanest category.** At $2.23 per trip, PRT's gen admin cost is the second-lowest among peers (only Buffalo is lower at $1.60). Baltimore ($4.07), Denver ($3.79), and St. Louis ($3.69) spend far more on admin per trip.

3. **Bus fleet age does not explain the maintenance premium.** A scatter plot of bus average age vs vehicle maintenance cost per trip shows a negative correlation (r = -0.52) — the opposite of what we'd expect if older buses drove higher costs. Pittsburgh's bus fleet (avg 7.1 years) is younger than Minneapolis (10.5) and Buffalo (9.1), yet its maintenance costs are far higher. The negative correlation likely reflects that cities with older buses (Minneapolis, Buffalo) are smaller systems with lower cost-of-labor.

4. **PRT's light rail fleet is the 3rd oldest among peers at 32.4 years.** Only Cleveland (43.0) and Buffalo (40.0) have older light rail vehicles. Denver (16.6) and Minneapolis (10.8) have much newer fleets. The aging light rail fleet likely contributes to PRT's elevated vehicle maintenance costs — rail vehicle maintenance is more expensive per unit than bus maintenance, and older rail vehicles require more intensive overhaul.

5. **Vehicle maintenance costs spiked in 2020-2021 and stayed elevated.** The cost trends show PRT's vehicle maintenance per trip jumped sharply when ridership cratered (fixed maintenance costs spread across fewer trips), but unlike most peers, it has not recovered. This suggests PRT's maintenance costs are largely fixed rather than variable with ridership.

6. **All per-trip costs spiked during COVID due to the denominator effect.** When ridership drops 40% but expenses don't drop proportionally, per-trip costs mechanically increase. The key question is which costs recovered as ridership partially stabilized — and for PRT, vehicle maintenance did not.

## Limitations

- **Per-trip normalization amplifies fixed costs.** Agencies with large fixed infrastructure (rail, maintenance facilities) will show higher per-trip costs when ridership drops, even if absolute spending is unchanged.
- **NTD cost categories are broad.** "Vehicle maintenance" includes both bus and rail maintenance. We cannot separate the light rail maintenance premium from bus maintenance in this data.
- **Fleet age is a proxy.** Average age doesn't capture fleet condition, maintenance practices, or rebuild history. Two fleets of the same age can have very different maintenance needs.
- **8 peers is a small sample for correlation analysis.** The r = -0.52 is suggestive but not statistically robust with n = 8.

## Validation

- **Data source verified.** Cost sub-categories from NTD TS2.2 OpExp sheets (VO, VM, NVM, GA). Fleet age from NTD Socrata API dataset `6abt-uhgq`.
- **Aggregates sanity-checked.** OpExp sub-categories sum exactly to OpExp Total for all peers and years.
- **Direction of effects checked.** Per-trip costs spiked in 2020-2021 (consistent with ridership crash) and partially recovered (consistent with partial ridership recovery). No anomalies.
- **Surprising result investigated.** The negative bus-age-vs-maintenance correlation is counterintuitive but likely reflects a confound: smaller cities (Buffalo, Minneapolis) have older fleets AND lower labor costs. With n = 8 we cannot control for this.
