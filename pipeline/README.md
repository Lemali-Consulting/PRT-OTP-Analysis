# Pipeline

Numbered ingestion steps that create and refresh project data assets. Pipeline scripts may write to `data/` and database tables, while analyses remain read-only consumers.

Run steps in numeric order, or use `uv run python scaffold.py run-all`.
