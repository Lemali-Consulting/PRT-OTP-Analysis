# Findings: Transit Service & Boardings vs Population Density

## Summary
Bus service scales strongly with residential density — denser Allegheny County
tracts get far more service, not just a nearer stop (Spearman ρ = 0.49 between
density and weekly bus trips). Boardings follow the same density gradient
(ρ = 0.56) and track service almost perfectly (ρ = 0.90), but they **diverge
sharply from raw population**: a tract's headcount barely predicts its boardings
(ρ = −0.14), and boardings are far more concentrated than people — the densest
quartile of tracts holds 23% of residents but generates 73% of boardings, and
Downtown alone accounts for 27%.

## Key Numbers
- **394 tracts** analyzed (386 populated), Allegheny County. 139,221 average
  weekday boardings total (Sept 2019), of which 138,780 fall inside a tract.
- **Service vs density:** Spearman ρ = **0.49** (p ≈ 7e-25). Median weekly bus
  trips by density quartile: **237 → 2,400 → 3,475 → 6,104** — a ~26× rise from
  the sparsest to the densest quarter of tracts.
- **Boardings vs density:** Spearman ρ = **0.56** (p ≈ 2e-33). Median weekday
  boardings by quartile: **3.8 → 44 → 92 → 330**.
- **Boardings vs population:** Spearman ρ = **−0.14** — essentially no
  relationship. **Boardings vs service:** ρ = **0.90**.
- **Boardings per 1,000 residents** by density quartile: **0.7 → 12 → 44 → 122**
  — a ~180× gradient, far steeper than the service gradient.
- **Concentration:** the densest quartile (22.7% of county population) produces
  **72.9%** of boardings; the top 10 tracts produce **46.6%**; the Central
  Business District alone produces **26.6%**.

## Observations
- **Q1 — service tracks density.** Service is not just present in dense tracts,
  it is concentrated there. The 26× quartile gradient in weekly trips is steeper
  than the proximity gradient Analysis 46 found, so the answer is unambiguous:
  dense neighborhoods get both a closer stop *and* much more service on it.
- **Q2 — boardings follow density but diverge from population.** Boardings rise
  with density at almost the same rank-correlation strength as service, and they
  shadow service itself extremely closely (ρ = 0.90). But the relationship is
  strongly **super-linear**: boardings per resident climb ~180× across density
  quartiles, so dense tracts board far more than their share of people. Raw
  population is a non-predictor (ρ = −0.14) because census tracts are drawn to
  hold roughly equal populations — what varies is density and destination role.
- **The biggest over-performers are destinations, not dense housing.** The
  Central Business District boards 36,202 riders a day — 27% of the county
  total — against only ~142 predicted by its (moderate) residential density.
  Other large over-performers are near-empty riverfront/industrial tracts
  (Chateau, 12 residents; South Shore, 47) and the airport-area Findlay
  township. Boardings are recorded where trips start, which concentrates them
  at employment and activity hubs.
- **The under-performers are the light-rail South Hills.** The tracts that board
  far below their density (Bethel Park, Castle Shannon, Mount Lebanon) are
  light-rail-served: their residents board the "T", which the bus-stop dataset
  does not cover. These are flagged `rail_served` in the output.

## Discussion
Analysis 46 showed PRT puts *stops* where the people are. This analysis shows
the same logic governs *service volume*: dense tracts get disproportionately
more bus service, and riders respond — boardings follow service almost
one-for-one. In that sense boardings do **not** diverge from the density
pattern; they amplify it.

The divergence is one of *degree and driver*. Boardings are far more unequal
than either population or service: they are destination-driven, so they pile up
in a handful of dense activity centers — above all Downtown — rather than
spreading across residential tracts in proportion to headcount. A planner
reading this should note that "serve the dense places" and "serve the most
residents" are not the same instruction: the boarding map is dominated by where
people *go*, not only where they *live*.

This is an **area-level (ecological) association**. It does not show that
individuals in dense tracts ride more — only that dense tracts, as places,
generate more boardings.

## Caveats
- **Bus-only.** The WPRDC stop-usage dataset covers bus and busway service;
  light rail has boarding data for a single stop. Both the service and the
  boardings metrics are therefore restricted to bus service. Light-rail-corridor
  tracts (notably the South Hills) genuinely show near-zero *bus* boardings
  because their riders use the "T"; they are flagged `rail_served`.
- **Temporal mismatch.** Boardings are September 2019; bus trip counts are the
  current GTFS snapshot; population is the ACS 2018–2022 estimate. The analysis
  assumes the spatial pattern is stable, not that levels are contemporaneous.
- **Stop-to-tract assignment is point-in-polygon.** A stop on a tract boundary
  counts entirely for one tract. Highland Park is the clearest artifact: it has
  1,580 weekly bus trips but ~0 recorded boardings because its service runs on
  perimeter corridors assigned to neighboring tracts and its interior is largely
  parkland.
- `weekly_trips` counts scheduled trips, not capacity or time-of-day frequency.
- Zero-population tracts are excluded from quartiles and correlations.

## Validation
- **Data sources verified.** `route_stops`, `routes`, `stops`, and
  `census_tracts` columns checked against the live schema; the boardings CSV
  schema inspected directly (long format, `datekey`/`serviceday`/`avg_ons`).
- **System total checked.** Summed boardings = 139,221 average weekday
  boardings, consistent with PRT's known ~130–135k pre-pandemic weekday
  ridership. Tract count (394) matches Analysis 46.
- **Scope checked.** Only 26 service / 35 boardings stops fall outside all
  Allegheny tracts — a small, expected edge effect (stops just over county/state
  lines).
- **Surprising result investigated.** Tracts with high service but zero
  boardings were traced to a data-source limitation: the bus-stop-usage dataset
  excludes light rail (1 rail stop present vs 98 in the network). The service
  metric was restricted to bus service to match, and rail-served tracts are
  flagged rather than silently treated as poorly-used.
- **Direction of effects checked.** Service-vs-density and boardings-vs-density
  correlations are both positive, consistent with Analysis 46; the near-zero
  boardings-vs-population correlation is explained by census tracts being drawn
  to roughly equal population.
- **Ecological framing** applied throughout — results describe tracts, not
  individuals.
