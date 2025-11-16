from typing import Dict, Any
from fastapi import FastAPI, Query, HTTPException, status, Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from backend.config import MONGO_URI, DB_NAME, PRODUCTS_COLLECTION, KEYS_TO_SHOW
from backend.routers.users import router as users_router
from backend.routers.product import router as product_router


app = FastAPI()
app.include_router(users_router)
app.include_router(product_router)

# MongoDB client for products
mongo_client = AsyncIOMotorClient(MONGO_URI)
products_collection = mongo_client[DB_NAME][PRODUCTS_COLLECTION]


def get_nested_value(doc: Dict[str, Any], key_path: str) -> Any:
    """Get value from nested dictionary using dot notation (e.g., 'cluster_info.level1_id')."""
    keys = key_path.split(".")
    value = doc
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    return value


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ObjectId to string for JSON serialization and filter by KEYS_TO_SHOW.
    Only includes keys specified in KEYS_TO_SHOW environment variable.
    """
    if doc is None:
        return None
    
    # If no keys specified, return all keys (backward compatibility)
    if not KEYS_TO_SHOW:
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = serialize_document(value)
            elif isinstance(value, list):
                result[key] = [
                    serialize_document(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    # Filter by KEYS_TO_SHOW
    result = {}
    for key_path in KEYS_TO_SHOW:
        if "." in key_path:
            # Handle nested keys (e.g., "cluster_info.level1_id")
            value = get_nested_value(doc, key_path)
            if value is not None:
                # Use the last part of the key path as the result key
                result_key = key_path.split(".")[-1]
                if isinstance(value, ObjectId):
                    result[result_key] = str(value)
                elif isinstance(value, dict):
                    result[result_key] = serialize_document(value)
                elif isinstance(value, list):
                    result[result_key] = [
                        serialize_document(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    result[result_key] = value
        else:
            # Handle top-level keys
            if key_path in doc:
                value = doc[key_path]
                if isinstance(value, ObjectId):
                    result[key_path] = str(value)
                elif isinstance(value, dict):
                    result[key_path] = serialize_document(value)
                elif isinstance(value, list):
                    result[key_path] = [
                        serialize_document(item) if isinstance(item, dict) else item
                        for item in value
                    ]
                else:
                    result[key_path] = value
    
    return result



@app.get("/")
async def sample_products_by_level1(
    sample_size: int = Query(default=3, ge=1, description="Number of products to sample from each level1_id group"),
    level1_id: int = Query(None, description="Optional: filter by specific level1_id")
):
    """
    Group products by cluster_info.level1_id and randomly sample from each group.
    
    - **sample_size**: Number of products to randomly sample from each level1_id group
    - **level1_id**: Optional filter to only return samples for a specific level1_id
    """
    try:
        # Build match stage - filter by level1_id if provided
        match_stage = {}
        if level1_id is not None:
            match_stage["cluster_info.level1_id"] = level1_id
        
        # First, get distinct level1_id values
        if level1_id is not None:
            distinct_level1_ids = [level1_id]
        else:
            distinct_level1_ids = await products_collection.distinct("cluster_info.level1_id")
        
        if not distinct_level1_ids:
            return {
                "message": "No products found with cluster_info.level1_id",
                "results": {}
            }
        
        # For each level1_id, sample products
        results = {}
        for l1_id in distinct_level1_ids:
            # Build aggregation pipeline for this level1_id
            pipeline = [
                {"$match": {"cluster_info.level1_id": l1_id}},
                {"$sample": {"size": sample_size}}
            ]
            
            # Execute aggregation
            cursor = products_collection.aggregate(pipeline)
            sampled_products = []
            async for doc in cursor:
                sampled_products.append(serialize_document(doc))
            
            results[str(l1_id)] = {
                "level1_id": l1_id,
                "sample_size": len(sampled_products),
                "products": sampled_products
            }
        
        return {
            "message": f"Sampled {sample_size} products from each level1_id group",
            "total_groups": len(distinct_level1_ids),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sampling products: {str(e)}"
        )


@app.get("/sub/{level1_id}")
async def sample_products_by_level2(
    level1_id: int = Path(..., description="level1_id to filter products"),
    sample_size: int = Query(default=3, ge=1, description="Number of products to sample from each level2_id group")
):
    """
    Group products by cluster_info.level2_id for a given level1_id and randomly sample from each level2_id group.
    
    - **level1_id**: Path parameter - filter products by this level1_id
    - **sample_size**: Number of products to randomly sample from each level2_id group
    """
    try:
        # First, check if any products exist with this level1_id
        count = await products_collection.count_documents({"cluster_info.level1_id": level1_id})
        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No products found with cluster_info.level1_id={level1_id}"
            )
        
        # Get distinct level2_id values for this level1_id
        distinct_level2_ids = await products_collection.distinct(
            "cluster_info.level2_id",
            {"cluster_info.level1_id": level1_id}
        )
        
        if not distinct_level2_ids:
            return {
                "message": f"No products found with cluster_info.level1_id={level1_id}",
                "level1_id": level1_id,
                "results": {}
            }
        
        # For each level2_id, sample products
        results = {}
        for l2_id in distinct_level2_ids:
            # Build aggregation pipeline for this level2_id
            pipeline = [
                {
                    "$match": {
                        "cluster_info.level1_id": level1_id,
                        "cluster_info.level2_id": l2_id
                    }
                },
                {"$sample": {"size": sample_size}}
            ]
            
            # Execute aggregation
            cursor = products_collection.aggregate(pipeline)
            sampled_products = []
            async for doc in cursor:
                sampled_products.append(serialize_document(doc))
            
            results[str(l2_id)] = {
                "level1_id": level1_id,
                "level2_id": l2_id,
                "sample_size": len(sampled_products),
                "products": sampled_products
            }
        
        return {
            "message": f"Sampled {sample_size} products from each level2_id group for level1_id={level1_id}",
            "level1_id": level1_id,
            "total_groups": len(distinct_level2_ids),
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sampling products: {str(e)}"
        )


@app.get("/sub/{level1_id}/sub-sub/{level2_id}")
async def sample_products_by_level3(
    level1_id: int = Path(..., description="level1_id to filter products"),
    level2_id: int = Path(..., description="level2_id to filter products"),
    sample_size: int = Query(default=3, ge=1, description="Number of products to sample from each level3_id group")
):
    """
    Group products by cluster_info.level3_id for given level1_id and level2_id, and randomly sample from each level3_id group.
    
    - **level1_id**: Path parameter - filter products by this level1_id
    - **level2_id**: Path parameter - filter products by this level2_id
    - **sample_size**: Number of products to randomly sample from each level3_id group
    """
    try:
        # First, check if any products exist with this level1_id and level2_id
        filter_query = {
            "cluster_info.level1_id": level1_id,
            "cluster_info.level2_id": level2_id
        }
        count = await products_collection.count_documents(filter_query)
        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No products found with cluster_info.level1_id={level1_id} and cluster_info.level2_id={level2_id}"
            )
        
        # Get distinct level3_id values for this level1_id and level2_id
        distinct_level3_ids = await products_collection.distinct(
            "cluster_info.level3_id",
            filter_query
        )
        
        if not distinct_level3_ids:
            return {
                "message": f"No products found with cluster_info.level1_id={level1_id} and cluster_info.level2_id={level2_id}",
                "level1_id": level1_id,
                "level2_id": level2_id,
                "results": {}
            }
        
        # For each level3_id, sample products
        results = {}
        for l3_id in distinct_level3_ids:
            # Build aggregation pipeline for this level3_id
            pipeline = [
                {
                    "$match": {
                        "cluster_info.level1_id": level1_id,
                        "cluster_info.level2_id": level2_id,
                        "cluster_info.level3_id": l3_id
                    }
                },
                {"$sample": {"size": sample_size}}
            ]
            
            # Execute aggregation
            cursor = products_collection.aggregate(pipeline)
            sampled_products = []
            async for doc in cursor:
                sampled_products.append(serialize_document(doc))
            
            results[str(l3_id)] = {
                "level1_id": level1_id,
                "level2_id": level2_id,
                "level3_id": l3_id,
                "sample_size": len(sampled_products),
                "products": sampled_products
            }
        
        return {
            "message": f"Sampled {sample_size} products from each level3_id group for level1_id={level1_id} and level2_id={level2_id}",
            "level1_id": level1_id,
            "level2_id": level2_id,
            "total_groups": len(distinct_level3_ids),
            "results": results
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sampling products: {str(e)}"
        )


