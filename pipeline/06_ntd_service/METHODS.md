# Methods: NTD Annual Service ETL

## Question

How do we make national transit service-level data (Vehicle Revenue Hours, Vehicle Revenue Miles) available for comparative analysis?

## Approach

1. Read four sheets (VRH, VRM, UPT, VOMS) from the NTD TS2.2 "Service Data by System" Excel workbook.
2. For each sheet, identify agency identifier columns and year columns (1991–2023).
3. Unpivot each sheet from wide format (one column per year) to long format (one row per agency-year).
4. Join the four metric DataFrames on `(ntd_id, year)`.
5. Attach agency identifiers (name, city, state, UZA) from the VRH sheet.
6. Write to a single `ntd_annual_service` table in `prt.db`.

## Data

| Name | Description | Source |
|------|-------------|--------|
| `2023_TS2.2_Service_Data.xlsx` | NTD TS2.2 workbook with annual service metrics by system | FTA National Transit Database (`data/ntd-annual-service/`) |

## Output

| Name | Description |
|------|-------------|
| `ntd_annual_service` | SQLite table in `prt.db`: annual VRH, VRM, UPT, VOMS per agency (1991–2023) |
