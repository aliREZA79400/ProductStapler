import mlflow
from mlflow import sklearn
from motor.motor_asyncio import AsyncIOMotorClient
from .config import (
    MONGO_URI,
    DB_NAME,
    PRODUCTS_COLLECTION,
    MLFLOW_TRACKING_URI,
    MODEL_NAME,
    MODEL_VERSION,
)


mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# Load the model from the Model Registry
model_uri = f"models:/{MODEL_NAME}/{MODEL_VERSION}"

model = sklearn.load_model(model_uri)

# all_products_cluster_info = model.sample_assignments
# print(all_products_cluster_info)
client = AsyncIOMotorClient(str(MONGO_URI))
db = client[str(DB_NAME)]
products_collection = db[str(PRODUCTS_COLLECTION)]


async def update_products_cluster_info():
    """
    Update products with cluster information using all_products_cluster_info data.
    If not found, use model.predict to assign cluster info.
    Uses extract_features_to_X from ml.preprocessing.
    """
    from ml.preprocessing import Preprocessor

    # Convert list of dicts to dict with id as key for faster lookup
    # cluster_info_map = {item["id"]: item for item in all_products_cluster_info}

    # Pre-load the preprocessing pipeline
    preprocessing = Preprocessor()

    def extract_features_to_X(product):
        """
        Converts a product dict to a feature vector suitable for model.predict
        This assumes product is a dictionary like from MongoDB.
        """
        import pandas as pd

        # Put product into single-row DataFrame
        df = pd.DataFrame([product])
        # Only use columns present in the preprocessing pipeline
        # If columns are missing, we just let the transformers impute/fail as designed
        X_array = preprocessing.transform(df)
        # If more than 1D output, flatten or select first row
        if X_array.shape[0] == 1:  # pyright:ignore
            return X_array[0]
        return X_array

    # Find all products that need updating
    # TODO updating products with new model (use all products with exists True)
    cursor = products_collection.find({})

    async for product in cursor:
        try:
            try:
                X_query = extract_features_to_X(product)
                pred_result = model.predict([X_query])[0]  # pyright:ignore
                cluster_info = {
                    "level1_id": pred_result.get("level1_id"),
                    "level2_id": pred_result.get("level2_id"),
                    "level3_id": pred_result.get("level3_id"),
                }
            except Exception as ee:
                print(
                    f"Error extracting features or predicting for product {product.get('_id')}: {str(ee)}"
                )
                continue  # skip updating if can't extract/predict

            # Update the product with cluster information
            await products_collection.update_one(
                {"_id": product["_id"]}, {"$set": {"cluster_info": cluster_info}}
            )

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
