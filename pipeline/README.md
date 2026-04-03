# Pipeline

Numbered ingestion steps that create and refresh project data assets. Pipeline scripts may write to `data/` and database tables, while analyses remain read-only consumers.

Run steps in numeric order, or use `uv run python scaffold.py run-all`.

## Current Steps

1. `01_data_ingestion`
2. `02_scheduled_trips`
3. `03_weather`
4. `04_traffic_overlay`
5. `05_ntd_ridership`
6. `06_ntd_service`
7. `07_otp_null_classification`
8. `08_allegheny_go`

