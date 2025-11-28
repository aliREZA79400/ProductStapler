import json

from pathlib import Path

import pytest

from data import etl


def write_file(path: Path, content):
    path.write_text(json.dumps(content, ensure_ascii=False))


def test_find_latest_file_nonexistent(tmp_path):
    # directory does not exist
    missing = tmp_path / "no_such_dir"
    res = etl.find_latest_file(str(missing), "Products")
    assert res is None


def test_find_latest_file_no_matching(tmp_path):
    # create files that don't match naming pattern (module expects names starting with "Products_")
    a = tmp_path / "other_1.json"
    a.write_text("{}")
    b = tmp_path / "ProductsX_1.json"
    b.write_text("{}")
    res = etl.find_latest_file(str(tmp_path), "Products")
    assert res is None


def test_find_latest_file_select_latest(tmp_path):
    # names must start with "Products_" per implementation; second part determines ordering in current sort
    f1 = tmp_path / "Products_2025-01-01_01.json"
    f2 = tmp_path / "Products_2025-01-02_01.json"
    f3 = tmp_path / "Products_2024-12-31_23.json"
    for p in (f1, f2, f3):
        p.write_text("{}")
    res = etl.find_latest_file(str(tmp_path), "Products")
    assert res is not None
    assert res.endswith("Products_2025-01-02_01.json")


def test_transform_products_creates_updateone_and_skips_invalid():
    # valid product
    product_ok = {
        "id": "p1",
        "title_en": "English Title",
        "brand": {"code": "bcode"},
        "category": {"code": "ccode"},
        "specifications": {"group": {"attr": ["v"]}},
        "title_fa": "FA",
        "colors": [{"title": "red"}, {"title": "green"}],
        "rating": {"rate": 4, "count": 10},
        "default_variant": {"price": {"selling_price": 199}},
        "product_badges": [1, 2],
        "suggestion": [42],
        "comments_count": 5,
        "questions_count": 2,
        "comments_overview": {"overview": "ok"},
        "images": {"main": {"url": ["m.jpg"]}, "list": [{"url": ["a.jpg"]}]},
    }
    # missing required fields -> should be skipped
    product_bad = {"id": "p2", "title_en": None, "brand": None, "category": None}

    ops = etl.transform_products([product_ok, product_bad])
    # ensures only one UpdateOne created for the valid product
    assert len(ops) == 1
    op = ops[0]
    # UpdateOne exposes private attrs; check they contain expected values
    assert op._filter == {"_id": "p1"}
    doc = op._doc
    assert "$set" in doc
    setdoc = doc["$set"]
    assert setdoc["title_en"] == "English Title"
    assert setdoc["title_fa"] == "FA"
    assert setdoc["brand"] == "bcode"
    assert "red" in setdoc["colors"]
    assert setdoc["specifications"] == {"group": {"attr": ["v"]}}
    assert "m.jpg" in setdoc["images"]


def test_transform_comments_skips_missing_and_parses_images_and_ids():
    raw = [
        {  # valid
            "product_id": "prod1",
            "title": "t",
            "body": "b",
            "rate": 5,
            "advantages": "good",
            "disadvantages": "bad",
            "is_buyer": True,
            "created_at": "2023-01-01T00:00:00Z",
            "purchased_item": {"color": {"title": "Black"}, "seller": {"title": "SellerA"}},
            "reactions": {"likes": 10, "dislikes": 1},
            "files": [{"url": ["i1.jpg"]}, {"url": ["i2.jpg"]}],
        },
        {  # missing product_id -> skipped
            "title": "noid",
            "body": "b",
        },
    ]
    docs, ids = etl.transform_comments(raw)
    assert len(docs) == 1
    assert ids == ["prod1"]
    doc = docs[0]
    assert doc["product_id"] == "prod1"
    assert "i1.jpg" in doc["images"]
    assert doc["color"] == "Black"
    assert doc["seller"] == "SellerA"
    assert doc["likes"] == 10
    assert doc["dislikes"] == 1


@pytest.mark.asyncio
async def test_extract_product_in_chunks_and_comments_in_chunks(tmp_path, monkeypatch):
    # Prepare product file: list of dicts, each maps a key to list of items
    products = [{"a": [{"id": "p1", "title_en": "a", "brand": {}, "category": {}, "specifications": {}}]},
                {"b": [{"id": "p2", "title_en": "b", "brand": {}, "category": {}, "specifications": {}}]},
                {"c": [{"id": "p3", "title_en": "c", "brand": {}, "category": {}, "specifications": {}}]}]
    products_file = tmp_path / "Products_test.json"
    write_file(products_file, products)
    # Make chunk size small so multiple chunks are produced in test
    monkeypatch.setattr(etl, "CHUNK_SIZE", 2)

    out = []
    async for ch in etl.extract_product_in_chunks(str(products_file)):
        out.append(ch)
    # should create 2 chunks: first 2 items, then 1 item
    assert sum(len(x) for x in out) == 3
    assert len(out) == 2

    # Prepare comments file structure matching expected nested lists
    comment1 = {"product_id": "p1", "body": "ok", "files": [{"url": ["c1.jpg"]}]}
    comment2 = {"product_id": "p2", "body": "ok2", "files": [{"url": ["c2.jpg"]}]}
    comments_raw = [{"brandA": [[comment1], [comment2]]}]
    comments_file = tmp_path / "Comments_test.json"
    write_file(comments_file, comments_raw)
    out_c = []
    async for ch in etl.extract_comments_in_chunks(str(comments_file)):
        out_c.append(ch)
    assert sum(len(x) for x in out_c) == 2


@pytest.mark.asyncio
async def test__process_chunk_async_and_run_chunked_pipeline_concurrently(tmp_path, monkeypatch):
    # Prepare a small product json with 3 items and chunk size 2
    monkeypatch.setattr(etl, "CHUNK_SIZE", 2)
    data = [{"x": [{"id": "p1", "title_en": "1", "brand": {}, "category": {}, "specifications": {}},
                   {"id": "p2", "title_en": "2", "brand": {}, "category": {}, "specifications": {}}]},
            {"y": [{"id": "p3", "title_en": "3", "brand": {}, "category": {}, "specifications": {}}]}]
    path = tmp_path / "Products_test.json"
    write_file(path, data)

    # create a dummy load function which asserts it receives transformed data format and returns a count
    async def fake_load(collection, transformed):
        # transformed is a list[UpdateOne] for products
        return len(transformed)

    # call the low-level processor directly with a single chunk
    chunk = [{"id": "p4", "title_en": "four", "brand": {}, "category": {}, "specifications": {}}]
    # use None executor to let run_in_executor use default (thread) executor
    res = await etl._process_chunk_async(chunk, etl.transform_products, fake_load, None, None)
    assert res == 1

    # run end-to-end pipeline using run_chunked_pipeline_concurrently with fake loader
    class DummyCollection:
        name = "dummy_products"

    total = await etl.run_chunked_pipeline_concurrently(str(path), DummyCollection(), etl.transform_products, fake_load, None, state="product")
    # We had 3 items total, transform produces UpdateOne per item -> fake_load returns count per chunk equal to ops in chunk -> total should be 3
    assert total == 3