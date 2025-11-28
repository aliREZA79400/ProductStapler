import asyncio
import json
import os
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Dict, List, Tuple
import logging
import aiofiles
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, OperationFailure

from .util.logger import setup_logger
from .config import CHUNK_SIZE , PRODUCTS_COLLECTION , COMMENTS_COLLECTION , ENABLE_LOGGING , MONGO_URI , DB_NAME

NUM_PROCESSES = os.cpu_count() or 1


if ENABLE_LOGGING:
    # --- Setup logger ---
    # Get the current date and time
    current_time = datetime.now()

    # Format the date and time into a string suitable for a filename
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    # Construct the log filename
    log_filename = f"logs/ETL_{timestamp}.log"

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the full path for the log file
    log_file_path = os.path.join(script_dir, log_filename)

    logger = setup_logger("ETL Pipeline", log_file_path=log_file_path)
else : 
    logger = logging.getLogger("ETL Pipeline")


def find_latest_file(base_dir: str, file_type: str) -> str | None:
    """
    Finds the path to the latest file of a specific type
    in a given directory based on the timestamp in its name.

    Args:
        base_dir: The directory to search in.
        file_type: The type of file to find (e.g., "Products" or "Comments").

    Returns:
        The full path to the latest file, or None if no file is found.
    """
    if not os.path.isdir(base_dir):
        logger.error(f"Directory not found: {base_dir}")
        return None

    try:
        # Get a list of all files in the directory
        all_files = os.listdir(base_dir)

        # Filter for files that match the naming convention
        # e.g., "2025-08-24_16-36-04_Products.json"
        matching_files = [f for f in all_files if f.startswith(f"{file_type}_") and f.endswith(".json")]

        if not matching_files:
            logger.warning(f"No files of type '{file_type}' found.")
            return None

        # Sort the files by their timestamp in descending order
        # The timestamp is the first part of the filename
        matching_files.sort(
            key=lambda f: f.split("_")[0] + f.split("_")[1], reverse=True
        )

        # The first file in the sorted list is the latest
        latest_file = matching_files[0]

        logger.info(f"Found latest '{file_type}' file: {latest_file}")
        return os.path.join(base_dir, latest_file)

    except OSError as e:
        logger.error(f"Error accessing directory: {e}")
        return None


script_dir = os.path.dirname(os.path.abspath(__file__))


