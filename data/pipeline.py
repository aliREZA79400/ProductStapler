import asyncio
import json
import os
from datetime import datetime
import argparse
import logging

# --- PREFECT IMPORTS ---
from prefect import flow, task
# REMOVED: from prefect.schedules import Schedule, Interval (Not used in Prefect 3.x)

# --- LOCAL IMPORTS (Assumed correct based on your context) ---
from .brand_ex import Extractor as BrandExtractor
from .product_ex import ProductExtractor
from .config import (
    URL,
    QUERY,
    TIMEOUT,
    ENABLE_LOGGING,
    PRODUCT_BASE_URL,
    COMMENTS_BASE_URL,
    COMMENTS_COLLECTION,
    DB_NAME,
    MONGO_URI,
    PRODUCTS_COLLECTION,
)
from .util.logger import setup_logger
from .etl import run_products_etl, run_comments_etl


# --- LOGGING SETUP ---
if ENABLE_LOGGING:
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"logs/Pipeline_{timestamp}.log"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(script_dir, log_filename)
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logger = setup_logger("Pipeline", log_file_path=log_file_path)
else:
    logger = logging.getLogger("Pipeline")


def ensure_dirs() -> str:
    original_data_dir = os.path.join("data/original_data")
    os.makedirs(original_data_dir, exist_ok=True)
    logger.info(f"Ensured directory: {original_data_dir}")
    return original_data_dir


# --- ASYNC HELPERS ---


async def run_brand_extraction(timeout: int, url: str, query: str) -> dict:
    extractor = BrandExtractor(base_url=url, query=query, timeout=timeout)
    try:
        return await extractor.get_all_ids_by_brand()
    except Exception as e:
        logger.error(f"Error in run_brand_extraction: {e}")
        raise


async def run_product_extractor(
    products_base_url: str,
    timeout: int,
    brands_info: dict,
    state: str = "",
    comments_base_url: str = "",
) -> tuple[list[dict], list[dict]]:
    extractor = ProductExtractor(
        base_url=products_base_url,
        timeout=timeout,
        state=state,
        comments_base_url=comments_base_url,
    )
    try:
        return await extractor.run(brands_info=brands_info)
    except Exception as e:
        logger.error(f"Error in run_product_extractor: {e}")
        raise


def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        logger.info(f"Saved JSON data to {path}")


# --- MANUAL RUN FUNCTIONS ---


async def products_main():
    """Manual execution logic without Prefect tasks (optional, strictly for manual debugging)"""
    out_dir = ensure_dirs()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 1) Brand IDs
    brands_info = await run_brand_extraction(timeout=TIMEOUT, url=str(URL), query=QUERY)
    brands_path = os.path.join(out_dir, f"brands_info_{current_time}.json")
    save_json(brands_info, brands_path)
    logger.info(f"Saved brands info to {brands_path}")

    # 2) Products
    products = await run_product_extractor(
        products_base_url=PRODUCT_BASE_URL,
        timeout=TIMEOUT,
        brands_info=brands_info,
        state="Products",
    )
    products_path = os.path.join(out_dir, f"Products_{current_time}.json")
    save_json(products, products_path)
    logger.info(f"Saved products info to {products_path}")

    # ETL
    return await run_products_etl(
        mongo_uri=MONGO_URI,
        product_path=products_path,
        db_name=DB_NAME,
        products_collection=PRODUCTS_COLLECTION,
    )


async def comments_main():
    """Manual execution logic for comments"""
    out_dir = ensure_dirs()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    brands_info = await run_brand_extraction(timeout=TIMEOUT, url=str(URL), query=QUERY)
    brands_path = os.path.join(out_dir, f"brands_info_{current_time}.json")
    save_json(brands_info, brands_path)

    comments = await run_product_extractor(
        products_base_url=PRODUCT_BASE_URL,
        timeout=TIMEOUT,
        brands_info=brands_info,
        state="Comments",
        comments_base_url=COMMENTS_BASE_URL,
    )
    comments_path = os.path.join(out_dir, f"Comments_{current_time}.json")
    save_json(comments, comments_path)

    return await run_comments_etl(
        mongo_uri=MONGO_URI,
        comments_path=comments_path,
        db_name=DB_NAME,
        comments_collection=COMMENTS_COLLECTION,
    )


# --- PREFECT TASKS & FLOW ---


@task
async def extract_brands_task():
    return await run_brand_extraction(timeout=TIMEOUT, url=str(URL), query=QUERY)


@task
async def extract_products_task(brands_info: dict):
    return await run_product_extractor(
        products_base_url=PRODUCT_BASE_URL,
        timeout=TIMEOUT,
        brands_info=brands_info,
        state="Products",
    )


@task
async def save_json_task(obj, path: str):
    save_json(obj, path)


@task
async def run_etl_task(
    mongo_uri: str, product_path: str, db_name: str, products_collection: str
):
    return await run_products_etl(
        mongo_uri=mongo_uri,
        product_path=product_path,
        db_name=db_name,
        products_collection=products_collection,
    )


@flow(log_prints=True)
async def products_pipeline_flow():
    """
    Prefect flow for the products ETL pipeline.
    """
    out_dir = ensure_dirs()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 1) Brand IDs
    brands_info = await extract_brands_task()
    brands_path = os.path.join(out_dir, f"brands_info_{current_time}.json")
    await save_json_task(brands_info, brands_path)
    logger.info(f"Saved brands info to {brands_path}")

    # 2) Products
    products = await extract_products_task(brands_info)
    products_path = os.path.join(out_dir, f"Products_{current_time}.json")
    await save_json_task(products, products_path)
    logger.info(f"Saved products info to {products_path}")

    # ETL
    await run_etl_task(
        mongo_uri=MONGO_URI,
        product_path=products_path,
        db_name=DB_NAME,
        products_collection=PRODUCTS_COLLECTION,
    )


# --- ENTRY POINT ---


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="ETL Pipeline for Products and Comments"
    )
    parser.add_argument(
        "--stage",
        type=str,
        choices=["Products", "Comments", "serve"],
        default="Products",
        help="Specify the ETL stage to run: 'Products', 'Comments', or 'serve'.",
    )
    args = parser.parse_args(argv)

    if args.stage == "Products":
        asyncio.run(products_main())
    elif args.stage == "Comments":
        asyncio.run(comments_main())
    elif args.stage == "serve":
        # PREFECT 3.X SCHEDULING LOGIC
        # We call .serve() on the flow function itself.
        # cron="0 2 * * *" means "At minute 0 of hour 2 (2:00 AM) every day".
        # Prefect handles timezone via UTC by default unless specified otherwise.
        products_pipeline_flow.serve(
            name="daily-products-pipeline",
            cron="0 2 * * *",
            tags=["etl", "daily"],
        )


if __name__ == "__main__":
    main()
