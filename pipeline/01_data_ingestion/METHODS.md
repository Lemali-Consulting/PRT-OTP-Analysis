# Methods: Data Ingestion

## Question
How do we reproducibly build a normalized SQLite database used by all analyses?

## Approach
1. Read canonical CSV sources from `data/`.
2. Normalize and reshape route, stop, OTP, and ridership records.
3. Rebuild `data/prt.db` with expected tables and constraints.
4. Emit basic verification output (row counts and sanity checks).

## Data
- `data/routes_by_month.csv`
- `data/PRT_Current_Routes_Full_System_de0e48fcbed24ebc8b0d933e47b56682.csv`
- `data/Transit_stops_(current)_by_route_e040ee029227468ebf9d217402a82fa9.csv`
- `data/PRT_Stop_Reference_Lookup_Table.csv`
- `data/average-ridership/12bb84ed-397e-435c-8d1b-8ce543108698.csv`

## Output
- `data/prt.db` -- normalized SQLite database for downstream analyses.
- Console verification logs (table counts and sample diagnostics).
