#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Argument Parsing ---


RUN_MODE="${RUN_MODE:-scheduler}" # allowed: scheduler|pipeline|idle
if [[ "${1:-}" == "--once" ]]; then
    RUN_MODE="pipeline"
elif [[ "${1:-}" == "--idle" ]]; then
    RUN_MODE="idle"
fi

# --- Environment Setup ---

# during container startup.
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PIPELINE_EXTRACT="${PIPELINE_EXTRACT:-true}"
export MONGO_URI="${MONGO_URI:-mongodb://root:example@mongodb:27017/?authSource=admin}"

echo "--- Runtime Configuration ---"
echo "RUN_MODE: $RUN_MODE"
echo "MONGO_URI: $MONGO_URI"
echo "------------------------------"


mkdir -p /app/data/digikala/original_data /app/data/digikala/logs

# --- Execution ---

case "$RUN_MODE" in
    "pipeline")
        echo "Running data pipeline once..."
        exec python -m data.pipeline
        ;;
    "scheduler")
        echo "Starting scheduler (recurring pipeline runs)..."
        exec python -m data.scheduler
        ;;
    *)
        echo "RUN_MODE=idle; sleeping indefinitely for debugging."
        sleep infinity
        ;;
esac
