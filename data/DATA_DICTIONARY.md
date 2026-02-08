# Data Dictionary

## Overview

Pittsburgh Regional Transit (PRT) on-time performance and system data, normalized into a SQLite database.

| Property       | Value                            |
|----------------|----------------------------------|
| Database       | `data/prt.db` (SQLite)           |
| Built by       | `src/prt_otp_analysis/build_db.py` |
| Rebuild        | `uv run python src/prt_otp_analysis/build_db.py` |

## Database Schema

| Table            | Rows    | Description                              |
|------------------|---------|------------------------------------------|
| `routes`         | 105     | Dimension: one row per route             |
| `stops`          | 6,466   | Dimension: one row per physical stop     |
| `route_stops`    | 11,078  | Bridge: which stops serve which routes   |
| `stop_reference` | 7,554   | Dimension: historical stop reference     |
| `otp_monthly`    | 7,651   | Fact: monthly on-time performance        |

### `routes`

| Column      | Type | Description                          |
|-------------|------|--------------------------------------|
| `route_id`  | TEXT PK | Route code (`"1"`, `"P1"`, `"BLUE"`) |
| `route_name`| TEXT | Human-readable name                   |
| `mode`      | TEXT | `BUS`, `RAIL`, `INCLINE`, or `UNKNOWN` (for historical routes) |

### `stops`

| Column    | Type    | Description                     |
|-----------|---------|---------------------------------|
| `stop_id` | TEXT PK | PRT stop identifier             |
| `stop_code`| INTEGER| Numeric stop code               |
| `stop_name`| TEXT   | Stop name                       |
| `lat`     | REAL    | Latitude                        |
| `lon`     | REAL    | Longitude                       |
| `county`  | TEXT    | County                          |
| `muni`    | TEXT    | Municipality                    |
| `hood`    | TEXT    | Neighborhood (nullable)         |

### `route_stops`

| Column      | Type    | Description                     |
|-------------|---------|---------------------------------|
| `route_id`  | TEXT FK | References `routes.route_id`    |
| `stop_id`   | TEXT FK | References `stops.stop_id`      |
| `direction` | TEXT    | `"IB"`, `"OB"`, or `"IB,OB"`   |
| `trips_wd`  | INTEGER | Weekday trips                   |
| `trips_sa`  | INTEGER | Saturday trips                  |
| `trips_su`  | INTEGER | Sunday trips                    |
| `trips_7d`  | INTEGER | Total weekly trips              |
| `svc_days`  | TEXT    | Service days (e.g. `"WD,SA,SU"`)|

Primary key: `(route_id, stop_id, direction)`

### `stop_reference`

Historical stop lookup table -- all stops ever in the PRT system.

| Column       | Type    | Description                     |
|--------------|---------|---------------------------------|
| `stop_id`    | TEXT PK | PRT stop identifier             |
| `stop_code`  | INTEGER | Numeric stop code               |
| `stop_name`  | TEXT    | Stop name                       |
| `stop_source`| TEXT    | GTFS feed that introduced it    |
| `public_stop`| TEXT    | `"yes"` / `"no"`                |
| `lat`        | REAL    | Latitude                        |
| `lon`        | REAL    | Longitude                       |
| `mode`       | TEXT    | BUS, INCLINE, etc.              |
| `first_served`| TEXT   | First GTFS feed version code    |
| `last_served` | TEXT   | Last GTFS feed version code     |
| `county`     | TEXT    | County                          |
| `muni`       | TEXT    | Municipality                    |
| `hood`       | TEXT    | Neighborhood (nullable)         |

### `otp_monthly`

| Column    | Type    | Description                     |
|-----------|---------|---------------------------------|
| `route_id`| TEXT FK | References `routes.route_id`    |
| `month`   | TEXT    | `"2019-01"` through `"2025-12"` |
| `otp`     | REAL    | On-time percentage, 0.0 -- 1.0  |

Primary key: `(route_id, month)`. Rows with NULL OTP in the source CSV are excluded.

## Route ID Reconciliation

Route codes are extracted from `routes_by_month.csv` by splitting on `" - "` (first token).

| Mapping | Notes |
|---------|-------|
| `MONONGAHELA INCLINE` -> `MI` | Name used in OTP data maps to system code |
| `37`, `42`, `P2`, `RLSH`, `SWL` | In OTP data only (historical/temporary routes) |
| `DQI`, `Y1`, `Y45`--`Y49` | In current system only (no OTP data) |

## Source Files

| File | Rows | Feeds into |
|------|------|------------|
| `routes_by_month.csv` | 99 routes x 84 months | `routes`, `otp_monthly` |
| `Transit_stops_(current)_by_route_*.csv` | 17,546 | `stops`, `route_stops` |
| `PRT_Current_Routes_Full_System_*.csv` | 277 | `routes` |
| `PRT_Stop_Reference_Lookup_Table.csv` | 7,554 | `stop_reference` |
| `Transit_stops_*.geojson` | 17,546 | Not used (same data as stops CSV) |

---

