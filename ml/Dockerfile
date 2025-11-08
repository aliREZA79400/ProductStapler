FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MLFLOW_SERVER_ALLOWED_HOSTS=mlflow,localhost,127.0.0.1,*



COPY ml/requirements.txt ./ml/requirements.txt
RUN python -m pip install --upgrade pip --no-cache-dir \
    && pip install -r ml/requirements.txt

COPY ml/ ./ml/


# Optional: fix permissions if needed

EXPOSE 5000

VOLUME ["/app/mlruns", "/app/mlartifacts"]

CMD ["mlflow", "server", \
    "--backend-store-uri", "file:/app/mlruns", \
    "--default-artifact-root", "file:/app/mlartifacts", \
    "--host", "0.0.0.0", \
    "--port", "5000"]
