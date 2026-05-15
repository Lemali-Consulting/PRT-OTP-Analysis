# Methods: Bus vs. Rail — Productivity by Mode

## Question
Analysis 48 found that PRT's agency-wide service productivity — passengers
carried per hour of service operated (UPT / VRH) — has roughly halved, to about
18 passengers per revenue hour in 2024. But that single number blends four very
different services: the motor bus network, the light rail "T", the door-to-door
ACCESS paratransit service, and the Monongahela Incline. This analysis splits
the agency figure apart. How productive is each mode? Is the low agency average
dragged down by one service? And has the post-2019 decline hit bus and rail
equally?

## Approach
- Define productivity exactly as Analysis 48 does — unlinked passenger trips per
  vehicle revenue hour, `productivity = UPT / VRH` — but compute it per mode
  instead of agency-wide.
- Pull PRT's monthly UPT and VRH by mode from `ntd_ridership` and aggregate to
  calendar years. The four NTD mode codes map to: `MB` = Motor Bus, `LR` = Light
  Rail, `DR` = Paratransit (demand-response ACCESS service), `IP` = Incline.
- Compute productivity only for mode-years with reported VRH > 0. The NTD
  Monthly Module does not report VRH for `DR` or `IP` before 2007, so their
  productivity series begin in 2007; `MB` and `LR` have a complete VRH record
  from 2002. Mode-years without VRH are left null, never treated as zero.
- Build two roll-ups: **fixed-route** (`MB` + `LR`, the conventional bus + rail
  network) and **all-mode** (every mode, which reproduces the agency-wide figure
  of Analysis 48). The all-mode series is reported only for 2007–2024, the span
  where every mode has VRH.
- Compare modes three ways: a 2024 productivity snapshot, the 2019→2024 change
  (the COVID window used by Analysis 48), and each mode's 2024 share of trips
  versus its share of revenue hours — which exposes whether a mode consumes
  service out of proportion to the riders it carries.
- Reconcile the all-mode 2024 figure against Analysis 48's 18.3, which is built
  from a different NTD source (the annual TS2.2 workbook).

## Data
- `ntd_ridership`: columns `ntd_id`, `mode`, `tos`, `month`, `upt`, `vrh`.
  Filtered to `ntd_id = 30022` (PRT). Monthly records summed to calendar years
  2002–2024. The `vrh` and `vrm` columns were added to this table specifically
  to support a per-mode productivity breakdown — the agency-level
  `ntd_annual_service` table used by Analysis 48 cannot be split by mode.
- The `IP` mode has two type-of-service records (`IP/DO` and `IP/PT`); the
  purchased-transportation record ends in 2012. Summing UPT and VRH across both
  records for each month combines them into one Incline series.

## Output
- `output/mode_productivity_by_year.csv` — UPT, VRH, and productivity for every
  mode and calendar year 2002–2024.
- `output/mode_summary.csv` — per mode (plus fixed-route and all-mode roll-ups):
  productivity at 2002/2007, 2019, and 2024, the 2019→2024 percent change, and
  the 2024 shares of trips and revenue hours.
- `output/mode_productivity_trends.png` — productivity by mode, 2002–2024.
- `output/mode_productivity_2024.png` — bar ranking of 2024 productivity by
  mode, with the fixed-route and all-mode roll-ups marked.
- `output/service_vs_ridership_2024.png` — each mode's share of 2024 trips
  versus its share of 2024 revenue hours.
- `output/productivity_decline_2019_2024.png` — productivity by mode in 2019
  versus 2024.
