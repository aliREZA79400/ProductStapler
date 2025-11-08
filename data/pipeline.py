import asyncio
import json
import os
from datetime import datetime

from .digikala import etl as etl_module

# Use absolute imports relative to project root
from .digikala.brand_ex import Extractor as BrandExtractor
from .digikala.product_ex import ProductExtractor


def ensure_dirs() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    digikala_dir = os.path.join(script_dir, "digikala")
    original_data_dir = os.path.join(digikala_dir, "original_data")
    logs_dir = os.path.join(digikala_dir, "logs")
    os.makedirs(original_data_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    return original_data_dir


async def run_brand_extraction(timeout: int) -> dict:
    base_url = "https://api.digikala.com/v1/categories/mobile-phone/search/"
    extractor = BrandExtractor(
        base_url=base_url, query="?sort=4&page=", timeout=timeout
    )
    return await extractor.get_all_ids_by_brand()


async def run_products_and_comments(
    brands_info: dict, timeout: int
) -> tuple[list[dict], list[dict]]:
    base_url = "https://api.digikala.com/v2/product/"
    extractor = ProductExtractor(base_url=base_url, timeout=timeout)

    products = await extractor.run(brands_info=brands_info, comments=False)
    comments = await extractor.run(brands_info=brands_info, comments=True)
    return products, comments


def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


async def main():
    out_dir = ensure_dirs()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Toggle via env: when false, only ETL runs and uses existing files
    extract_flag = os.getenv("PIPELINE_EXTRACT", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if extract_flag:
        # 1) Brand IDs
        brands_info = await run_brand_extraction(timeout=120)

        brands_ts_path = os.path.join(out_dir, f"brands_info_{ts}.json")
        brands_fixed_path = os.path.join(out_dir, "brands_info_has_price.json")
        save_json(brands_info, brands_ts_path)
        save_json(brands_info, brands_fixed_path)

        # 2) Products and Comments
        products, comments = await run_products_and_comments(
            brands_info=brands_info, timeout=400
        )

        products_path = os.path.join(out_dir, f"{ts}_products.json")
        comments_path = os.path.join(out_dir, f"{ts}_comments.json")
        save_json(products, products_path)
        save_json(comments, comments_path)

    # 3) ETL (uses latest *_products.json and *_comments.json automatically)
    await etl_module.main()


if __name__ == "__main__":
    asyncio.run(main())
