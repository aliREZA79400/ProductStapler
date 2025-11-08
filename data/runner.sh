#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Argument Parsing ---


# Default is to run the pipeline.
RUN_PIPELINE="true"
if [[ "${1:-}" == "--skip-pipeline" ]]; then
    RUN_PIPELINE="false"
fi

# --- Environment Setup ---

# during container startup.
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export PIPELINE_EXTRACT=false
export RUN_PIPELINE="$RUN_PIPELINE"

export MONGO_URI="${MONGO_URI:-mongodb://root:example@mongodb:27017/?authSource-admin}"

echo "--- Runtime Configuration ---"
echo "RUN_PIPELINE: $RUN_PIPELINE"
echo "MONGO_URI: $MONGO_URI"
echo "------------------------------"


mkdir -p /app/data/digikala/original_data /app/data/digikala/logs

# --- Execution ---

if [ "$RUN_PIPELINE" = "true" ]; then
    echo "RUN_PIPELINE is true. Starting the data pipeline..."
    # Assumes the command is run from the WORKDIR /app
    python -m data.pipeline
    echo "Pipeline execution finished."
else
    echo "RUN_PIPELINE is false; skipping data.pipeline. Sleeping indefinitely."
    # Keeps the container running so you can `exec` into it for debugging.
    sleep infinity
fi
