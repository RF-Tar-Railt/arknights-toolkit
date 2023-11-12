from arknights_toolkit.update.record import generate
from arknights_toolkit.update.main import fetch
from pathlib import Path
import asyncio


async def main():
    # await fetch(cover=False)
    await generate(Path("exam_pool.json"), proxy="http://127.0.0.1:7890")


asyncio.run(main())
