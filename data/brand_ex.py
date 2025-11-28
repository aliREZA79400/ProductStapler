"""
Brand Extractor Module for Digikala API

This module provides functionality to extract brand information and then product IDs
from the Digikala API. It includes methods to fetch all brands, get product IDs
for each brand of mobile phone, and handle pagination with concurrent requests.
"""

import asyncio
import os
from datetime import datetime
import json

from httpx import AsyncClient 
from .config import ENABLE_LOGGING , URL , QUERY , TIMEOUT
from .util.async_timer import async_time
from .util.logger import setup_logger
import logging

### Setup logger
if ENABLE_LOGGING:
    # Get the current date and time for log file naming
    current_time = datetime.now()

    # Format the date and time into a string suitable for a filename
    # Format: YYYY-MM-DD_HH-MM-SS
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    # Construct the log filename with timestamp to avoid conflicts
    log_filename = f"logs/brand_ex_{timestamp}.log"

    # Get the directory of the current script for relative path resolution
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the full path for the log file
    log_file_path = os.path.join(script_dir, log_filename)

    # Initialize logger with module name and file path
    logger = setup_logger("Mobile_Ids_Extractor", log_file_path=log_file_path)

else:
    logger = logging.getLogger("Test")


class Extractor:
    """
    Main extractor class for fetching brand and product data from Digikala API.

    This class handles HTTP requests, pagination, and concurrent data extraction
    with proper error handling and logging.
    """

    def __init__(self, base_url:str, query:str, timeout:int) -> None:
        """
        Initialize the Extractor with API configuration.

        Args:
            base_url (str): Base URL for the Digikala API endpoint
            query (str): Query string template for pagination (e.g., "?sort=4&page=")
            timeout (int): Timeout in seconds for HTTP requests
        """
        self.base_url = base_url
        self.query = query
        self.client = AsyncClient(timeout=timeout,follow_redirects=True)
        self.timeout = timeout

    @async_time()
    async def get_all_brands(self) -> set:
        """
        Fetch all available brands from the API.

        Returns:
            set: Set of tuples containing (brand_id, brand_code) for all brands
        """
        try:
           # Make request to get brand information
           req = await self.client.get(url=self.base_url)
        except Exception as e:
            logger.error(f"Error fetching all brands: {e} with status code {req.status_code}", exc_info=True)
            return set()
        try:
           res = req.json()
        except Exception as e:
            logger.error(f"Error extracting brands: {e}", exc_info=True)
            return set()
        
        # Extract brand options from API response 
        #TODO: parameterize this as a query parameter
        brands = res["data"]["filters"]["brands"]["options"]

        # Create set of (id, code) tuples for all brands
        all_brands = {(brand["id"], brand["code"]) for brand in brands}

        return all_brands

    @async_time()
    async def get_total_pages_of_each_brand(self, brand_id:int) -> int:
        """
        Get the total number of pages for products of a specific brand.

        Args:
            brand_id (int): ID of the brand to check

        Returns:
            int: Total number of pages for the brand's products
        """
        # Make request with brand filter to get pagination info
        try:
          req = await self.client.get(
            #TODO: this is business logic . parameterize this as a query parameter
            url=f"{self.base_url}?has_selling_stock=1&brand[0]={brand_id}&page=1"
        )
        except Exception as e:
            logger.error(f"Error fetching total pages of brand {brand_id}: {e} with status code {req.status_code}", exc_info=True)
            return 0
        try:
            res = req.json()
        except Exception as e:
            logger.error(f"Error extracting total pages of brand {brand_id}: {e}", exc_info=True)
            return 0
        # Extract total pages from response
        #TODO: parameterize this as a query parameter
        total_page = res["data"]["pager"]["total_pages"]

        return total_page

    @async_time()
    async def get_product_ids_of_each_brand(self, brand_id:int, total_pages:int) -> set:
        """
        Fetch all product IDs for a specific brand across all its pages.

        Args:
            brand_id (int): ID of the brand to fetch products for
            total_pages (int): Total number of pages for this brand

        Returns:
            set: Set of all product IDs for the specified brand
        """
        # Limit concurrent requests to avoid overwhelming the server
        semaphore = asyncio.Semaphore(5)

        async def fetch_page(page_num:int) -> set:
            """
            Fetch product IDs from a specific page of a brand.

            Args:
                page_num (int): Page number to fetch

            Returns:
                set: Set of product IDs from the specified page
            """
            async with semaphore:
                try:
                    # Construct URL with brand filter and page number
                    #TODO: this is business logic . parameterize this as a query parameter
                    try :
                       resp = await self.client.get(
                        url=f"{self.base_url}?brand[0]={brand_id}&page={page_num}"
                    )
                    except Exception as e:
                        logger.error(f"Error fetching page {page_num} of category {brand_id}: {e} with status code {resp.status_code}", exc_info=True)
                        return set()
                    try:
                        result = resp.json()
                    except Exception as e:
                        logger.error(f"Error extracting page {page_num} of category {brand_id}: {e}", exc_info=True)
                        return set()
                    # Extract product IDs from response
                    products = result["data"]["products"]
                    return {product["id"] for product in products}
                except Exception as e:
                    logger.error(
                        f"Error fetching page {page_num} of category {brand_id}: {e}",
                        exc_info=True,
                    )
                    return set()

        # Create tasks for all pages of the brand
        tasks = [asyncio.create_task(fetch_page(i)) for i in range(1, total_pages + 1)]

        # Wait for all tasks with timeout
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)

        # Cancel pending tasks (commented out to avoid cancellation errors)
        # for task in pending:
        #   task.cancel()

        logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        # Collect results from completed tasks
        product_ids = set()
        for task in done:
            try:
                product_ids.update(task.result())
            except Exception as e:
                logger.error(f"Error processing task result: {e}", exc_info=True)

        return product_ids

    async def get_all_ids_by_brand(self) -> dict:
        """
        Main method to fetch all product IDs organized by brand.

        This method:
        1. Gets all available brands
        2. For each brand, fetches all its product IDs
        3. Returns a dictionary mapping brand_id to list of product_ids

        Returns:
            dict: Dictionary with brand_id as key and list of product_ids as value

        Note:
            Uses concurrent processing for all brands with semaphore limiting
        """
        # Get all available brands first
        all_brands = await self.get_all_brands()

        logger.info(f"Found {len(all_brands)} Brands and are {all_brands}")

        # Limit concurrent brand processing
        semaphore = asyncio.Semaphore(5)

        @async_time()
        async def get_all_ids_of_brand(brand_id):
            """
            Fetch all product IDs for a single brand.

            Args:
                brand_id (int): ID of the brand to process

            Returns:
                tuple: (brand_id, set_of_product_ids) or empty dict on error
            """
            async with semaphore:
                try:
                    # Get total pages for this brand
                    total_pages = await self.get_total_pages_of_each_brand(brand_id)
                    if total_pages:
                        # Fetch all product IDs for this brand
                        product_ids = await self.get_product_ids_of_each_brand(
                            brand_id, total_pages=total_pages
                        )

                        logger.info(
                            f"{total_pages} pages and {len(product_ids)} ids found from {brand_id}"
                        )

                        return brand_id, product_ids
                    else:
                        # No pages found for this brand
                        return brand_id, set()

                except Exception as e:
                    logger.error(
                        f"Error fetching Brand {brand_id} : {e}", exc_info=True
                    )
                    return dict()

        # Create tasks for all brands
        tasks = [
            asyncio.create_task(get_all_ids_of_brand(brand_id=brand[0]))
            for brand in all_brands
        ]

        # Wait for all brand processing tasks to complete
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)

        logger.debug(f"Done Task : {len(done)} ,Pending : {len(pending)}")

        # Collect results into final dictionary
        all_product_ids = dict()
        for task in done:
            try:
                c, ids = task.result()
                # Convert set to list for JSON serialization compatibility
                all_product_ids[c] = list(ids)
            except Exception as e:
                logger.error(f"Error in processing task with {e}", exc_info=True)

        logger.info(f"Found {len(all_product_ids)} ids {all_product_ids}")
        return all_product_ids


# # Example usage (commented out):
# e = Extractor(base_url=URL, query=QUERY, timeout=TIMEOUT)
# brands_info = asyncio.run(e.get_all_ids_by_brand())

# # Load brand information from file
# file_path = f"data/original_data/brand_ex_{timestamp}.json"
# try:
#     with open(file_path, "w") as f:
#         brands_info = json.dump(brands_info, f)
# except Exception as e:
#     print(f"File not found and accure erroe {e} ")
#     brands_info = None


