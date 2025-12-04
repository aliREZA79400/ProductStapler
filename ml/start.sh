#!/bin/bash

# Start cron service
service cron start

# Keep cron running in the background and start MLflow server
exec mlflow server \
    --backend-store-uri file:/app/mlruns \
    --default-artifact-root file:/app/mlartifacts \
    --host 0.0.0.0 \
    --port 5000

