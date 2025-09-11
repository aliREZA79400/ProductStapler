import asyncio
import json
from typing import Any

import aiofiles

file_path = "./data/digikala/original_data/2025-08-24_16-36-04_products.json"


async def extract_data(file_path: str) -> Any:
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error {e}")
        return None


if __name__ == "__main__":
    content = asyncio.run(extract_data(file_path=file_path))
    print(f"len content {len(content)}")
    print(f"Type content : {type(content)}")
    print(f"Type each item of content : {type(content[0])}")
    print(f"Type each item of item of content : {type(content[0]['51748'])}")
