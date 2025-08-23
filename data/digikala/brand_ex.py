import asyncio
from rnet import Impersonate, Client
from typing import Set
from datetime import datetime
import os

from ..util.async_timer import async_time
from ..util.logger import setup_logger

# Get the current date and time
current_time = datetime.now()

# Format the date and time into a string suitable for a filename
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Construct the log filename
log_filename = f"extractor_ids_{timestamp}.log"

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the full path for the log file
log_file_path = os.path.join(script_dir, log_filename)

logger = setup_logger("Mobile_Ids_Extractor", log_file_path=log_file_path)


class Extractor:
    def __init__(self, base_url, query, timeout) -> None:
        self.base_url = base_url
        self.query = query
        self.client = Client(impersonate=Impersonate.Firefox139, timeout=timeout)
        self.timeout = timeout

    @async_time()
    async def get_total_pages(self) -> int:
        req = await self.client.get(url=self.base_url)
        total = await req.json()
        total = total["data"]["pager"]["total_pages"]
        logger.info(f"Found {total} pages")
        return total

    @async_time()
    async def get_all_ids(self) -> Set:
        total_pages = await self.get_total_pages()

        semaphore = asyncio.Semaphore(5)

        @async_time()
        async def fetch_page(num_page):
            async with semaphore:
                try:
                    req = await self.client.get(
                        url=f"{self.base_url}{self.query}{num_page}"
                    )
                    res = await req.json()
                    products = res["data"]["products"]
                    return {product["id"] for product in products}
                except Exception as e:
                    logger.error(
                        f"Error fetching page {num_page} with {e}", exc_info=True
                    )
                    return set()

        tasks = [asyncio.create_task(fetch_page(i)) for i in range(1, total_pages + 1)]
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)

        logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        all_mobile_ids = set()

        for task in done:
            try:
                all_mobile_ids.update(task.result())
            except Exception as e:
                logger.error(f"Error processing task with {e}")
        logger.info(f"Found {len(all_mobile_ids)}")

        return all_mobile_ids

    @async_time()
    async def get_all_brands(self):
        req = await self.client.get(url=self.base_url)
        res = await req.json()
        brands = res["data"]["filters"]["brands"]["options"]
        all_brands = {(brand["id"], brand["code"]) for brand in brands}
        return all_brands

    @async_time()
    async def get_total_pages_of_each_brand(self, brand_id):
        req = await self.client.get(url=f"{self.base_url}?brand[0]={brand_id}&page=1")
        res = await req.json()
        total_page = res["data"]["pager"]["total_pages"]
        return total_page

    @async_time()
    async def get_product_ids_of_each_brand(self, brand_id, total_pages):
        # Limit concurrent requests to avoid overwhelming the server
        semaphore = asyncio.Semaphore(5)

        async def fetch_page(page_num):
            async with semaphore:
                try:
                    resp = await self.client.get(
                        url=f"{self.base_url}?brand[0]={brand_id}&page={page_num}"
                    )
                    result = await resp.json()
                    products = result["data"]["products"]
                    return {product["id"] for product in products}
                except Exception as e:
                    logger.error(
                        f"Error fetching page {page_num} of category {brand_id}: {e}",
                        exc_info=True,
                    )
                    return set()

        # Create tasks for all pages
        tasks = [asyncio.create_task(fetch_page(i)) for i in range(1, total_pages + 1)]

        # Wait for all tasks with timeout
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)

        # Cancel pending tasks
        # for task in pending:
        #   task.cancel()

        logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        # Collect results
        product_ids = set()
        for task in done:
            try:
                product_ids.update(task.result())
            except Exception as e:
                logger.error(f"Error processing task result: {e}", exc_info=True)

        return product_ids

    async def get_all_ids_by_brand(self):
        all_brands = await self.get_all_brands()

        logger.info(f"Found {len(all_brands)} Brands and are {all_brands}")

        semaphore = asyncio.Semaphore(5)

        @async_time()
        async def get_all_ids_of_brand(brand_id):
            async with semaphore:
                try:
                    total_pages = await self.get_total_pages_of_each_brand(brand_id)
                    if total_pages:
                        product_ids = await self.get_product_ids_of_each_brand(
                            brand_id, total_pages=total_pages
                        )

                        logger.info(
                            f"{total_pages} pages and {len(product_ids)} ids found from {brand_id}"
                        )

                        return brand_id, product_ids
                    else:
                        return brand_id, set()

                except Exception as e:
                    logger.error(
                        f"Error fetching Brand {brand_id} : {e}", exc_info=True
                    )
                    return dict()

        tasks = [
            asyncio.create_task(get_all_ids_of_brand(brand_id=brand[0]))
            for brand in all_brands
        ]

        done, pending = await asyncio.wait(tasks, timeout=self.timeout)

        logger.debug(f"Done Task : {len(done)} ,Pending : {len(pending)}")

        all_product_ids = dict()
        for task in done:
            try:
                c, ids = task.result()
                all_product_ids[c] = list(ids)
            except Exception as e:
                logger.error(f"Error in processing task with {e}", exc_info=True)

        logger.info(f"Found {len(all_product_ids)} ids {all_product_ids}")
        return all_product_ids


# URL = "https://api.digikala.com/v1/categories/mobile-phone/search/"

# e = Extractor(base_url=URL, query="?sort=4&page=", timeout=100)

# brands_info = asyncio.run(e.get_all_ids_by_brand())
