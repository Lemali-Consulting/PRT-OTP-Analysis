# Findings: Population Transit Proximity

## Key findings

1. **Denser census tracts sit much closer to PRT transit.** Across the 386
   populated census tracts in Allegheny County, population density and
   distance to the nearest stop are strongly negatively correlated
   (Spearman ρ = −0.62, p < 0.001). The county's people-dense neighborhoods
   are, as a rule, its best-served.

2. **The proximity gradient is steep and consistent.** Sorting tracts into
   population-density quartiles, the median distance to the nearest stop
   falls monotonically as density rises:

   | Density quartile | Median distance to nearest stop |
   |------------------|---------------------------------|
   | Q1 (sparsest)    | 1,350 m (~0.84 mi)              |
   | Q2               | 417 m                           |
   | Q3               | 194 m                           |
   | Q4 (densest)     | 151 m (~0.09 mi)                |

   A resident of the densest quartile of tracts is typically within a
   two-minute walk of a stop; in the sparsest quartile the nearest stop is
   nearly nine times farther away.

3. **The typical tract is well served.** The median Allegheny County tract
   centroid is just 318 m from the nearest stop — comfortably inside a
   quarter-mile walk.

4. **Coverage thins out in the lower-density tracts.** 301 of 394 tracts have
   their centroid within 805 m (≈ ½ mile) of a stop, but those tracts hold
   only **67.5%** of the county's population. The roughly one-third of
   residents beyond that threshold are concentrated in the lower-density
   tracts that the gradient above shows are farthest from service.

5. **Together with Analysis 44, this answers both halves of the access
   question.** Analysis 44 ranks which routes reach the most people;
   this analysis shows that proximity to transit tracks population density —
   PRT's network is built where the people are, and the unserved share lives
   in the spread-out periphery.

## Limitations

- **Area-level (ecological) result.** The correlation describes census
  tracts, not individuals. It does not measure who rides transit or how far
  any particular resident walks.
- **Straight-line distance from the tract centroid.** The real walk follows
  the street network and is usually longer; Pittsburgh's rivers and hillsides
  make this gap larger than in a flat, gridded city. A centroid also
  misrepresents large or irregularly shaped tracts.
- **Stop presence is not service quality.** A nearby stop may be served only
  hourly. Proximity is necessary but not sufficient for useful transit access.
- **Allegheny County only.** Tracts in the four adjacent counties present in
  the `census_tracts` table are excluded, since PRT service there is sparse
  and would dominate the "far from transit" tail without being informative.

## Validation

- **Data source verified.** Tract population, land area, and polygons from the
  `census_tracts` table (`prt.db`), loaded via `walksheds.load_tracts` and
  checked against the `CENSUS_TRACTS` schema. Stop coordinates from the
  `stops` table.
- **Geographic scope matches.** Both inputs are filtered to Allegheny County
  (`county_fips = '003'`), 394 tracts — consistent with the 2020 Census tract
  geography for the county.
- **Null/missing handling.** Stops with null coordinates are excluded. The 8
  tracts with zero ACS population are excluded from the density correlation
  and quartiles (density is undefined for them) but retained for the coverage
  count.
- **Direction of effects checked.** Density and distance are negatively
  correlated and the quartile gradient is monotonic — the expected direction
  (transit is built where people are). A positive correlation would have been
  a red flag.
- **Surprising results investigated.** None. The result is consistent with
  Analysis 44 and with standard transit-geography expectations; no value fell
  outside the plausible range.
- **Small-sample note.** Distances are deterministic geographic measures, not
  sampled estimates, so no minimum-observation threshold applies. The
  correlation uses all 386 populated tracts.
