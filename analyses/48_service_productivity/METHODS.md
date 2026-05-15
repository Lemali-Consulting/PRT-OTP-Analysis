# Methods: Service Productivity (Passengers per Revenue Hour)

## Question
Has PRT's service productivity — the number of passengers carried per hour of
service operated — declined over time? And if so, is the decline because
ridership fell faster than service was cut (emptier buses) rather than a
deliberate right-sizing of service to match demand?

## Approach
- Define service productivity as unlinked passenger trips per vehicle revenue
  hour: `productivity = UPT / VRH`. This is the standard transit efficiency
  ratio — how many riders each hour of operated service actually carried.
- Pull the full 1991–2024 annual record of UPT and VRH for PRT and 7 peer
  cities from `ntd_annual_service`.
- Plot PRT's productivity curve across the whole record to separate the
  long-run secular trend from the COVID shock.
- Decompose the ratio: index UPT, VRH, and productivity to 1991 = 100 on one
  chart. If VRH (supply) holds roughly flat while UPT (demand) collapses, the
  productivity decline is demand-driven — empty buses — not a supply-side
  right-sizing.
- Normalize the demand side by population. Allegheny County (PRT's service
  area) has lost residents since 1991, so part of the ridership decline could
  simply be fewer people. Split ridership into `UPT = population x
  trips-per-capita` and partition the 1991→2024 ridership decline between the
  two factors using log shares: `share = ln(factor ratio) / ln(UPT ratio)`.
  This isolates how much of the drop is fewer residents versus each resident
  riding less.
- Benchmark PRT against peers two ways: a 2024 cross-section ranking, and the
  full 1991–2024 trajectory for all 8 cities.
- Report percent change in productivity over the full period (1991→2024) and
  over the post-pandemic window (2019→2024) for every peer.

## Data
- `ntd_annual_service`: columns `ntd_id`, `year`, `upt` (unlinked passenger
  trips), `vrh` (vehicle revenue hours).
- Filtered to the 8 peer-city NTD IDs in `PEERS`; PRT is `ntd_id = 30022`.
- All 8 agencies have complete, non-null UPT and VRH for every year 1991–2024
  (34 city-years each, 272 rows total) — verified before analysis, so no null
  handling is required.
- Allegheny County population (`COUNTY_POPULATION` in `main.py`): U.S. Census
  Bureau decennial counts for 1990 (1,336,449), 2000, 2010, and 2020
  (1,250,578), plus the Census Bureau's Vintage 2024 Population Estimates
  Program figure (1,231,809). The 1990 decennial count is used as the 1991
  population anchor — a ~9-month offset. Population is paired with the NTD
  record only at these census/estimate years; no annual interpolation is done.

## Output
- `output/prt_productivity_by_year.csv` — PRT UPT, VRH, and productivity for
  every year 1991–2024.
- `output/peer_productivity.csv` — productivity at 1991, 2019, and 2024 for all
  8 peers, with percent change over both windows.
- `output/prt_productivity_trend.png` — PRT productivity line, 1991–2024.
- `output/supply_vs_demand_decomposition.png` — PRT UPT, VRH, and productivity
  indexed to 1991 = 100.
- `output/peer_productivity_2024.png` — horizontal bar ranking of 2024
  productivity across the 8 peers, PRT highlighted.
- `output/peer_productivity_trends.png` — productivity trajectories 1991–2024
  for all 8 peers, PRT highlighted.
- `output/per_capita_decomposition.csv` — Allegheny County population, PRT UPT,
  VRH, productivity, and ridership per resident at 1991, 2000, 2010, 2020, 2024.
- `output/per_capita_normalization.png` — county population, total ridership,
  and ridership per resident indexed to 1991 = 100.
