FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIPELINE_EXTRACT=false

# Build-time switch to control whether to run the pipeline at container start
ARG RUN_PIPELINE=true
ENV RUN_PIPELINE=${RUN_PIPELINE}

WORKDIR /app

# System deps (curl for debugging, build essentials rarely needed for our deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy only what we need
COPY data /app/data

# Install Python dependencies from requirements.txt
COPY data/requirements.txt /app/data/requirements.txt
RUN pip install --no-cache-dir -r /app/data/requirements.txt

# Default environment (override in compose)
ENV MONGO_URI="mongodb://root:example@mongodb:27017/?authSource=admin"

# Persist outputs and logs
VOLUME ["/app/data/digikala/original_data", "/app/data/digikala/logs"]

# Conditionally run the pipeline based on RUN_PIPELINE
CMD ["/bin/sh", "-c", "if [ \"$RUN_PIPELINE\" = \"true\" ]; then python -m data.pipeline; else echo 'RUN_PIPELINE is false; skipping data.pipeline'; sleep infinity; fi"]


