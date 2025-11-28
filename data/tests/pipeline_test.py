import os
import json
import asyncio
import sys
import pytest

from data import pipeline

# fixtures
@pytest.fixture(autouse=True)
def ensure_cwd(tmp_path, monkeypatch):
    """
    Ensure tests run in a temporary working directory to avoid writing to the real project.
    """
    monkeypatch.chdir(tmp_path)
    yield


# utils
def make_dummy_brand_extractor(return_value=None, raise_exc=False):
    class DummyBE:
        def __init__(self, base_url, query, timeout):
            self.base_url = base_url
            self.query = query
            self.timeout = timeout

        async def get_all_ids_by_brand(self):
            if raise_exc:
                raise RuntimeError("Brand extraction failed")
            return return_value or {"brand": [1, 2, 3]}

    return DummyBE


def make_dummy_product_extractor(return_value=None, raise_exc=False):
    class DummyPE:
        def __init__(self, base_url, timeout, state=None, comments_base_url=None):
            self.base_url = base_url
            self.timeout = timeout
            self.state = state
            self.comments_base_url = comments_base_url

        async def run(self, brands_info):
            if raise_exc:
                raise RuntimeError("Product extraction failed")
            return return_value or ([{"id": 1, "name": "p1"}], [{"meta": "m1"}])

    return DummyPE


# tests
@pytest.mark.asyncio
async def test_ensure_dirs_creates_directory(monkeypatch, tmp_path):
    # Ensure working directory is tmp_path
    monkeypatch.chdir(tmp_path)
    result = pipeline.ensure_dirs()
    # ensure it created the expected relative path under cwd
    assert os.path.isdir(os.path.join(tmp_path, result))
    assert "data" in result and "original_data" in result


@pytest.mark.asyncio
async def test_run_brand_extraction_success(monkeypatch):
    # Patch BrandExtractor to return expected data
    monkey = make_dummy_brand_extractor(return_value={"brand_x": [123]})
    monkeypatch.setattr(pipeline, "BrandExtractor", monkey)

    result = await pipeline.run_brand_extraction(timeout=1, url="http://", query="q")
    assert isinstance(result, dict)
    assert result == {"brand_x": [123]}


@pytest.mark.asyncio
async def test_run_brand_extraction_exception(monkeypatch):
    # Patch BrandExtractor to raise
    monkey = make_dummy_brand_extractor(raise_exc=True)
    monkeypatch.setattr(pipeline, "BrandExtractor", monkey)

    with pytest.raises(RuntimeError):
        await pipeline.run_brand_extraction(timeout=1, url="http://", query="q")


@pytest.mark.asyncio
async def test_run_product_extractor_success_and_exception(monkeypatch):
    # success
    monkey_ok = make_dummy_product_extractor(return_value=([{"id": 99}], []))
    monkeypatch.setattr(pipeline, "ProductExtractor", monkey_ok)

    result = await pipeline.run_product_extractor(
        products_base_url="http://p", timeout=1, brands_info={"b": 1}, state="Products"
    )
    assert isinstance(result, tuple)
    assert result[0][0]["id"] == 99

    # exception
    monkey_bad = make_dummy_product_extractor(raise_exc=True)
    monkeypatch.setattr(pipeline, "ProductExtractor", monkey_bad)

    with pytest.raises(RuntimeError):
        await pipeline.run_product_extractor(
            products_base_url="http://p", timeout=1, brands_info={"b": 1}, state="Products"
        )


@pytest.mark.asyncio
async def test_products_main_calls_etl_and_saves_json(monkeypatch, tmp_path):
    # Prepare monkeypatches
    monkeypatch.chdir(tmp_path)

    # brand extraction stub
    async def fake_brand_extraction(timeout, url, query):
        return {"food": [1, 2]}

    # product extractor stub
    async def fake_product_extractor(products_base_url, timeout, brands_info, state=None, comments_base_url=None):
        # return product list and metadata
        return ([{"id": "p1", "name": "foo"}], [{"meta": "m"}])

    results = {}
    async def fake_run_products_etl(mongo_uri, product_path, db_name, products_collection):
        # verify the product_path file exists and contains expected content
        results["path"] = product_path
        with open(product_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # data should be what fake_product_extractor returned
        assert isinstance(data, list) or isinstance(data, tuple)
        return {"status": "ok"}

    monkeypatch.setattr(pipeline, "run_brand_extraction", fake_brand_extraction)
    monkeypatch.setattr(pipeline, "run_product_extractor", fake_product_extractor)
    monkeypatch.setattr(pipeline, "run_products_etl", fake_run_products_etl)

    out = await pipeline.products_main()
    assert out == {"status": "ok"}
    # ensure ETL received the path
    assert "path" in results
    assert os.path.exists(results["path"])


@pytest.mark.asyncio
async def test_comments_main_calls_etl_and_saves_json(monkeypatch, tmp_path):
    # Prepare monkeypatchs
    monkeypatch.chdir(tmp_path)

    # brand extraction stub
    async def fake_brand_extraction(timeout, url, query):
        return {"food": [1, 2]}

    # product extractor stub for comments
    async def fake_product_extractor(products_base_url, timeout, brands_info, state=None, comments_base_url=None):
        # return comments data as a list-like structure
        return ([{"id": "c1", "text": "nice"}], [{"meta": "m"}])

    results = {}
    async def fake_run_comments_etl(mongo_uri, comments_path, db_name, comments_collection):
        # verify the comments_path file exists and contains expected content
        results["path"] = comments_path
        with open(comments_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list) or isinstance(data, tuple)
        return {"status": "comments_ok"}

    monkeypatch.setattr(pipeline, "run_brand_extraction", fake_brand_extraction)
    monkeypatch.setattr(pipeline, "run_product_extractor", fake_product_extractor)
    monkeypatch.setattr(pipeline, "run_comments_etl", fake_run_comments_etl)

    out = await pipeline.comments_main()
    assert out == {"status": "comments_ok"}
    assert "path" in results
    assert os.path.exists(results["path"])


def test_main_arg_parsing_calls_products_and_comments(monkeypatch, tmp_path):
    # Replace asyncio.run to capture whether functions are called
    called = {"products": False, "comments": False}

    async def fake_products_main():
        called["products"] = True

    async def fake_comments_main():
        called["comments"] = True

    def fake_asyncio_run(coro):
        # run the coroutine directly for test
        return asyncio.get_event_loop().run_until_complete(coro)

    monkeypatch.setattr(pipeline, "products_main", fake_products_main)
    monkeypatch.setattr(pipeline, "comments_main", fake_comments_main)
    monkeypatch.setattr(asyncio, "run", fake_asyncio_run)

    # Test products stage
    monkeypatch.setenv("PYTEST_IS_RUNNING", "1")  # keep environment stable
    old_argv = sys.argv[:]

    sys.argv = [sys.argv[0], "--stage", "Products"]
    pipeline.main(argv=["--stage", "Products"])
    assert called["products"] is True

    # reset and test comments stage
    called["products"] = False
    sys.argv = [sys.argv[0], "--stage", "Comments"]
    pipeline.main(argv=["--stage", "Comments"])
    assert called["comments"] is True

    # restore
    sys.argv = old_argv