"""
Category Extractor Module for Digikala Fresh API

This module provides functionality to extract category information and product IDs
from the Digikala Fresh API. It includes methods to fetch all categories, get product IDs
for each category, and handle pagination with concurrent requests.

The module is specifically designed for the Digikala Fresh supermarket section,
extracting product data organized by food and grocery categories.
"""

import asyncio
from ..util.async_timer import async_time
from typing import Set, Dict
from rnet import Impersonate, Client
import os
from datetime import datetime
from ..util.logger import setup_logger

# Get the current date and time for log file naming
current_time = datetime.now()

# Format the date and time into a string suitable for a filename
# Format: YYYY-MM-DD_HH-MM-SS
timestamp = current_time.strftime("%Y-%m-%d_%H-%M-%S")

# Construct the log filename with timestamp to avoid conflicts
log_filename = f"logs/category_ex_{timestamp}.log"

# Get the directory of the current script for relative path resolution
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the full path for the log file
log_file_path = os.path.join(script_dir, log_filename)

# Initialize logger with module name and file path
logger = setup_logger("Category_Ids_Extractor", log_file_path=log_file_path)


@async_time()
async def get_categories(base_url: str, timeout: int) -> Set:
    """
    Fetch all available categories from the Digikala Fresh API.
    
    This function extracts category codes from the API response structure.
    The categories are found in a specific widget section of the response.
    
    Args:
        base_url (str): Base URL for the Digikala Fresh API
        timeout (int): Timeout in seconds for HTTP requests
        
    Returns:
        Set[str]: Set of category codes available in the API
        
    Note:
        Uses Firefox Android impersonation for mobile-specific API access
        TODO: Find better way to extract data from JSON response structure
    """
    # Initialize client with mobile browser impersonation for fresh API
    client = Client(impersonate=Impersonate.FirefoxAndroid135, timeout=timeout)

    # Make request to get category information
    resp = await client.get(url=base_url)
    result = await resp.json()
    # TODO: Find best way to fetch data from json file structure
    # Extract categories from specific widget in API response
    categories = result["data"]["widgets"][3]["data"]["categories"]
    lc = len(categories)
    # Return set of category codes
    return {categories[i]["code"] for i in range(lc)}


# TODO: Implement multiple sessions for concurrent requests to improve performance


@async_time()
async def get_total_page_of_each_category(
    base_url: str, category_name: str, category_query: str, timeout: int
) -> int:
    """
    Get the total number of pages for products in a specific category.
    
    This function makes a request to the first page of a category to determine
    the total number of pages available for that category.
    
    Args:
        base_url (str): Base URL for the Digikala Fresh API
        category_name (str): Name/code of the category to check
        category_query (str): Query string template for pagination
        timeout (int): Timeout in seconds for HTTP requests
        
    Returns:
        int: Total number of pages for the specified category
    """
    # Initialize client with Firefox impersonation
    client = Client(impersonate=Impersonate.Firefox135, timeout=timeout)

    # Make request to first page to get pagination information
    first_page = await client.get(
        url=f"{base_url}categories/{category_name}/search/{category_query}1"
    )
    result = await first_page.json()
    # Extract total pages from API response
    return result["data"]["pager"]["total_pages"]


