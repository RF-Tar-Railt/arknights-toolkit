from arknights_toolkit import ArknightsGacha
import asyncio


async def main():
    gacha = ArknightsGacha()
    await gacha.update()
    await gacha.initialize()


asyncio.run(main())
