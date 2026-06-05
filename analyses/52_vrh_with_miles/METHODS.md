# Methods: VRH and Vehicle Revenue Miles

## Question

How has PRT's operating speed (vehicle revenue miles per vehicle revenue hour) changed over time, and does that speed vary by mode? Specifically, has bus speed declined in recent years — a signal of growing traffic congestion or service restructuring — relative to light rail and paratransit?

## Approach

1. Load monthly VRH and VRM from `ntd_ridership` for PRT (ntd_id = 30022) for 2002–2024.
2. Aggregate to annual totals by mode.
3. Compute average operating speed in miles per hour: `mph = vrm / vrh` (only where `vrh > 0`).
4. Plot speed (mph) by mode over time — one line per mode — to reveal trends.
5. Plot indexed VRH and VRM for each mode (base = 2019 = 100) to show whether hours and miles diverged post-pandemic.
6. Produce a summary table of mph at key years (2007, 2019, 2024) and percent change.
7. Exclude the Incline (IP) from speed comparisons because its extremely short track and near-vertical geometry make the mph figure uninformative for congestion analysis.

## Data

- **`ntd_ridership`** (`ntd_id`, `mode`, `month`, `vrh`, `vrm`): PRT-only rows filtered to modes MB, LR, DR, IP.
- Rows with `vrh IS NULL` or `vrh = 0` are excluded from speed calculations.
- Calendar year aggregates: sum VRH and VRM across all months for a given mode-year.

## Output

- `output/speed_by_mode.csv` — annual VRH, VRM, and mph by mode (2002–2024)
- `output/speed_trends.png` — time-series of mph by mode (bus, rail, paratransit), 2002–2024
- `output/vrh_vrm_index.png` — indexed VRH and VRM for each mode (2019 = 100)
- `output/mode_speed_summary.csv` — mph at key years and % change 2019→2024
