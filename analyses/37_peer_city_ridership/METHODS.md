# Methods: Peer City Ridership Comparison

## Question
How does Pittsburgh's ridership trajectory and post-pandemic recovery compare to 7 peer cities from 2019 through 2025?

## Approach
- Select 8 peer transit agencies by NTD ID: Pittsburgh (30022), Baltimore (30034), Cleveland (50015), Denver (80006), St. Louis (70006), Buffalo (20004), Portland (8), Minneapolis (50027).
- Sum monthly UPT across all modes and TOS per agency, Jan 2019–Dec 2025.
- Index each agency's monthly total to its 2019 monthly average (= 100) to normalize for size.
- Plot indexed ridership trajectories for all 8 peers.
- Compute 2024 vs 2019 recovery percentage for each peer.
- Break down recovery by mode (bus vs rail) where the agency operates both.

## Data
- `ntd_ridership` — monthly UPT by agency/mode/TOS, filtered to Jan 2019–Dec 2025.
- `ntd_agency` — agency names and mode codes.

## Output
- `output/peer_ridership_indexed.png` — time-series line chart of indexed ridership for all 8 peers.
- `output/peer_recovery_bar.png` — bar chart of 2024 vs 2019 recovery %, PRT highlighted.
- `output/peer_mode_breakdown.png` — bus vs rail recovery by peer city.
- `output/peer_ridership_data.csv` — monthly indexed data for all peers.
- `output/peer_recovery_summary.csv` — per-peer recovery metrics.
