"""
Product Extractor Module for Digikala API

This module provides functionality to extract detailed product information and comments
from the Digikala API. It includes methods to fetch individual products, process multiple
products by brand, and handle both product data and user comments extraction.

The module supports two main modes:
1. Product data extraction - fetches detailed product information
2. Comments extraction - fetches user reviews and ratings for products

"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiofiles
from httpx import AsyncClient
from .config import ENABLE_LOGGING, COMMENTS_BASE_URL, PRODUCT_BASE_URL
from .util.async_timer import async_time
from .util.logger import setup_logger
import logging

if ENABLE_LOGGING:
    # Get the current date and time for log file naming
    current_time = datetime.now()

    # Format the date and time into a string suitable for a filename
    # Format: YYYY-MM-DD_HH-MM-SS
    timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    # Construct the log filename with timestamp to avoid conflicts
    # Note: There's a typo in the original filename "prduct_ex" instead of "product_ex"
    log_filename = f"logs/prduct_ex_{timestamp}.log"

    # Get the directory of the current script for relative path resolution
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define the full path for the log file
    log_file_path = os.path.join(script_dir, log_filename)

    # Initialize logger with module name and file path
    logger = setup_logger("Product_Extractor", log_file_path=log_file_path)
else:
    logger = logging.getLogger("Test")


class ProductExtractor:
    """
    Main extractor class for fetching product data and comments from Digikala API.

    This class handles HTTP requests, concurrent processing, and data extraction
    with proper error handling and logging. It supports both product data and
    comments extraction modes.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int,
        concurrency: int = 5,
        logger_instance=logger,
        comments_base_url: str = "",
        state: str = "",
    ):
        """
        Initialize the ProductExtractor with API configuration.

        Args:
            base_url (str): Base URL for the Digikala product API endpoint
            timeout (int): Timeout in seconds for HTTP requests
            concurrency (int): Maximum number of concurrent requests (default: 5)
            client (Optional[Async Client]): Custom HTTP client instance
            logger_instance: Logger instance for logging operations
            comments_base_url (str): Base URL for comments API endpoint
        """
        self.base_url = base_url
        self.timeout = timeout
        # Create semaphore to limit concurrent requests
        self.semaphore = asyncio.Semaphore(concurrency)
        # Use provided client or create default one with Firefox impersonation
        self.client = AsyncClient(timeout=timeout, follow_redirects=True)
        self.logger = logger_instance
        self.comments_base_url = comments_base_url
        self.state = state

    @async_time()
    async def fetch_product(self, product_id: Union[int, str]) -> Optional[dict]:
        """
        Fetch detailed product information for a single product.

        Args:
            product_id (Union[int, str]): ID of the product to fetch

        Returns:
            Optional[dict]: Product data dictionary or None if fetch failed

        Note:
            Uses semaphore to limit concurrent requests and includes
            comprehensive error handling for JSON decode and HTTP errors
        """
        async with self.semaphore:
            res = None
            try:
                # Make request to product API endpoint
                res = await self.client.get(
                    url=f"{self.base_url}{product_id}/", timeout=self.timeout
                )
                result = res.json()
                # Extract product data from API response structure
                return result["data"]["product"]
            except json.JSONDecodeError as e:
                self.logger.error(f"Json decode error for {product_id} with {e}")
            except Exception as e:
                # Get HTTP status code if available for better error reporting
                status = getattr(res, "status", "unknown")
                self.logger.error(
                    f"Unexpected error {e} status code {status} for product {product_id}"
                )
            return None

    @async_time()
    async def fetch_brand_products(
        self,
        brand_id: Union[int, str],
        product_ids: List[Union[int, str]],
    ) -> dict:
        """
        Fetch data for all products belonging to a specific brand.

        Args:
            brand_id (Union[int, str]): ID of the brand to process
            product_ids (List[Union[int, str]]): List of product IDs for this brand

        Returns:
            dict: Dictionary with brand_id as key and list of fetched data as value
        """
        self.logger.debug(f"Fetching the Brand Products {brand_id}")

        # Create tasks for fetching product data for each product
        tasks = [asyncio.create_task(self.fetch_product(pid)) for pid in product_ids]

        # Wait for all tasks to complete with timeout
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)
        self.logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        # Initialize result structure for this brand
        result_by_brand = {brand_id: list()}

        # Collect results from completed tasks
        for task in done:
            try:
                item = task.result()
                if item is not None:
                    result_by_brand[brand_id].append(item)
            except Exception as e:
                self.logger.error(f"Found error {e} when processing")

        self.logger.info(f"{brand_id} Fetched")
        return result_by_brand

    @async_time()
    async def _fetch_comments_page(
        self, product_id: Union[int, str], page_number: int
    ) -> List[dict]:
        """
        Fetch comments from a specific page for a product.

        This is a private helper method used by fetch_product_comments
        to handle pagination of comments.

        Args:
            product_id (Union[int, str]): ID of the product
            page_number (int): Page number to fetch

        Returns:
            List[dict]: List of comment dictionaries from the specified page
        """
        async with self.semaphore:
            res = None
            try:
                # Construct URL for specific page of comments
                url = f"{self.comments_base_url}{product_id}/?page={page_number}"
                res = await self.client.get(url=url, timeout=self.timeout)
                result = res.json()
                # Extract comments from API response, default to empty list if not found
                return result["data"].get("comments", [])
            except json.JSONDecodeError as e:
                self.logger.error(
                    f"Json decode error for comments of {product_id} page {page_number} with {e}"
                )
            except Exception as e:
                # Get HTTP status code if available for better error reporting
                status = getattr(res, "status", "unknown")
                self.logger.error(
                    f"Unexpected error {e} status code {status} for comments of product {product_id} page {page_number}"
                )
            return []

    @async_time()
    async def fetch_product_comments(self, product_id: Union[int, str]) -> List[dict]:
        """
        Fetch all comments for a specific product across all pages.

        This method handles pagination by first fetching the first page to determine
        total pages, then concurrently fetching all remaining pages.

        Args:
            product_id (Union[int, str]): ID of the product to fetch comments for

        Returns:
            List[dict]: List of all comment dictionaries for the product

        Note:
            Returns empty list if any error occurs during the process
        """
        try:
            # First page to get total pages and initial comments
            first_page_url = f"{self.comments_base_url}{product_id}/?page=1"
            first_page_response = await self.client.get(
                url=first_page_url, timeout=self.timeout
            )
            first_page_result = first_page_response.json()
            total_pages = first_page_result["data"]["pager"]["total_pages"]

            # Gather comments from page 1 (already fetched)
            comments: List[dict] = first_page_result["data"].get("comments", [])

            # If only one page, return the comments we already have
            if int(total_pages) <= 1:
                return comments

            # Create tasks for remaining pages (2..total_pages)
            tasks = [
                asyncio.create_task(self._fetch_comments_page(product_id, page_number))
                for page_number in range(2, int(total_pages) + 1)
            ]

            # Wait for all page tasks to complete
            done, _ = await asyncio.wait(tasks, timeout=self.timeout)

            # Aggregate comments from all pages
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
    async def fetch_brand_comments(
        self, brand_id: Union[int, str], product_ids: List[Union[int, str]]
    ) -> dict:
        """
        Fetch data for all products comments belonging to a specific brand.

        Args:
            brand_id (Union[int, str]): ID of the brand to process
            product_ids (List[Union[int, str]]): List of product IDs for this brand

        Returns:
            dict: Dictionary with brand_id as key and list of fetched data as value
        """
        self.logger.debug(f"Fetching the Brand Products {brand_id}")

        # Create tasks for fetching product data for each product
        tasks = [
            asyncio.create_task(self.fetch_product_comments(pid)) for pid in product_ids
        ]

        # Wait for all tasks to complete with timeout
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)
        self.logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        # Initialize result structure for this brand
        result_by_brand = {brand_id: list()}

        # Collect results from completed tasks
        for task in done:
            try:
                item = task.result()
                if item is not None:
                    result_by_brand[brand_id].append(item)
            except Exception as e:
                self.logger.error(f"Found error {e} when processing")

        self.logger.info(f"{brand_id} Fetched")
        return result_by_brand

    @async_time()
    async def run(
        self,
        brands_info: Dict[Union[int, str], List[Union[int, str]]],
    ) -> List[dict]:
        """
        Main method to process all brands and their products.

        This method orchestrates the extraction process for multiple brands,
        creating concurrent tasks for each brand and collecting all results.

        Args:
            brands_info (Dict[Union[int, str], List[Union[int, str]]]):
                Dictionary mapping brand IDs to lists of product IDs
            comments (bool): If True, fetch comments; if False, fetch product data

        Returns:
            List[dict]: List of dictionaries, each containing brand data

        Note:
            Only processes brands that have non-empty product ID lists
        """
        match self.state:
            case "Products":
                tasks = [
                    asyncio.create_task(
                        self.fetch_brand_products(brand_id, product_ids)
                    )
                    for brand_id, product_ids in brands_info.items()
                    if len(product_ids) != 0
                ]
            case "Comments":
                tasks = [
                    asyncio.create_task(
                        self.fetch_brand_comments(brand_id, product_ids)
                    )
                    for brand_id, product_ids in brands_info.items()
                    if len(product_ids) != 0
                ]

        # Wait for all brand processing tasks to complete
        done, pending = await asyncio.wait(tasks, timeout=self.timeout)  # pyright: ignore
        self.logger.debug(f"Done task : {len(done)} , Pending tassk : {len(pending)} ")

        # Collect all results from completed tasks
        all_results: List[dict] = []
        for task in done:
            try:
                all_results.append(task.result())
            except Exception as e:
                self.logger.error(f"Found error {e} when processing a brand")

        self.logger.info("Completed")
        return all_results

    @async_time()
    async def save(self, data: Any, file_name: str) -> None:
        """
        Save data to a JSON file asynchronously.

        Args:
            data (Any): Data to save (will be JSON serialized)
            file_name (str): Path to the output file

        Note:
            Uses aiofiles for asynchronous file I/O operations
        """
        async with aiofiles.open(file_name, "w") as f:
            await f.write(json.dumps(data, indent=4))

    @staticmethod
    def load_brands_info(file_path: str) -> Optional[Dict]:
        """
        Load brand information from a JSON file.

        Args:
            file_path (str): Path to the JSON file containing brand info

        Returns:
            Optional[Dict]: Loaded brand information or None if file not found

        Note:
            This is a static method for utility purposes
        """
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"File not found and accure erroe {e} ")
            return None


# This section demonstrates how to use the ProductExtractor class

# # Load brand information from file
# file_path = "data/original_data/brand_ex.json"
# try:
#     with open(file_path, "r") as f:
#         brands_info = json.load(f)
# except Exception as e:
#     print(f"File not found and accure erroe {e} ")
#     brands_info = None


# state="Products"
# # Execute extraction if brand info is available
# if brands_info:
#     # Initialize extractor with configuration
#     extractor = ProductExtractor(base_url=PRODUCT_BASE_URL, timeout=400,comments_base_url=COMMENTS_BASE_URL,state=state)


#     # Run extraction process
#     all_results = asyncio.run(
#         extractor.run(brands_info=brands_info)
#     )

#     # Print number of results
#     print(len(all_results))


#     out_file = f"data/original_data/{state}_{timestamp}.json"

#     # Save results to file
#     asyncio.run(extractor.save(all_results, out_file))
