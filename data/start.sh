#!/bin/bash
set -euo pipefail

export PREFECT_HOST="${PREFECT_HOST:-0.0.0.0}"
export PREFECT_PORT="${PREFECT_PORT:-4200}"
export PREFECT_API_URL="${PREFECT_API_URL:-http://localhost:4200/api}"
export PREFECT_HEALTH_ENDPOINT="${PREFECT_HEALTH_ENDPOINT:-${PREFECT_API_URL%/}/health}"

echo "Starting Prefect Server on ${PREFECT_HOST}:${PREFECT_PORT}..."
prefect server start --host "${PREFECT_HOST}" --port "${PREFECT_PORT}" &
server_pid=$!

cleanup() {
  echo "Stopping Prefect Server..."
  kill "$server_pid" >/dev/null 2>&1 || true
}
trap cleanup SIGINT SIGTERM

echo "Waiting for Prefect API at ${PREFECT_HEALTH_ENDPOINT}..."
python3 - <<'PY'
import os
import time
import urllib.request
from urllib.error import URLError, HTTPError

endpoint = os.environ["PREFECT_HEALTH_ENDPOINT"]
for attempt in range(60):
    try:
        with urllib.request.urlopen(endpoint, timeout=2) as resp:
            if resp.getcode() == 200:
                print("Prefect API is ready.")
                break
    except (URLError, HTTPError) as exc:
        print(f"Prefect API not ready yet ({exc}). Retrying...")
        time.sleep(2)
else:
    raise SystemExit("Prefect API did not become ready in time.")
PY

echo "Starting data pipeline serve stage..."
python3 -m data.pipeline --stage serve "$@"