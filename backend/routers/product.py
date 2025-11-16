from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

from backend.config import MONGO_URI, DB_NAME, PRODUCTS_COLLECTION


router = APIRouter(prefix="/product", tags=["product"])

# MongoDB client for products
mongo_client = AsyncIOMotorClient(MONGO_URI)
products_collection = mongo_client[DB_NAME][PRODUCTS_COLLECTION]


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId to string for JSON serialization."""
    if doc is None:
        return None
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


@router.get("/{product_id}")
async def get_product(product_id: str = Path(..., description="Product ID to retrieve")):
    """
    Get a product by its ID.
    
    - **product_id**: The ID of the product to retrieve (can be ObjectId or string)
    """
    try:
        # Try to convert to ObjectId if it's a valid ObjectId string
        try:
            product_oid = ObjectId(product_id)
            query = {"_id": int(product_oid)}
        except (InvalidId, ValueError):
            # If not a valid ObjectId, search as string
            query = {"_id": int(product_id)}
        # Find the product
        product = await products_collection.find_one(query)
        
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  
                detail=f"Product with id '{product_id}' not found"
            )
        
        # Serialize and return
        return serialize_document(product)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving product: {str(e)}"
        )