## Source File: routes_by_month.csv

## Fields

| Column         | Type   | Description                                                                 |
|----------------|--------|-----------------------------------------------------------------------------|
| `Route`        | Text   | Route identifier and name (e.g. `"1 - FREEPORT ROAD"`, `"P1 - EAST BUSWAY-ALL STOPS"`) |
| `YYYY-Mon`     | Float  | On-Time Percentage for that route in that month, scaled 0.0 to 1.0          |

### Route naming conventions

Routes follow several naming patterns that reflect service type:

| Pattern              | Example                                      | Service type         |
|----------------------|----------------------------------------------|----------------------|
| Number only          | `1 - FREEPORT ROAD`                          | Local bus             |
| Number + `L`         | `51L - CARRICK LIMITED`                       | Limited-stop bus      |
| Number + `X`         | `28X - AIRPORT FLYER`                         | Express bus           |
| `P` prefix           | `P1 - EAST BUSWAY-ALL STOPS`                 | Busway / flyer        |
| `O` prefix           | `O1 - ROSS FLYER`                            | Flyer (express)       |
| `G` prefix           | `G2 - WEST BUSWAY`                           | Busway               |
| Color name           | `RED - Castle Shannon via Beechview`          | Light rail (T)        |
| `SLVR`               | `SLVR - Libary via Overbrook`                | Light rail (T)        |
| `BLUE`               | `BLUE - SouthHills Village via Overbrook`    | Light rail (T)        |
| Special              | `MONONGAHELA INCLINE`, `RLSH - Red Line Shuttle`, `SWL - Outbound to SHJ` | Incline / shuttle |

### OTP value

Each numeric cell represents the **On-Time Percentage** for a route in a given month.

| Property       | Value               |
|----------------|---------------------|
| Data type      | Float (or empty)    |
| Range          | 0.0 -- 1.0          |
| Interpretation | 0.0 = 0%, 1.0 = 100%|
| Example        | 0.6912 = 69.12% on-time |

## Known ambiguities and data quality notes

### 1. "On-time" definition is unspecified
The dataset does not define what threshold constitutes "on-time." Transit industry standards vary:
- Common definition: a vehicle is on-time if it departs **0 to 5 minutes late** (and not early)
- PRT may use a different window (e.g. 1 minute early to 5 minutes late)
- It is unclear whether OTP is measured at all stops, timepoints only, or at origin/destination

### 2. Empty cells are ambiguous
Many cells are blank. Possible reasons include:
- **Route did not exist** during that period (e.g. `37 - CASTLE SHANNON` only has Jan--Mar 2024)
- **Route was temporarily suspended** (e.g. COVID-era service reductions)
- **Data was not collected or reported** for that month
- **Route was discontinued** (e.g. `P2 - EAST BUSWAY SHORT` data ends after Sep 2023)

There is no sentinel value or flag to distinguish these cases.

### 3. Sparse or short-lived routes
Several routes have very limited data, suggesting they were introduced, discontinued, or are seasonal:

| Route                        | Data months | Notes                                  |
|------------------------------|-------------|----------------------------------------|
| `37 - CASTLE SHANNON`        | 3           | Only Jan--Mar 2024                      |
| `42 - POTOMAC`               | 3           | Only Jan--Mar 2024                      |
| `53 - HOMESTEAD PARK`        | 2           | Only Jan--Feb 2020                      |
| `78 - MONONGAHELA INCLINE`   | 0           | Row present but all values empty        |
| `88 - P2 - EAST BUSWAY SHORT`| 56          | Data ends after Sep 2023                |
| `98 - RLSH - Red Line Shuttle`| 3          | Only Jan--Mar 2024                      |
| `100 - SWL - Outbound to SHJ`| ~12         | Sparse data, mostly 2024               |

### 4. Potential outliers or anomalies
Some values appear as sharp drops that may indicate data quality issues rather than true performance:
- `15 - CHARLES`: drops to ~0.35 in Jul--Sep 2022, then rebounds to ~0.80 (possible measurement change or route restructuring)
- `65 - SQUIRREL HILL`: drops to 0.28--0.37 range in mid-2023, far below its historical norm
- `SWL - Outbound to SHJ`: value of **0.2097** in Dec 2024 (single-month anomaly amid ~0.88--0.90 values)
- `39 - BROOKLINE`: drops to 0.4000 in Mar 2022, otherwise consistently 0.72--0.89
- `7 - SPRING GARDEN`: value of **0.2863** in Aug 2025, far below its historical range

### 5. Data source is undocumented
- The dataset does not specify where the OTP values originate (e.g. AVL/APC systems, manual reporting, GTFS-realtime)
- It is unclear whether these are PRT self-reported figures or independently calculated
- Aggregation method is unknown (simple average across all trips? weighted by ridership?)

### 6. Trailing comma
Each data row ends with a trailing comma, which may produce an extra empty column when parsed. Parsers should account for this.

### 7. Typo in source data
`SLVR - Libary via Overbrook` appears to be a misspelling of "Library."
