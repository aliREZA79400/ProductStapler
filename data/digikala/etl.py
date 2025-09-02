import asyncio
import json
import logging
import os
from datetime import datetime

import aiofiles
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, OperationFailure

from ..util.logger import setup_logger

# --- Configuration ---
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "digikal"
PRODUCTS_COLLECTION = "products"
COMMENTS_COLLECTION = "comments"

# TODO
# def get_last_file_names(comments: bool = False):


PRODUCTS_FILE = "products.json"
COMMENTS_FILE = "comments.json"

# --- Setup logger ---
# Get the current date and time
current_time = datetime.now()

# Format the date and time into a string suitable for a filename
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Construct the log filename
log_filename = f"logs/prduct_ex_{timestamp}.log"

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the full path for the log file
log_file_path = os.path.join(script_dir, log_filename)

logger = setup_logger("Product_Extractor", log_file_path=log_file_path)


async def setup_database_schemas(db: motor.motor_asyncio.AsyncIOMotorDatabase):
    """
    Applies JSON Schema validation rules to the MongoDB collections.
    This ensures data integrity at the database level.
    """
    logging.info("Applying database schema validation rules...")

    # --- Products Schema ---
    product_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "prduct_id",
                "title_en",
                "brand",
                "category",
                "specifications",
            ],
            "properties": {
                "prduct_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "title_en": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "title_fa": {
                    "bsonType": "string",
                    "description": "must be a string",
                },
                "brand": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "category": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "price": {
                    "bsonType": "number",
                    "description": "must be a number",
                },
                "rate": {"bsonType": "number", "description": "must be a number"},
                "count_raters": {
                    "bsonType": "int",
                    "description": "must be an integer",
                },
                "colors": {
                    "bsonType": "array",
                    "items": {"bsonType": "string"},
                    "description": "must be an array of strings",
                },
                "specifications": {
                    "bsonType": "object",
                    "description": "Must be an object containing specification groups.",
                    "patternProperties": {
                        "^.*$": {
                            "bsonType": "object",
                            "description": "Group must be an object of key-value attributes.",
                            "patternProperties": {
                                "^.*$": {
                                    "bsonType": "array",
                                    "description": "Attribute value must be an array.",
                                }
                            },
                        }
                    },
                },
                "popularity": {"bsonType": int, "description": "must be an integrity"},
                "num_questions": {
                    "bsonType": "int",
                    "description": "must be a string",
                },
                "num_comments": {
                    "bsonType": "int",
                    "description": "must be a string",
                },
                "num_sellers": {
                    "bsonType": "int",
                    "description": "must be a string",
                },
                "suggestions": {
                    "bsonType": "array",
                    "items": "int",
                    "description": "an array of integers",
                },
                "comments_overview": {
                    "bsonType": "object",
                    "description": "key-value object (overview , advantages , disadvantages)",
                },
                "images": {"bsonType": "array", "items": {"bsonType": "string"}},
            },
        }
    }

    # --- Comments Schema ---
    # Ensures every comment is linked to a product and has essential text content.
    comment_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["product_id", "text"],
            "properties": {
                "product_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "title": {"bsonType": "string"},
                "text": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "reactions": {
                    "bsonType": "array",
                    "description": "an array with two value first like and two dislike",
                },
                "created_at": {
                    "bsonType": "date",
                    "description": "must be a valid BSON date and is required",
                },
                "is_buyer": {
                    "bsonType": "bool",
                    "description": "True is buyer and vice versa",
                },
                "rating": {"bsonType": "int", "minimum": 1, "maximum": 5},
                "color": {"bsonType": "string"},
                "seller": {"bsonType": "string"},
                "advantages": {"bsonType": "string"},
                "disadvantages": {"bsonType": "string"},
                "images": {"bsonType": "array", "items": {"bsonType": "string"}},
            },
        }
    }

    # Apply the validators to the collections
    try:
        await db.command("collMod", PRODUCTS_COLLECTION, validator=product_validator)
        await db.command("collMod", COMMENTS_COLLECTION, validator=comment_validator)
        logging.info("Successfully applied schema validation to collections.")
    except OperationFailure as e:
        # This can happen if the collections don't exist yet.
        logging.warning(
            f"Could not modify collections (they may not exist yet): {e}. Schemas will be applied on creation."
        )


async def extract_data(file_path: str) -> None:
    logging.info(f"Extracting data from {file_path}...")
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to extract data: {e}")
        return None


