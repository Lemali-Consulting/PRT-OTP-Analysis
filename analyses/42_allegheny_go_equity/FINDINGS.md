# Findings: Allegheny Go Equity

## Summary

There is no statistically significant relationship between municipal on-time
performance and Allegheny Go program adoption. The Spearman correlation between
trip-weighted OTP and estimated reached households is ρ = −0.080 (p = 0.496,
n = 74 municipalities). This result is robust to removing Pittsburgh
(ρ = −0.079, p = 0.504).

## Key Numbers

- 74 of 99 tract municipalities matched to OTP data (75% match rate)
- Spearman ρ = −0.080 (p = 0.496) — no significant association
- Pittsburgh dominates adoption: 6,025 estimated reached households across 111 census tracts
- Program demographics: 59% Black, 64% female, 26% aged 25–34
- 71% of rides taken by participants who have enrolled

## Observations

- **Pittsburgh dominates the data.** With 111 of 326 tracts and an estimated 6,025
  reached households, Pittsburgh is a massive outlier. Even removing it does not
  change the null result.
- **Adoption appears driven by population density and program outreach**, not by
  transit service quality. Municipalities with large low-income populations
  (Pittsburgh, McKeesport, Wilkinsburg) have high adoption regardless of OTP.
- **Demographics suggest the program reaches its target population.** 59% of
  participants are Black (vs ~13% of Allegheny County), and 64% are female.
  The age distribution skews younger (25–34 is the largest group at 3,112).
- **Municipalities with poor OTP do not have systematically lower adoption.**
  Penn Hills (OTP 0.617, 279 households) and North Braddock (OTP 0.623, 238
  households) have high adoption despite poor service. This suggests the program
  successfully reaches areas with unreliable transit.

## Caveats

- Reached-household tiers (1-5, 6-25, etc.) are converted to midpoints for
  aggregation. The 101-500 tier has a very wide range; results are directionally
  consistent using ordinal ranks instead.
- 25 tract municipalities had no match in the OTP data, mostly areas without PRT
  bus service (e.g., Pine Township, Forward Township). These are correctly excluded.
- This is an ecological analysis at the municipality level. Individual-level
  claims about OTP and program participation cannot be drawn.
- OTP data covers 2019-01 to 2025-11, while adoption data is a snapshot; the
  temporal mismatch could mask relationships.

## Validation

1. **Data source verified.** Tract reach data from Allegheny Go Tableau dashboard;
   OTP aggregation uses the same pattern as Analysis 15.
2. **Geographic scope matches.** Both datasets cover Allegheny County municipalities.
3. **Null handling.** Tracts with "Unpopulated Areas" and "%null%" municipalities
   filtered out before joining.
4. **Aggregates sanity-checked.** Total midpoint households (~12,000) is consistent
   with the ~11,900 enrolled participants reported in program demographics.
5. **Surprising result investigated.** The null correlation was checked with and
   without Pittsburgh, and with ordinal vs midpoint encoding. The null holds across
   all specifications.
