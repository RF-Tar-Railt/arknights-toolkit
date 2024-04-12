from arknights_toolkit.update.record import generate as record_generate
from arknights_toolkit.update.gacha import generate as gacha_generate
from arknights_toolkit.update.main import fetch
from pathlib import Path
import asyncio


async def main():
    # await fetch(cover=False)
    await gacha_generate(Path("exam_gacha.json"), proxy="http://127.0.0.1:7897")
    # await record_generate(Path("exam_pool.json"), proxy="http://127.0.0.1:7897")


asyncio.run(main())
