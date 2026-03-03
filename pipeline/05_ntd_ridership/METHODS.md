# Methods: NTD Ridership ETL

## Question
How do we load national monthly ridership benchmarks into the project database?

## Approach
1. Read agency dimension rows from NTD workbook Master sheet.
2. Unpivot monthly UPT values from wide to long format.
3. Normalize month keys to `YYYY-MM`.
4. Rebuild `ntd_agency` and `ntd_ridership` tables in `prt.db`.

## Data
- NTD monthly ridership workbook in `data/ntd-monthly-ridership/`

## Output
- `ntd_agency` table in `data/prt.db`
- `ntd_ridership` table in `data/prt.db`
