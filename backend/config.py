from decouple import config

MONGO_URI = config("MONGO_URI")
DB_NAME = config("DB_NAME")
PRODUCTS_COLLECTION = config("PRODUCTS_COLLECTION")
USERS_COLLECTION = config("USERS_COLLECTION")

SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default="30"))

# Parse KEYS_TO_SHOW from comma-separated string
KEYS_TO_SHOW_STR = config("KEYS_TO_SHOW", default="")
KEYS_TO_SHOW = [key.strip() for key in KEYS_TO_SHOW_STR.split(",") if key.strip()] if KEYS_TO_SHOW_STR else []