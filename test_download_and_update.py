from arknights_toolkit.update.gacha import generate
from arknights_toolkit.update.main import fetch
from pathlib import Path
import asyncio


async def main():
    await fetch(cover=False)
    await generate(Path("exam_gacha.json"))


asyncio.run(main())
