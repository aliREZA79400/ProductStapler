FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  PYTHONPATH=/app

WORKDIR /app

RUN rm -rf /var/lib/apt/lists/*

COPY data/requirements.txt ./data/requirements.txt

RUN python -m pip install --upgrade pip -r ./data/requirements.txt  

COPY data ./data
COPY .env_data ./
EXPOSE 4200

VOLUME ["/app/data/original_data", "/app/data/logs"]

CMD ["/bin/bash", "data/start.sh"]

