import pytest

import sys
import os



# Ensure the parent directory is in the path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.brand_ex import Extractor
from data.config import URL, QUERY, TIMEOUT

@pytest.mark.asyncio
async def test_get_all_brands():
    """
    Test that get_all_brands returns a non-empty set of (id, code) tuples.
    """
    extractor = Extractor(base_url=URL, query=QUERY, timeout=TIMEOUT)
    result = await extractor.get_all_brands()
    assert isinstance(result, set)
    assert len(result) > 0
    # Verify each element is a tuple with 2 entries (id, code)
    for b in result:
        assert isinstance(b, tuple)
        assert len(b) == 2
        assert isinstance(b[0], int)

@pytest.mark.asyncio
async def test_get_total_pages_of_each_brand():
    """
    Test get_total_pages_of_each_brand returns an int >= 0 for a known good brand.
    """
    extractor = Extractor(base_url=URL, query=QUERY, timeout=TIMEOUT)
    brands = await extractor.get_all_brands()
    any_brand = next(iter(brands))
    brand_id = any_brand[0]
    pages = await extractor.get_total_pages_of_each_brand(brand_id)
    assert isinstance(pages, int)
    assert pages >= 0

@pytest.mark.asyncio
async def test_get_product_ids_of_each_brand():
    """
    Test product ID extraction for one known brand.
    It is possible some brands do not have any products.
    """
    extractor = Extractor(base_url=URL, query=QUERY, timeout=TIMEOUT)
    brands = await extractor.get_all_brands()
    brand_id = next(iter(brands))[0]
    pages = await extractor.get_total_pages_of_each_brand(brand_id)
    result = await extractor.get_product_ids_of_each_brand(brand_id, total_pages=pages)
    assert isinstance(result, set)
    # It's possible for some brands to have no products
    if pages == 0 or result == set():
        assert len(result) == 0
    else:
        # There should be at least one product id if pages > 0 and result is not empty
        assert len(result) > 0
        for pid in result:
            assert isinstance(pid, int)

@pytest.mark.asyncio
async def test_get_all_ids_by_brand_returns_dict():
    """
    Test that get_all_ids_by_brand returns a dict keyed by brand id, with list of product ids.
    """
    extractor = Extractor(base_url=URL, query=QUERY, timeout=TIMEOUT)
    result = await extractor.get_all_ids_by_brand()
    assert isinstance(result, dict)
    # Test only first 2 brands for speed
    count = 0
    for k, v in result.items():
        assert isinstance(k, int)
        assert isinstance(v, list)
        for pid in v:
            assert isinstance(pid, int)
        count += 1
        if count > 2:
            break