@async_time()
async def get_product_ids_of_each_category(
    base_url: str,
    category_name: str,
    category_query: str,
    total_pages: int,
    timeout: int,
) -> Set:
    """
    Fetch all product IDs for a specific category across all its pages.
    
    This function uses concurrent requests with semaphore limiting to efficiently
    fetch product IDs from all pages of a category without overwhelming the server.
    
    Args:
        base_url (str): Base URL for the Digikala Fresh API
        category_name (str): Name/code of the category to fetch products for
        category_query (str): Query string template for pagination
        total_pages (int): Total number of pages for this category
        timeout (int): Timeout in seconds for HTTP requests
        
    Returns:
        Set[int]: Set of all product IDs for the specified category
        
    Note:
        Uses semaphore with limit of 5 concurrent requests for rate limiting
    """
    # Initialize client with Firefox impersonation
    client = Client(impersonate=Impersonate.Firefox136, timeout=timeout)

    # Limit concurrent requests to avoid overwhelming the server
    semaphore = asyncio.Semaphore(5)

    async def fetch_page(page_num):
        """
        Fetch product IDs from a specific page of a category.
        
        Args:
            page_num (int): Page number to fetch
            
        Returns:
            set: Set of product IDs from the specified page
        """
        async with semaphore:
            try:
                # Construct URL with category and page number
                resp = await client.get(
                    url=f"{base_url}/categories/{category_name}/search/{category_query}{page_num}"
                    # TODO: Parameterize URL construction for better maintainability
                )
                result = await resp.json()
                # Extract product IDs from response
                products = result["data"]["products"]
                return {product["id"] for product in products}
            except Exception as e:
                logger.error(
                    f"Error fetching page {page_num} of category {category_name}: {e}",
                    exc_info=True,
                )
                return set()

    # Create tasks for all pages of the category
    tasks = [asyncio.create_task(fetch_page(i)) for i in range(1, total_pages + 1)]

    # Wait for all tasks with timeout
    done, pending = await asyncio.wait(tasks, timeout=timeout)

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


@async_time()
async def main(base_url: str, timeout: int = 150) -> Dict:
    """
    Main function to get all product IDs from the Digikala Fresh supermarket.
    
    This function orchestrates the entire extraction process:
    1. Fetches all available categories
    2. For each category, gets total pages and fetches all product IDs
    3. Returns a dictionary mapping category names to their product IDs
    
    Args:
        base_url (str): The base URL of the Digikala Fresh API
        timeout (int): Timeout in seconds for the requests (default: 150)
        
    Returns:
        Dict[str, Set[int]]: Dictionary with category names as keys and 
                           sets of product IDs as values
                           
    Note:
        Uses concurrent processing for all categories with semaphore limiting
        TODO: Add categories list parameter for selective extraction
        TODO: Add try-except for KeyError when finding categories
    """
    # Get all available categories from the API
    categories = await get_categories(base_url=base_url, timeout=timeout)
    # TODO: Add categories list parameter for selective extraction
    # TODO: Add try-except for KeyError when finding categories

    logger.info(f"Found {len(categories)} categories and are {categories}")

    # Limit concurrent category processing
    semaphore = asyncio.Semaphore(5)

    async def fech_all_ids_of_category(category_name: str, category_query: str):
        """
        Fetch all product IDs for a single category.
        
        Args:
            category_name (str): Name/code of the category to process
            category_query (str): Query string template for pagination
            
        Returns:
            tuple: (category_name, set_of_product_ids) or empty dict on error
        """
        async with semaphore:
            try:
                # Get total pages for this category
                total_pages = await get_total_page_of_each_category(
                    base_url=base_url,
                    category_name=category_name,
                    category_query=category_query,
                    timeout=timeout,
                )

                # Fetch all product IDs for this category
                # Note: This was previously in a loop for all categories
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

    # Create tasks for all categories with default query parameters
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

    # Wait for all category processing tasks to complete
    done, pending = await asyncio.wait(tasks, timeout=timeout)

    logger.debug(f"Done Task : {len(done)} ,Pending : {len(pending)}")

    # Collect results into final dictionary
    all_product_ids = dict()
    for task in done:
        try:
            c, ids = task.result()
            all_product_ids[c] = ids
        except Exception as e:
            logger.error(f"Error in processing task with {e}", exc_info=True)

    return all_product_ids


# TODO: Remove total page calculation if not needed for optimization
# TODO: Log execution time for performance monitoring
# TODO: Customize the categories query with special parameters in main function

# Base URL for Digikala Fresh API
BASE_URL = "https://api.digikala.com/fresh/v1/"

# Run the main extraction function
asyncio.run(main(base_url=BASE_URL))
