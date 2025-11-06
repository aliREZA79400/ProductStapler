import os
from contextlib import asynccontextmanager
from typing import Any, List

from bson import ObjectId
from fastapi import FastAPI, Response, Query
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

mongo_client: AsyncIOMotorClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    try:
        yield
    finally:
        if mongo_client:
            mongo_client.close()


app = FastAPI(lifespan=lifespan)


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "digikala")
PRODUCTS_COLLECTION = os.getenv("PRODUCTS_COLLECTION", "products")


def _serialize_id(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    return value


def _serialize_doc(doc: dict) -> dict:
    return {k: _serialize_id(v) for k, v in doc.items()}


@app.get("/")
async def root(limit: int = Query(5, ge=1, le=1000)):
    db = mongo_client[DB_NAME]
    coll = db[PRODUCTS_COLLECTION]
    cursor = coll.aggregate([{"$sample": {"size": limit}}])
    docs: List[dict] = []
    async for d in cursor:
        docs.append(_serialize_doc(d))
    return JSONResponse(content=docs)


@app.get("/collections")
async def list_collections() -> JSONResponse:
    db = mongo_client[DB_NAME]
    collection_names = await db.list_collection_names()
    results: List[dict] = []
    for name in collection_names:
        count = await db[name].count_documents({})
        results.append({"collection": name, "count": count})
    return JSONResponse(content=results)


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)

