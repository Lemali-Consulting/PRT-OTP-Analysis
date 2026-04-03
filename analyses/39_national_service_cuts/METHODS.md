# Methods: National Service Cuts (2019 vs 2024)

## Question

How much service have the largest US transit agencies cut since 2019, where does PRT rank, and how does supply-side service change compare to demand-side ridership change?

## Approach

1. Load annual VRH (Vehicle Revenue Hours) and UPT (Unlinked Passenger Trips) from `ntd_annual_service` for 2019 and 2024.
2. Filter to agencies with non-null VRH in both years.
3. Rank agencies by 2019 VRH (descending) and take the top 150 to match Analysis 36's size-based approach.
4. Compute percent change in VRH and UPT for each agency.
5. Rank PRT nationally by VRH percent change (best recovery = rank 1).
6. Compare PRT to 7 peer cities (Baltimore, Cleveland, Denver, St. Louis, Buffalo, Portland, Minneapolis) on both VRH and UPT change.
7. Plot year-by-year VRH and UPT trajectories (indexed to 2019 = 100) for all 8 peer cities to reveal recovery shape and timing.
8. Classify agencies into quadrants based on whether they lost more service (VRH) or more riders (UPT) relative to each other.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `ntd_annual_service` | Annual VRH, VRM, UPT, VOMS per agency (1991–2024) | `prt.db` table (pipeline 06, TS2.2 2023+2024 editions) |

## Output

| File | Description |
|------|-------------|
| `service_cuts_distribution.png` | Histogram of VRH % change across 150 agencies, PRT highlighted |
| `service_cuts_ranking.png` | Horizontal bar chart ranking 150 agencies by VRH % change |
| `peer_service_vs_ridership.png` | Grouped bars: VRH change vs UPT change for 8 peer cities |
| `peer_trajectory.png` | Side-by-side line charts: VRH and UPT indexed to 2019=100 for 8 peer cities |
| `supply_vs_demand_scatter.png` | Scatter plot: VRH change (x) vs UPT change (y) for top 150, with y=x diagonal |
| `service_cuts_data.csv` | Per-agency data with VRH and UPT changes and ranks |
