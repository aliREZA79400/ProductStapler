import asyncio
from pymongo import AsyncMongoClient


async def main():
    uri = "mongodb://localhost:27017"
    client = AsyncMongoClient(uri)

    # Ping the server
    await client.admin.command("ping")
    print("Connected successfully")

    # Select database and collection
    db = client["test_db"]
    collection = db["test_collection"]

    # Create (Insert)
    result = await collection.insert_one({"name": "MongoDB", "type": "Database"})
    print(f"Inserted document id: {result.inserted_id}")

    # Read (Find)
    doc = await collection.find_one({"name": "MongoDB"})
    print(doc)

    # Update
    await collection.update_one(
        {"name": "MongoDB"}, {"$set": {"type": "NoSQL Database"}}
    )

    # Delete
    await collection.delete_one({"name": "MongoDB"})

    await client.close()


asyncio.run(main())
