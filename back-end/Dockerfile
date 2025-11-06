FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MONGO_URI=mongodb://root:example@mongodb:27017/?authSource=admin \
    DB_NAME=digikala \
    PRODUCTS_COLLECTION=products


COPY back-end/ ./back-end/

RUN pip install --no-cache-dir -r /app/back-end/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "back-end.main:app", "--host", "0.0.0.0", "--port", "8000"]