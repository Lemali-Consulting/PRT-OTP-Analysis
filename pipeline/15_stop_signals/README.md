# 15 - Stop Signals ETL

Ingests PRT's authoritative bus-stop signal classification (near-side / far-side /
no-signal at traffic signals) from a PRT-provided spreadsheet into the `stop_signals`
table in `prt.db`, resolving each stop_code to its GTFS stop_id for downstream joins.
