import asyncio
from rnet import Client, Impersonate
from datetime import datetime
import os
from ..util.logger import setup_logger
from ..util.async_timer import async_time
import aiofiles
import json
from typing import Dict, Union, Optional, List, Any

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


class ProductExtractor:
    def __init__(
        self,
        base_url: str,
        timeout: int,
        concurrency: int = 5,
        client: Optional[Client] = None,
        logger_instance=logger,
        comments_base_url: str = "https://api.digikala.com/v1/rate-review/products/",
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = client or Client(
            impersonate=Impersonate.Firefox136, timeout=timeout
        )
        self.logger = logger_instance
        self.comments_base_url = comments_base_url

    @async_time()
    async def fetch_product(self, product_id: Union[int, str]) -> Optional[dict]:
        async with self.semaphore:
            res = None
            try:
                res = await self.client.get(
                    url=f"{self.base_url}{product_id}/", timeout=self.timeout
                )
                result = await res.json()
                return result["data"]["product"]
            except json.JSONDecodeError as e:
                self.logger.error(f"Json decode error for {product_id} with {e}")
            except Exception as e:
                status = getattr(res, "status", "unknown")
                self.logger.error(
                    f"Unexpected error {e} status code {status} for product {product_id}"
                )
            return None

    @async_time()
    async def fetch_brand(
        self,
        brand_id: Union[int, str],
        product_ids: List[Union[int, str]],
        comments: bool = False,
    ) -> dict:
        self.logger.debug(f"Fetching the Brand {brand_id}")
        if comments:
            tasks = [
                asyncio.create_task(self.fetch_product_comments(pid))
                for pid in product_ids
            ]
        else:
            tasks = [
                asyncio.create_task(self.fetch_product(pid)) for pid in product_ids
            ]

        done, pending = await asyncio.wait(tasks, timeout=self.timeout)
        self.logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        result_by_brand = {brand_id: list()}
        for task in done:
            try:
                item = task.result()
                if item is not None:
                    result_by_brand[brand_id].append(item)
            except Exception as e:
                self.logger.error(
                    f"Found error {e} when processing the {'comments' if comments else 'product'} "
                )

        self.logger.info(f"{brand_id} Fetched")
        return result_by_brand

    @async_time()
    async def run(
        self,
        brands_info: Dict[Union[int, str], List[Union[int, str]]],
        comments: bool = False,
    ) -> List[dict]:
        tasks = [
            asyncio.create_task(
                self.fetch_brand(brand_id, product_ids, comments=comments)
            )
            for brand_id, product_ids in brands_info.items()
            if len(product_ids) != 0
        ]
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)
        self.logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        all_results: List[dict] = []
        for task in done:
            try:
                all_results.append(task.result())
            except Exception as e:
                self.logger.error(f"Found error {e} when processing a brand")

        self.logger.info("Completed")
        return all_results

    @async_time()
    async def _fetch_comments_page(
        self, product_id: Union[int, str], page_number: int
    ) -> List[dict]:
        async with self.semaphore:
            res = None
            try:
                url = f"{self.comments_base_url}{product_id}/?page={page_number}"
                res = await self.client.get(url=url, timeout=self.timeout)
                result = await res.json()
                return result["data"].get("comments", [])
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Json decode error for comments of {product_id} page {page_number} with {e}"
                )
            except Exception as e:
                status = getattr(res, "status", "unknown")
                self.logger.error(
                    f"Unexpected error {e} status code {status} for comments of product {product_id} page {page_number}"
                )
            return []

    @async_time()
    async def fetch_product_comments(self, product_id: Union[int, str]) -> List[dict]:
        try:
            # First page to get total pages
            first_page_url = f"{self.comments_base_url}{product_id}/?page=1"
            first_page_response = await self.client.get(
                url=first_page_url, timeout=self.timeout
            )
            first_page_result = await first_page_response.json()
            total_pages = first_page_result["data"]["pager"]["total_pages"]

            # Gather comments from page 1 (already fetched)
            comments: List[dict] = first_page_result["data"].get("comments", [])

            if int(total_pages) <= 1:
                return comments

            # Create tasks for remaining pages (2..total_pages)
            tasks = [
                asyncio.create_task(self._fetch_comments_page(product_id, page_number))
                for page_number in range(2, int(total_pages) + 1)
            ]

            done, pending = await asyncio.wait(tasks, timeout=self.timeout)
            for task in done:
                try:
                    comments.extend(task.result())
                except Exception as e:
                    self.logger.error(
                        f"Found error {e} when aggregating comments for product {product_id}"
                    )

            return comments
        except Exception as e:
            self.logger.error(f"Failed to fetch comments for product {product_id}: {e}")
            return []

    @async_time()
    async def save(self, data: Any, file_name: str) -> None:
        async with aiofiles.open(file_name, "w") as f:
            await f.write(json.dumps(data, indent=4))

    @staticmethod
    def load_brands_info(file_path: str) -> Optional[Dict]:
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"File not found and accure erroe {e} ")
            return None


# Optional runnable section for parity with the functional script
file_path = "data/digikala/original_data/brands_info.json"
try:
    with open(file_path, "r") as f:
        brands_info = json.load(f)
except Exception as e:
    print(f"File not found and accure erroe {e} ")
    brands_info = None

BASE_URL = "https://api.digikala.com/v2/product/"

if brands_info:
    extractor = ProductExtractor(base_url=BASE_URL, timeout=400)
    COMMENTS_MODE = True  # Set True to fetch comments instead of product data
    all_results = asyncio.run(
        extractor.run(brands_info=brands_info, comments=COMMENTS_MODE)
    )

    print(len(all_results))
    suffix = "comments" if COMMENTS_MODE else "products"
    out_file = f"data/digikala/original_data/{timestamp}_{suffix}.json"
    asyncio.run(extractor.save(all_results, out_file))

# TODO handle this errors 2025-08-27 09:59 - ERROR - Failed to fetch comments for product 6078: is_decode error: wreq::Error { kind: Decode, source: Error("expected value", line: 1, column: 1) }
# 2025-08-27 09:59 - ERROR - Failed to fetch comments for product 11274529: is_connect error: wreq::Error { kind: Request, url: "https://api.digikala.com/v1/rate-review/products/11274529/?page=1", source: crate::util::client::Error(Connect, ConnectError("tcp open error", Os { code: 24, kind: Uncategorized, message: "Too many open files" })) }
