# Stapler

## Automated Data Pipeline

- `docker compose up -d data-pipeline` builds and starts the recurring Digikala ingestion/ETL job. The service depends on `mongodb` availability.
- The scheduler defaults to running every three days (`PIPELINE_INTERVAL_DAYS=3`). Override with environment variables or `docker compose run -e PIPELINE_INTERVAL_DAYS=1 data-pipeline`.
- The runner script supports three modes via `RUN_MODE`: `scheduler` (default recurring), `pipeline` (single run, exits), and `idle` (no-op, keeps container alive). You can also pass `--once` to the container entrypoint.
- Persistent artifacts are stored in named volumes `data_original_data` and `data_logs`, ensuring raw snapshots and ETL logs survive container restarts.
- Relevant environment knobs: `PIPELINE_INITIAL_DELAY_SECONDS` (offset start), `PIPELINE_EXTRACT` (skip extraction and reuse latest files), `PIPELINE_RUN_ON_START` (skip the first immediate run).
