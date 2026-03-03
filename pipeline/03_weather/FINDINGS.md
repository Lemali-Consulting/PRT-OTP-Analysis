# Findings: Weather ETL

## Summary
Monthly weather features are loaded into `prt.db` and validated for overlap with OTP months.

## Notes
- Uses cached raw weather CSV when present.
- Emits seasonality sanity checks and null-rate diagnostics.
