# Methods: Monongahela Incline Investigation

## Question
The Monongahela Incline may have zero or missing OTP data. Is this a data pipeline artifact, or was OTP never measured for the Incline?

## Approach
- Query the `otp_monthly` table for both incline route_ids ('MI' and 'DQI') and examine all values.
- Check if 'MI' appears in `route_stops` and what stops are associated.
- Check the `routes` table for mode and name (including all INCLINE-mode routes).
- Cross-reference with the `stop_reference` table for historical Incline stops.
- Summarize findings as a data quality report.

## Data
- `otp_monthly` -- any MI records
- `routes` -- MI metadata
- `route_stops` -- MI stop associations
- `stops` -- physical Incline stops
- `stop_reference` -- historical Incline stops

## Output
- `output/incline_report.csv` -- all data found for MI across tables
- `output/incline_report.txt` -- plain-text summary of findings
