# Findings: Route Population Reach

## Summary
Each PRT route's resident population reach was estimated by buffering its stops by ¼ mile (bus) or ½ mile (rail/incline), dissolving the buffers per route, and apportioning ACS 5-year (2018–2022) tract population to those walksheds via areal interpolation. The top-reaching routes are concentrated in the Pittsburgh core: light-rail RED (58k), bus 69 (55k), light-rail SLVR (53k), and the 54 / 61A / 61C corridors all exceed 48,000 residents within walking distance.

## Key Numbers
- **100 routes** scored across the PRT system using **6,466 stops** and **669 census tracts** in Allegheny + Beaver + Butler + Washington + Westmoreland counties (5-county population: 2.17M).
- **Median route reach: 21,393 residents.** Mean: 23,943.
- **Top route by total reach:** RED Line (LRT) — **58,425 residents** across 59 stops.
- **Top bus route by total reach:** Route 69 — **55,088 residents** across 209 stops.
- **Most efficient reach (population per stop):** Mon Incline (2,347), then Duquesne Incline (1,343), then BLUE Line (1,028). Bus routes top out at ~310 residents/stop (61C).
- **Lowest reach:** DQI (2,686), O1 (3,015), 18 Manchester (4,169) — short or specialty routes.

## Observations
- **Light rail is structurally efficient.** Despite having far fewer stops than the busiest bus routes (~45–60 vs ~200), the RED, SLVR, and BLUE lines reach as many or more residents because the larger ½-mile rail walkshed and the South Hills' density combine to broaden each station's catchment.
- **Bus reach concentrates on the Oakland–East End corridor and cross-town spines.** The 61A/B/C/67 group (Oakland trunk to Squirrel Hill / Homestead / Swissvale) and routes 54 (north-south crosstown) and 75 (Oakland–Bloomfield) all exceed 43,000 — these are the routes whose disruptions affect the most people.
- **Inclines have the highest population per stop** (2,000+ for the Mon Incline) because they sit in dense Mt. Washington / South Side neighborhoods, but absolute reach is small (only 2 stops each).
- **Route length and stop count predict, but do not determine, reach.** Route 18 (Manchester) has 43 stops and reaches only 4,169 — its corridor is in low-density industrial North Side. Route O1 has 7 stops and reaches 3,015 — typical of express park-and-ride routes. Density of the served corridor matters as much as the size of the route.

## Caveats
- **Walkshed buffers are circular Euclidean** (¼ / ½ mile straight-line), not network walking distance. Real walksheds are smaller and irregular — actual usable reach is overstated, especially in areas with rivers, hillsides, or cul-de-sacs (much of Pittsburgh).
- **Areal interpolation assumes uniform population within each tract.** Tracts in Pittsburgh are small in the urban core but large at the periphery; for outlying tracts (Beaver, Butler), a small overlap may apportion population from areas with no actual residents.
- **Reach is not ridership.** A route can pass through dense neighborhoods that don't ride it (e.g., affluent areas with high car ownership). For demand-weighted impact, see Analysis 22 (Delay Burden).
- **Routes are not mutually exclusive.** Summing `population_served` across all routes (~2.39M) double-counts residents served by multiple routes — the figure exceeds the 5-county population and is not a valid system total.
- **ACS population is 2018–2022 averages.** Post-pandemic shifts (e.g., downtown depopulation) are partially captured but lag current conditions.

## Validation
- **Data source verified.** TIGER 2022 tract polygons and ACS 5-year B01003_001E pulled live from census.gov; 5-county total of 2.17M matches published Census estimates (Allegheny 1.25M + adjacent ~0.9M).
- **Geographic scope matches.** All routes' stops fall within the 5-county tract set; no walkshed extends past the loaded tract polygons.
- **Null/missing handling.** Stops with NULL lat/lon excluded (none observed in current `stops` table). Tracts with `population` NULL contribute zero.
- **Aggregates sanity-checked.** Top routes are well-known dense-corridor service (Oakland trunk, Mon Valley LRT). Lowest-reach routes are short specialty/express routes — direction of effect matches expectation.
- **Surprising results investigated.** Light rail outranking the busiest bus route was checked: RED has 59 stops with the larger ½-mile rail buffer, giving it 27.7 km² of walkshed vs. 23.4 km² for bus 69 — the result is consistent with the methodology.
