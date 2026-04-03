# Methods: Peer City Dashboard

## Question
How does PRT compare to peer cities across ridership recovery, service supply, and fare burden — and do these dimensions tell a consistent story about Pittsburgh's post-pandemic transit trajectory?

## Approach
- Pull 2019 and 2023 annual data for 8 peer cities from `ntd_annual_service`.
- Compute percent change (2019→2023) for ridership (UPT), service hours (VRH), and fare revenue.
- Compute derived metrics: fare per trip (`fares / upt`), farebox recovery ratio (`fares / opexp`), and cost per trip (`opexp / upt`).
- Visualize changes as grouped bars with Pittsburgh highlighted, and derived metrics as paired 2019-vs-2023 bars.
- Combine key views into a multi-panel dashboard figure.

## Data
- `ntd_annual_service`: columns `ntd_id`, `year`, `upt`, `vrh`, `fares`, `opexp`.
- Filtered to `year IN (2019, 2023)` and the 8 peer city NTD IDs defined in `PEERS`.
- No null handling needed — all 8 peers have complete data for both years.

## Output
- `output/peer_comparison.csv` — full metrics table with raw values, percent changes, and derived ratios for all peers.
- `output/peer_dashboard.png` — 2×2 multi-panel figure: percent changes, fare per trip, farebox recovery, and cost per trip.
- `output/indexed_change.png` — grouped bar chart showing percent change in ridership, service hours, and fare revenue side-by-side per city.
- `output/fare_per_trip.png` — paired bars (2019 vs 2023) for fare revenue per unlinked trip.
- `output/farebox_recovery.png` — paired bars (2019 vs 2023) for farebox recovery ratio.