async def setup_database_schemas(db: motor.motor_asyncio.AsyncIOMotorDatabase):
    """
    Applies JSON Schema validation rules to the MongoDB collections.
    This ensures data integrity at the database level.
    """
    logger.info("Applying database schema validation rules...")

    # --- Products Schema ---
    product_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "_id",
                "title_en",
                "brand",
                "category",
                "specifications",
            ],
            "properties": {
                "_id": {
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
                "popularity": {"bsonType": int, "description": "must be an integer"},
                "num_questions": {
                    "bsonType": "int",
                    "description": "must be a string",
                },
                "num_comments": {
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
            "required": ["product_id", "body"],
            "properties": {
                "product_id": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "title": {"bsonType": "string"},
                "body": {
                    "bsonType": "string",
                    "description": "must be a string and is required",
                },
                "likes": {
                    "bsonType": "int",
                    "description": "must be integer",
                },
                "dislikes": {
                    "bsonType": "int",
                    "description": "must be integer",
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
        logger.info("Successfully applied schema validation to collections.")
    except OperationFailure as e:
        # This can happen if the collections don't exist yet.
        logger.warning(
            f"Could not modify collections (they may not exist yet): {e}. Schemas will be applied on creation."
        )


def transform_products(raw_chunc: list[dict]) -> list[UpdateOne]:
    def _get_colors(item: list | None) -> list:
        if item is None:
            return []
        else:
            return [dic["title"] for dic in item]

    def _get_images(item: dict | None) -> list[str]:
        if item is None:
            return []
        images = []
        try:
            main = item.get("main")
            if main is not None:
                images.append(main.get("url")[0])
        except KeyError as e:
            logger.error(f"Error in extracting main image of product {e}")
        try:
            ims = item.get("list")
            if ims is not None:
                for im in ims:
                    images.append(im.get("url")[0])
        except KeyError as e:
            logger.error(f"Error in extracting images of product {e}")
        return images

    def _general_get(item, inner_key: str, outer_key: str):
        if item is None or isinstance(item, list):
            return None
        try:
            value = item.get(outer_key)
            if value is not None:
                return value.get(inner_key)
        except KeyError as e:
            logger.error(f"Error extracting {outer_key, inner_key} with {e}")

    logger.info("Transforming product data...")
    operations = []
    for item in raw_chunc:
        doc_id = item.get("id")

        # Treat empty dicts/lists as present (e.g., brand={}, specifications={})
        # Only skip when a required value is missing or explicitly None
        required_present = [
            doc_id is not None,
            item.get("title_en") is not None,
            item.get("brand") is not None,
            item.get("category") is not None,
            item.get("specifications") is not None,
        ]
        if not all(required_present):
            logger.warning(
                f"Skipping product with missing required fields: {doc_id or 'N/A'}"
            )
            continue

        document = {
            "title_fa": item.get("title_fa"),
            "title_en": item.get("title_en"),
            "brand": _general_get(item, "code", "brand"),
            "category": _general_get(item, "code", "category"),
            "colors": _get_colors(item.get("colors", None)),
            "specifications": item.get("specifications", []),
            "rate": _general_get(item, "rate", "rating"),
            "count_raters": _general_get(item, "count", "rating"),
            "price": _general_get(
                item.get("default_variant", None), "selling_price", "price"
            ),
            "popularity": len(item.get("product_badges", [])),
            "suggestions": item.get("suggestion", {}),
            "num_comments": item.get("comments_count", 0),
            "num_questions": item.get("questions_count", 0),
            "comments_overview": item.get("comments_overview", []),
            "images": _get_images(item.get("images", None)),
        }
        operations.append(UpdateOne({"_id": doc_id}, {"$set": document}, upsert=True))
    return operations


def transform_comments(raw_chunk: list) -> Tuple[List[Dict], List[str]]:
    """Synchronous comments transformation for a single chunk."""

    def _general_get_comment(
        item, outer_key, inner_key=None
    ) -> int | str | list | None:
        if item is None:
            return None
        try:
            outer_value = item.get(outer_key)
            if outer_value is not None and (inner_key is None):
                return outer_value
            elif outer_value is not None and (inner_key is not None):
                return outer_value.get(inner_key)
        except KeyError as e:
            logger.error(f"Error in extracting {outer_key, inner_key} with error {e}")

    def _get_images(item) -> List:
        if item is not None:
            images = []
            for im in item:
                images.append(im.get("url")[0])
        else:
            return []
        return images

    documents, product_ids = [], set()

    # The raw_chunk is a list of dictionaries, where each dict has product_id and other keys
    for item in raw_chunk:
        product_id = item.get("product_id")
        if not product_id:
            continue

        product_ids.add(product_id)

        # Create a new document for the comment
        comment_doc = {
            # _id; store product_id explicitly
            "product_id": product_id,
            "title": _general_get_comment(item, "title"),
            "body": _general_get_comment(item, "body"),
            "rate": _general_get_comment(item, "rate"),
            "advantages": _general_get_comment(item, "advantages"),
            "disadvantages": _general_get_comment(item, "disadvantages"),
            "is_buyer": _general_get_comment(item, "is_buyer"),
            "created_at": _general_get_comment(item, "created_at"),
            "color": _general_get_comment(
                _general_get_comment(item, "purchased_item"), "color", "title"
            ),
            "seller": _general_get_comment(
                _general_get_comment(item, "purchased_item"), "seller", "title"
            ),
            "likes": _general_get_comment(item, "reactions", "likes"),
            "dislikes": _general_get_comment(item, "reactions", "dislikes"),
            "images": _get_images(_general_get_comment(item, "files")),
        }
        documents.append(comment_doc)

    return documents, list(product_ids)


# --- Asynchronous I/O and Orchestrating Functions ---
async def extract_product_in_chunks(file_path: str):
    """Asynchronously extracts data from a file and yields it in chunks."""
    logger.info(f"Starting async chunked extraction from {file_path}...")
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            raw_data = json.loads(content)

            # This logic flattens the nested dictionary into a list of documents
            flat_list = []
            for product in raw_data:
                for _, product_list in product.items():
                    for item in product_list:
                        flat_list.append(item)

            logger.info(f"Flattened {len(flat_list)} total products.")

            for i in range(0, len(flat_list), CHUNK_SIZE):
                yield flat_list[i : i + CHUNK_SIZE]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to extract data: {e}")
        return


async def extract_comments_in_chunks(file_path: str):
    """
    Asynchronously extracts comments from a file and yields it in chunks.
    This version handles the dictionary-of-lists structure of the comments JSON.
    """
    logger.info(f"Starting async chunked extraction from {file_path}...")
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            raw_data = json.loads(content)

            # The JSON is a dictionary with numeric string keys
            # and each value is a list of comment dicts.

            flat_list = []
            # comments structure are list of dict and each dict have key and its value
            # that is a list of list and each inner list
            # contains comments of a product
            for brand in raw_data:
                for brand_key, brand_comments in brand.items():
                    for cl in brand_comments:
                        # use logical AND, and ensure we only extend with iterables
                        if isinstance(cl, list) and cl is not None:
                            flat_list.extend(cl)
                        else:
                            logger.warning(
                                f"Unexpected data type for key {brand_key}: {type(cl)}"
                            )

            logger.info(f"Flattened {len(flat_list)} total comments.")

            # Now, yield chunks from the flattened list
            for i in range(0, len(flat_list), CHUNK_SIZE):
                yield flat_list[i : i + CHUNK_SIZE]

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to extract data: {e}")
        return


async def load_products(
    collection: AsyncIOMotorCollection, operations: list[UpdateOne]
) -> int:
    logger.info(f"Loading {len(operations)} product operations into DB...")
    try:
        result = await collection.bulk_write(operations, ordered=False)
        count = result.upserted_count + result.modified_count
        logger.info(
            f"✅Load complete. Upserted: {result.upserted_count}, Modified: {result.modified_count}."
        )
        return count
    except (BulkWriteError, Exception) as e:
        logger.error(f"Load failed: {e}", exc_info=True)
        return 0


async def load_comments(
    collection: AsyncIOMotorCollection, transformed_data: tuple[list[dict], list[str]]
) -> int:
    documents, product_ids = transformed_data
    if not documents:
        return 0

    logger.info(f"Deleting old comments for {len(product_ids)} products...")
    await collection.delete_many({"product_id": {"$in": product_ids}})

    logger.info(f"Inserting {len(documents)} new comments...")
    try:
        result = await collection.insert_many(documents, ordered=False)
        count = len(result.inserted_ids)
        logger.info(f"✅Inserted {count} new comments.")
        return count
    except (BulkWriteError, Exception) as e:
        logger.error(f"Load failed: {e}", exc_info=True)
        return 0


async def _process_chunk_async(chunk, transform_func, load_func, collection, executor):
    """
    An asynchronous worker task to handle a single chunk's transformation and loading.
    """
    # 1. Transform the chunk in a separate process (CPU-bound)
    loop = asyncio.get_running_loop()
    transformed_chunk = await loop.run_in_executor(executor, transform_func, chunk)

    # 2. Load the transformed chunk asynchronously (I/O-bound)
    loaded_count = await load_func(collection, transformed_chunk)

    return loaded_count


async def run_chunked_pipeline_concurrently(
    file_path, collection, transform_func, load_func, executor, state: str
):
    """
    Runs a fully concurrent ETL pipeline using a producer-consumer model.
    """
    logger.info(f"Starting fully concurrent pipeline for {collection.name}...")

    chunk_generator = None
    try:
        match state:
            case "comment":
                chunk_generator = extract_comments_in_chunks(file_path)
            case "product":
                chunk_generator = extract_product_in_chunks(file_path)
    except Exception as e:
        logger.error(f"Error {e}")
        return None

    if not chunk_generator:
        logger.error("Chunk generator could not be created.")
        return None

    tasks = []
    async for chunk in chunk_generator:
        task = asyncio.create_task(
            _process_chunk_async(chunk, transform_func, load_func, collection, executor)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    total_loaded = sum(results)
    logger.info(f"Total documents loaded for {collection.name}: {total_loaded}")
    return total_loaded


# --- Separate ETL Functions ---
async def run_products_etl(mongo_uri: str, product_path: str,db_name: str ,products_collection: str):
    """Runs ETL pipeline for products only."""
    executor = ProcessPoolExecutor(max_workers=NUM_PROCESSES)
    client = None
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        products_collection = db[products_collection]

        await run_chunked_pipeline_concurrently(
            product_path,
            products_collection,
            transform_products,
            load_products,
            executor,
            state="product",
        )

    except Exception as e:
        logger.error(f"A critical error occurred in products ETL: {e}", exc_info=True)
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed.")
        if executor:
            executor.shutdown(wait=True)


async def run_comments_etl(mongo_uri: str, comments_path: str, db_name: str , comments_collection: str):
    """Runs ETL pipeline for comments only."""
    executor = ProcessPoolExecutor(max_workers=NUM_PROCESSES)
    client = None
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        comments_collection = db[comments_collection]

        await run_chunked_pipeline_concurrently(
            comments_path,
            comments_collection,
            transform_comments,
            load_comments,
            executor,
            state="comment",
        )

    except Exception as e:
        logger.error(f"A critical error occurred in comments ETL: {e}", exc_info=True)
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed.")
        if executor:
            executor.shutdown(wait=True)


# --- Main Orchestrator / Example Usage---
async def main():
    """Initializes and runs the ETL pipelines concurrently."""
    executor = ProcessPoolExecutor(max_workers=NUM_PROCESSES)
    client = None
    try:
        # Discover latest input files now (pipeline may have created them just before)
        products_path = find_latest_file(base_dir="./original_data", file_type="Products")
        # comments_path = find_latest_file(base_dir="./original_data", file_type="Comments")

        # if not products_path:
        #     logger.error("No products file found. Ensure the extractor has generated *_products.json.")
        # if not comments_path:
        #     logger.error("No comments file found. Ensure the extractor has generated *_comments.json.")
        print(MONGO_URI)
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        products_collection = db[PRODUCTS_COLLECTION]
        # comments_collection = db[COMMENTS_COLLECTION]

        # Start both pipelines concurrently
        products_task = asyncio.create_task(
            run_chunked_pipeline_concurrently(
                products_path,
                products_collection,
                transform_products,
                load_products,
                executor,
                state="product",
            )
        )

        # comments_task = asyncio.create_task(
        #     run_chunked_pipeline_concurrently(
        #         comments_path,
        #         comments_collection,
        #         transform_comments,
        #         load_comments,
        #         executor,
        #         state="comment",
        #     )
        # )

        await asyncio.gather(products_task)

    #   await setup_database_schemas(db)
    except Exception as e:
        logger.error(f"A critical error occurred: {e}", exc_info=True)
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed.")
        if executor:
            executor.shutdown(wait=True)


if __name__ == "__main__":
    asyncio.run(main())
