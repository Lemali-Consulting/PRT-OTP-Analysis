# Findings: Scheduled Trips ETL

## Summary
Scheduled trip and pick-period tables are loaded into `prt.db` for overlap months with OTP coverage.

## Notes
- Route matching and overlap diagnostics are emitted during execution.
- Cached files under `data/wprdc-schedule/` are used when available.
