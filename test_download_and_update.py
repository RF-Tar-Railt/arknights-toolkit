from arknights_toolkit import initialize
import asyncio

initialize(cover=True)


async def main():
    from arknights_toolkit import ArknightsGacha
    gacha = ArknightsGacha()
    await gacha.update()


asyncio.run(main())
