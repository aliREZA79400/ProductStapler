import os

import mlflow
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "digikala")
PRODUCTS_COLLECTION = os.getenv("PRODUCTS_COLLECTION", "products")


# Allow overriding tracking via env
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


# Model selection via env
model_name = os.getenv("MODEL_NAME", "Linkage")
model_version = os.getenv("MODEL_VERSION", "2")

# Load the model from the Model Registry
model_uri = f"models:/{model_name}/{model_version}"

model = mlflow.sklearn.load_model(model_uri)

all_products_cluster_info = model.sample_assignments
print(all_products_cluster_info)
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
products_collection = db[PRODUCTS_COLLECTION]


async def update_products_cluster_info():
    """
    Update products with cluster information using all_products_cluster_info data.
    """
    # Convert list of dicts to dict with id as key for faster lookup
    cluster_info_map = {item["id"]: item for item in all_products_cluster_info}

    # Find all products that need updating
    cursor = products_collection.find({"cluster_info": {"$exists": False}})

    async for product in cursor:
        try:
            if product["_id"] in cluster_info_map:
                cluster_info = {
                    "level1_id": cluster_info_map[product["_id"]]["level1_id"],
                    "level2_id": cluster_info_map[product["_id"]]["level2_id"],
                    "level3_id": cluster_info_map[product["_id"]]["level3_id"],
                }

                # Update the product with cluster information
                await products_collection.update_one(
                    {"_id": product["_id"]}, {"$set": {"cluster_info": cluster_info}}
                )
            else:
                print(f"No cluster info found for product {product['_id']}")

        except Exception as e:
            print(f"Error processing product {product.get('_id')}: {str(e)}")


if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            print("Starting product cluster info update...")
            await update_products_cluster_info()
            print("Finished updating product cluster info")
        finally:
            # Close the MongoDB connection
            client.close()

    # Run the async main function
    asyncio.run(main())