def transform_product(raw_data: dict) -> list[UpdateOne]:
    logging.info("Transforming product data...")
    operations = []
    for _, product_list in raw_data.items():
        for item in product_list:
            doc_id = item.get("id")
            if not all(
                [
                    doc_id,
                    item.get("title_en"),
                    item.get("brand"),
                    item.get("category"),
                    item.get("price") is not None,
                ]
            ):
                logging.warning(
                    f"Skipping product with missing required fields: {doc_id or 'N/A'}"
                )
                continue

            document = {
                "title_fa": item.get("title_fa"),
                "title_en": item.get("title_en"),
                "brand": item.get("brand"),
                "category": item.get("category"),
                "colors": item.get("colors", []),
                "specifications": item.get("specifications", {}),
                "rate": item.get("rate"),
                "count_raters": item.get("count_raters"),
                "price": item.get("price"),
                "product_badges": item.get("product_badges", []),
                "suggestions": item.get("suggestions", []),
                "num_comments": item.get("num_comments"),
                "num_questions": item.get("num_questions"),
                "num_sellers": item.get("num_sellers"),
                "review": item.get("review", {}),
                "comments_overview": item.get("comments_overview", []),
                "expert_reviews": item.get("expert_reviews", []),
                "images": item.get("images", []),
            }
            operations.append(
                UpdateOne({"_id": doc_id}, {"$set": document}, upsert=True)
            )
    return operations


# is better BulkWrite of UpdateMany over UpdateOne ?


async def load_products(
    collection: AsyncIOMotorCollection, operations: list[UpdateOne]
) -> int:
    logging.info(f"Loading {len(operations)} product operations into DB...")
    try:
        result = await collection.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count
        logging.info(
            f"✅Load complete. Upserted: {result.upserted_count}, Modified: {result.modified_count}."
        )
        return count
    except (BulkWriteError, Exception) as e:
        logging.error(f"Load failed: {e}")
        return 0


def transform_comments(raw_data: dict) -> tuple[list[dict], list[str]]:
    logging.info("Transforming comment data...")
    documents, product_ids_in_file = [], set()
    for brand_id, products_comments in raw_data.items():
        for product_id, comment_list in products_comments.items():
            product_ids_in_file.add(product_id)
            for item in comment_list:
                if not all([item.get("author"), item.get("text")]):
                    logging.warning(
                        f"Skipping comment for product {product_id} with missing fields."
                    )
                    continue
                item["product_id"] = product_id
                documents.append(item)
    return documents, list(product_ids_in_file)


async def load_comments(
    collection: AsyncIOMotorCollection, transformed_data: tuple[list[dict], list[str]]
) -> int:
    documents, product_ids = transformed_data
    if not documents:
        return 0

    logging.info(f"Deleting old comments for {len(product_ids)} products...")
    await collection.delete_many({"product_id": {"$in": product_ids}})

    logging.info(f"Inserting {len(documents)} new comments...")
    try:
        result = await collection.insert_many(documents, ordered=False)
        count = len(result.inserted_ids)
        logging.info(f"✅Inserted {count} new comments.")
        return count
    except (BulkWriteError, Exception) as e:
        logging.error(f"Load failed: {e}")
        return 0


async def run(self) -> int:
    raw_data = await self._extract_data()
    if not raw_data:
        return 0
    documents, product_ids = self._transform(raw_data)
    if not documents:
        logging.warning(
            f"[{self.__class__.__name__}] No documents to load after transformation."
        )
        return 0
    return await self._load((documents, product_ids))


# --- Main Orchestrator ---
async def main():
    """Initializes and runs the ETL pipelines using asyncio.wait."""
    client = None
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGO_URI, MIN_POOL_SIZE=3, MAX_POOL_SIZE=8
        )
        db = client[DB_NAME]

        # Setup collections, schemas, and indexes
        await setup_database_schemas(db)
        products_collection = db[PRODUCTS_COLLECTION]
        comments_collection = db[COMMENTS_COLLECTION]
        await comments_collection.create_index("product_id")

        # Instantiate pipelines
        product_pipeline = ProductsPipeline(PRODUCTS_FILE, products_collection)
        comment_pipeline = CommentsPipeline(COMMENTS_FILE, comments_collection)

        logging.info("--- Starting ETL Pipelines ---")

        # Create tasks for each pipeline
        product_task = asyncio.create_task(product_pipeline.run())
        comment_task = asyncio.create_task(comment_pipeline.run())
        tasks = {product_task, comment_task}

        # Use asyncio.wait for more explicit control over task completion
        done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

        logging.info("--- ETL Pipelines Finished ---")
        for task in done:
            task_name = "Products" if task is product_task else "Comments"
            try:
                result = task.result()
                logging.info(f"Pipeline '{task_name}' processed {result} documents.")
            except Exception as e:
                logging.error(f"Pipeline '{task_name}' failed with an exception: {e}")

    except Exception as e:
        logging.critical(f"A critical error occurred in the main orchestrator: {e}")
    finally:
        if client:
            client.close()
            logging.info("MongoDB connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
