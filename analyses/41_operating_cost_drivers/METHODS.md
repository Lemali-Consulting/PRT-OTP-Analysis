# Methods: Operating Cost Drivers

## Question
Where does PRT's operating cost premium come from relative to peers, and does fleet age explain the vehicle maintenance gap?

## Approach
- Pull OpExp sub-categories (VO, VM, NVM, GA) and UPT from `ntd_annual_service` for 8 peers, 2019 and 2024.
- Normalize all costs to per-trip amounts (`opexp_xx / upt`) to control for agency size.
- Pull fleet age data from `ntd_fleet_age` for 2024 (bus and light rail vehicle types).
- Scatter-plot bus average age vs vehicle maintenance cost per trip to test whether older fleets explain higher maintenance costs.
- Show cost-per-trip breakdown as stacked bars and time trends (2019–2024).

## Data
- `ntd_annual_service`: columns `ntd_id`, `year`, `upt`, `opexp_vo`, `opexp_vm`, `opexp_nvm`, `opexp_ga`.
- `ntd_fleet_age`: columns `ntd_id`, `year`, `vehicle_type`, `avg_age`, `total_vehicles`.
- Filtered to the 8 peer city NTD IDs defined in `PEERS`.

## Output
- `output/cost_breakdown.png` — stacked bar chart of per-trip cost by category for each peer (2024).
- `output/cost_change.png` — grouped bars showing 2019 vs 2024 per-trip cost by category for Pittsburgh.
- `output/fleet_age_vs_maintenance.png` — scatter plot correlating bus fleet age with vehicle maintenance cost per trip.
- `output/fleet_age_comparison.png` — bar chart of average bus and light rail fleet age per peer.
- `output/cost_trends.png` — 2×2 line chart panel showing per-trip cost trajectories by category (2019–2024).
- `output/cost_breakdown.csv` — full per-trip cost data and fleet age metrics for all peers.
