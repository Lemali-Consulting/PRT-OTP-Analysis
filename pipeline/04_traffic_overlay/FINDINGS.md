# Findings: Traffic Overlay ETL

## Summary
Route-level traffic exposure metrics are computed from PennDOT AADT segments and written to `prt.db`.

## Notes
- Matching diagnostics include segment counts and route match rates.
- Cached PennDOT responses are reused when available.
