import asyncio
import json
import os
from datetime import datetime
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
from .etl import run_products_etl , run_comments_etl
import argparse
import logging


if ENABLE_LOGGING:
    # --- Setup logger ---
    # Get the current date and time
    current_time = datetime.now()

    # Format the date and time into a string suitable for a filename
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    # Construct the log filename
    log_filename = f"logs/Pipeline_{timestamp}.log"

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the full path for the log file
    log_file_path = os.path.join(script_dir, log_filename)

    logger = setup_logger("Pipeline", log_file_path=log_file_path)
else : 
    logger = logging.getLogger("Pipeline")


def ensure_dirs() -> str:
    original_data_dir = os.path.join("data/original_data")
    os.makedirs(original_data_dir, exist_ok=True)
    logger.info(f"Ensured directory: {original_data_dir}")
    return original_data_dir


async def run_brand_extraction(timeout: int, url: str, query: str) -> dict:
    extractor = BrandExtractor(base_url=url, query=query, timeout=timeout)
    try:
        return await extractor.get_all_ids_by_brand()
    except Exception as e:
        logger.error(f"Error in run_brand_extraction: {e}")
        raise


async def run_product_extractor(
    products_base_url: str, timeout: int, brands_info: dict ,state:str=None ,comments_base_url: str = None
) -> tuple[list[dict], list[dict]]:
    extractor = ProductExtractor(base_url=products_base_url, timeout=timeout, state=state ,comments_base_url=comments_base_url)
    try:
        return await extractor.run(brands_info=brands_info)
    except Exception as e:
        logger.error(f"Error in run_product_extractor: {e}")
        raise



def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        logger.info(f"Saved JSON data to {path}")


async def products_main():

    out_dir = ensure_dirs()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 1) Brand IDs
    brands_info = await run_brand_extraction(timeout=TIMEOUT, url=URL, query=QUERY)
    brands_path = os.path.join(out_dir, f"brands_info_{current_time}.json")
    save_json(brands_info, brands_path)
    logger.info(f"Saved brands info to {brands_path}")


    # 2) Products 
    products = await run_product_extractor(
        products_base_url=PRODUCT_BASE_URL, timeout=TIMEOUT, brands_info=brands_info,state="Products"
    )
    products_path = os.path.join(out_dir, f"Products_{current_time}.json")
    save_json(products, products_path)
    logger.info(f"Saved products info to {products_path}")
    
    # ETL for products
    return await run_products_etl(
        mongo_uri=MONGO_URI,
        product_path=products_path,
        db_name=DB_NAME,
        products_collection=PRODUCTS_COLLECTION,
    )


async def comments_main():
    
    out_dir = ensure_dirs()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 1) Brand IDs
    brands_info = await run_brand_extraction(timeout=TIMEOUT, url=URL, query=QUERY)
    brands_path = os.path.join(out_dir, f"brands_info_{current_time}.json")
    save_json(brands_info, brands_path)
    logger.info(f"Saved brands info to {brands_path}")


    # 2) Products 
    comments = await run_product_extractor(
        products_base_url=PRODUCT_BASE_URL, timeout=TIMEOUT, brands_info=brands_info , state="Comments" , comments_base_url=COMMENTS_BASE_URL
    )
    comments_path = os.path.join(out_dir, f"Comments_{current_time}.json")
    save_json(comments, comments_path)
    logger.info(f"Saved comments info to {comments_path}")
    
    # ETL for products
    return await run_comments_etl(
        mongo_uri=MONGO_URI,
        comments_path=comments_path,
        db_name=DB_NAME,
        comments_collection=COMMENTS_COLLECTION,
    )


def main(argv=None):
    """
    Entry point for CLI. Accepts an optional argv list (for testability).
    """
    parser = argparse.ArgumentParser(description="ETL Pipeline for Products and Comments")
    parser.add_argument(
        "--stage",
        type=str,
        choices=["Products", "Comments"],
        default="Products",
        help="Specify the ETL stage to run: 'Products' or 'Comments'. Default is 'Products'.",
    )
    args = parser.parse_args(argv)

    if args.stage == "Products":
        asyncio.run(products_main())
    elif args.stage == "Comments":
        asyncio.run(comments_main())


if __name__ == "__main__":
    main()

