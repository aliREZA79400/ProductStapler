from decouple import config
import mlflow

MLFLOW_TRACKING_URI = str(config("MLFLOW_TRACKING_URI"))
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

MONGO_URI = config("MONGO_URI")
DB_NAME = config("DB_NAME")
PRODUCTS_COLLECTION = config("PRODUCTS_COLLECTION")


MODEL_NAME = config("MODEL_NAME")
MODEL_VERSION = config("MODEL_VERSION")

