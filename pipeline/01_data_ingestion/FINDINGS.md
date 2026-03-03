# Findings: Data Ingestion

## Summary
The ingestion step rebuilds `data/prt.db` from source CSV inputs and validates expected core tables.

## Notes
- This step is deterministic for a fixed set of input files.
- Analyses assume this database exists and is readable.
