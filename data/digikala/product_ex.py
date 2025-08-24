import asyncio
from rnet import Client, Impersonate
from datetime import datetime
import os
from ..util.logger import setup_logger
from ..util.async_timer import async_time
import aiofiles
import json
from typing import Dict, Union

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


@async_time()
async def fetch_brand(
    base_url: str, brand_id: Union[int, str], product_ids: list, timeout: int
):
    logger.debug(f"Fetching the Brand {brand_id}")

    client = Client(impersonate=Impersonate.Firefox136, timeout=timeout)
    semaphore = asyncio.Semaphore(5)

    @async_time()
    async def fetch_product(client: Client, base_url: str, product_id: int):
        async with semaphore:
            res = await client.get(url=f"{base_url}{product_id}/", timeout=timeout)
            # TODO comments & questions & comments
            try:
                result = await res.json()
                return result["data"]["product"]

            except json.JSONDecodeError as e:
                logger.error(f"Josn decode error for {product_id} with {e} ")
            except Exception as e:
                logger.error(f"Unxpected error {e} status code {res.status}")

    tasks = [
        asyncio.create_task(fetch_product(client, base_url, product_id=pid))
        for pid in product_ids
    ]

    done, pending = await asyncio.wait(tasks, timeout=timeout)

    logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

    all_products_of_brand = {brand_id: list()}
    for task in done:
        try:
            all_products_of_brand[brand_id].append(task.result())
        except Exception as e:
            logger.error(f"Found error {e} when processing the product ")

    logger.info(f"{brand_id} Fetched")

    return all_products_of_brand


@async_time()
async def main(base_url: str, brands_info: Dict, timeout: int):
    tasks = [
        asyncio.create_task(fetch_brand(base_url, brand_id, product_ids, timeout))
        for brand_id, product_ids in brands_info.items()
        if len(product_ids) != 0
    ]
    done, pending = await asyncio.wait(tasks, timeout=timeout)

    logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

    all_products = list()

    for task in done:
        try:
            all_products.append(task.result())
        except Exception as e:
            logger.error(f"Found error {e} when processing a brand")

    logger.info("Completed")

    print(len(all_products))

    file_name = f"data/digikala/original_data/{timestamp}.json"

    async with aiofiles.open(file_name, "w") as f:
        await f.write(json.dumps(all_products, indent=4))


# from .brand_ex import Extractor

# URL = "https://api.digikala.com/v1/categories/mobile-phone/search/"

# e = Extractor(base_url=URL, query="?sort=4&page=", timeout=100)

# brands_info = asyncio.run(e.get_all_ids_by_brand())

file_path = "data/digikala/brands_info.json"
try:
    with open(file_path, "r") as f:
        brands_info = json.load(f)
except Exception as e:
    print(f"File not found and accure erroe {e} ")
    brands_info = None

BASE_URL = "https://api.digikala.com/v2/product/"

asyncio.run(main(base_url=BASE_URL, brands_info=brands_info, timeout=400))
