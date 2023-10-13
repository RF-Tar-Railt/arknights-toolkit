from arknights_toolkit.update.record import generate
from arknights_toolkit.update.main import fetch
from pathlib import Path
import asyncio


async def main():
    # await fetch(cover=False)
    await generate(Path("exam_pool.json"))


asyncio.run(main())
