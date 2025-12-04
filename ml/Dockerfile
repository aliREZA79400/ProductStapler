FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MLFLOW_SERVER_ALLOWED_HOSTS=mlflow,localhost,127.0.0.1,*



COPY ml/requirements.txt ./ml/requirements.txt
RUN python -m pip install --upgrade pip --no-cache-dir \
    && pip install -r ml/requirements.txt \
    && apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY ml/ ./ml/

# Copy and set up cron job
RUN mkdir -p /var/log
COPY ml/crontab /etc/cron.d/model-cron
RUN chmod 0644 /etc/cron.d/model-cron \
    && crontab /etc/cron.d/model-cron \
    && touch /var/log/model_cron.log

# Make startup script executable
RUN chmod +x ml/start.sh

# Optional: fix permissions if needed

EXPOSE 5000

VOLUME ["/app/mlruns", "/app/mlartifacts"]

CMD ["/bin/bash", "ml/start.sh"]
