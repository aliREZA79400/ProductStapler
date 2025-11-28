from decouple import config

URL = config("URL")
QUERY = str(config("QUERY"))
TIMEOUT = int(config("TIMEOUT"))
ENABLE_LOGGING = bool(int((config("ENABLE_LOGGING"))))
COMMENTS_BASE_URL = str(config("COMMENTS_BASE_URL"))
PRODUCT_BASE_URL = str(config("PRODUCT_BASE_URL"))

MONGO_URI = str(config("MONGO_URI"))
DB_NAME = str(config("DB_NAME"))
CHUNK_SIZE = int(config("CHUNK_SIZE"))
PRODUCTS_COLLECTION = str(config("PRODUCTS_COLLECTION"))
COMMENTS_COLLECTION = str(config("COMMENTS_COLLECTION"))