# Methods: Stop Signals ETL

## Question
Which PRT bus stops sit at a signalized intersection, and are they near-side or
far-side of the signal?

## Approach
1. Read the PRT-provided spreadsheet (`bus_stops_with_signals_2602.xlsx`), one row
   per bus stop with a `mode` tag.
2. Map each `mode` to a canonical `signal_class`: `none`, `nearside`, `farside`, or
   `busway` (dedicated busway/BRT right-of-way, not a street signal).
3. Derive `has_signal` (true only for near-side / far-side stops).
4. Resolve each PRT `stop_code` to its GTFS `stop_id` via the `stops` table so the
   classification can join to `route_stops`, `otp_monthly`, and census geography.
5. Drop and rebuild the `stop_signals` table in `prt.db`.

## Data
- `data/prt-stop-signals/bus_stops_with_signals_2602.xlsx` (PRT, Samuel Buckley, 2026)
- `stops` table in `prt.db` (stop_code → GTFS stop_id crosswalk)

## Output
- `stop_signals` table in `data/prt.db`
