import pytest

from data.product_ex import ProductExtractor

# Dummy constants for test configuration
BASE_URL = "https://api.digikala.com/v1/product/"
TIMEOUT = 100
BRAND_ID = 18
PRODUCT_IDS = [13981188, 18576389]  # Example product IDs from sample data
NON_EXISTENT_PRODUCT_ID = 99999999  # Assumed not to exist

@pytest.mark.asyncio
async def test_fetch_product_success(monkeypatch):
    # Mock client.get to simulate API response for a valid product
    class DummyResponse:
        def json(self):
            return {"data": {"product": {"id": 13981188, "title_fa": "Test Product"}}}
    async def dummy_get(*args, **kwargs):
        return DummyResponse()
    extractor = ProductExtractor(BASE_URL, TIMEOUT)
    extractor.client.get = dummy_get

    product = await extractor.fetch_product(13981188)
    assert product is not None
    assert product["id"] == 13981188
    assert product["title_fa"] == "Test Product"

@pytest.mark.asyncio
async def test_fetch_product_invalid_json(monkeypatch):
    class DummyResponse:
        def json(self):
            raise Exception("JSON decode error")
    async def dummy_get(*args, **kwargs):
        return DummyResponse()
    extractor = ProductExtractor(BASE_URL, TIMEOUT)
    extractor.client.get = dummy_get

    product = await extractor.fetch_product(13981188)
    assert product is None

@pytest.mark.asyncio
async def test_fetch_product_http_error(monkeypatch):
    async def dummy_get(*args, **kwargs):
        raise Exception("HTTP error")
    extractor = ProductExtractor(BASE_URL, TIMEOUT)
    extractor.client.get = dummy_get

    product = await extractor.fetch_product(NON_EXISTENT_PRODUCT_ID)
    assert product is None

@pytest.mark.asyncio
async def test_fetch_brand_products(monkeypatch):
    # Simulate fetch_product calls for two product_ids
    responses = [
        {"id": 13981188, "title_fa": "First"}, 
        {"id": 18576389, "title_fa": "Second"}
    ]
    async def dummy_fetch_product(pid):
        for r in responses:
            if r["id"] == pid:
                return r
        return None

    extractor = ProductExtractor(BASE_URL, TIMEOUT)
    extractor.fetch_product = dummy_fetch_product  # monkeypatch instance method

    result = await extractor.fetch_brand_products(BRAND_ID, PRODUCT_IDS)
    assert BRAND_ID in result
    assert isinstance(result[BRAND_ID], list)
    assert {p["id"] for p in result[BRAND_ID]} == set(PRODUCT_IDS)

@pytest.mark.asyncio
async def test_fetch_brand_products_all_failures(monkeypatch):
    async def always_none(pid):
        return None

    extractor = ProductExtractor(BASE_URL, TIMEOUT)
    extractor.fetch_product = always_none

    result = await extractor.fetch_brand_products(BRAND_ID, PRODUCT_IDS)
    assert result[BRAND_ID] == []

