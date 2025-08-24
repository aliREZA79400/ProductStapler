import asyncio
from ..util.async_timer import async_time
from typing import Set, Dict
from rnet import Impersonate, Client
import os
from datetime import datetime
from ..util.logger import setup_logger

# Get the current date and time
current_time = datetime.now()

# Format the date and time into a string suitable for a filename
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Construct the log filename
log_filename = f"logs/category_ex_{timestamp}.log"

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the full path for the log file
log_file_path = os.path.join(script_dir, log_filename)

logger = setup_logger("Category_Ids_Extractor", log_file_path=log_file_path)


@async_time()
async def get_categories(base_url: str, timeout: int) -> Set:
    client = Client(impersonate=Impersonate.FirefoxAndroid135, timeout=timeout)

    resp = await client.get(url=base_url)
    result = await resp.json()
    # TODO best way to fetch data from json file
    categories = result["data"]["widgets"][3]["data"]["categories"]
    lc = len(categories)
    return {categories[i]["code"] for i in range(lc)}


# TODO use multiple  sessions for requests


@async_time()
async def get_total_page_of_each_category(
    base_url: str, category_name: str, category_query: str, timeout: int
) -> int:
    client = Client(impersonate=Impersonate.Firefox135, timeout=timeout)

    first_page = await client.get(
        url=f"{base_url}categories/{category_name}/search/{category_query}1"
    )
    result = await first_page.json()
    return result["data"]["pager"]["total_pages"]


@async_time()
async def get_product_ids_of_each_category(
    base_url: str,
    category_name: str,
    category_query: str,
    total_pages: int,
    timeout: int,
) -> Set:
    client = Client(impersonate=Impersonate.Firefox136, timeout=timeout)

    # Limit concurrent requests to avoid overwhelming the server
    semaphore = asyncio.Semaphore(5)

    async def fetch_page(page_num):
        async with semaphore:
            try:
                resp = await client.get(
                    url=f"{base_url}/categories/{category_name}/search/{category_query}{page_num}"
                    # parameterize url
                )
                result = await resp.json()
                products = result["data"]["products"]
                return {product["id"] for product in products}
            except Exception as e:
                logger.error(
                    f"Error fetching page {page_num} of category {category_name}: {e}",
                    exc_info=True,
                )
                return set()

    # Create tasks for all pages
    tasks = [asyncio.create_task(fetch_page(i)) for i in range(1, total_pages + 1)]

    # Wait for all tasks with timeout
    done, pending = await asyncio.wait(tasks, timeout=timeout)

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


@async_time()
async def main(base_url: str, timeout: int = 150) -> Dict:
    """
    Main function to get all product ids from the supermarket.
    :param base_url: The url of the supermarket.
    :param timeout: Timeout for the requests.
    :return: Set of product ids.
    """
    categories = await get_categories(base_url=base_url, timeout=timeout)
    # TODO categories list
    # TODO try except for keyerror in founding categories

    logger.info(f"Found {len(categories)} categories and are {categories}")

    semaphore = asyncio.Semaphore(5)

    async def fech_all_ids_of_category(category_name: str, category_query: str):
        async with semaphore:
            try:
                total_pages = await get_total_page_of_each_category(
                    base_url=base_url,
                    category_name=category_name,
                    category_query=category_query,
                    timeout=timeout,
                )

                # for category in categories:
                product_ids = await get_product_ids_of_each_category(
                    base_url=base_url,
                    category_name=category_name,
                    category_query=category_query,
                    total_pages=total_pages,
                    timeout=timeout,
                )
                logger.info(
                    f"{total_pages} pages and {len(product_ids)} ids found from {category_name}"
                )

                return category_name, product_ids

            except Exception as e:
                logger.error(
                    f"Error fetching Category {category_name} : {e}", exc_info=True
                )
                return dict()

    tasks = [
        asyncio.create_task(
            (
                fech_all_ids_of_category(
                    category, category_query="?_whid=29&seo_url=&page="
                )
            )
        )
        for category in categories
    ]

    done, pending = await asyncio.wait(tasks, timeout=timeout)

    logger.debug(f"Done Task : {len(done)} ,Pending : {len(pending)}")

    all_product_ids = dict()
    for task in done:
        try:
            c, ids = task.result()
            all_product_ids[c] = ids
        except Exception as e:
            logger.error(f"Error in processing task with {e}", exc_info=True)

    return all_product_ids


# remove total page
# log the exc time
# TODO customize the categories query with special parameter in main
BASE_URL = "https://api.digikala.com/fresh/v1/"
asyncio.run(main(base_url=BASE_URL))
