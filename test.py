from graiax.arkkit import ArknightsGacha, GachaUser, simulate_ten_generate
from io import BytesIO
from PIL import Image
import asyncio


async def main():
    gacha = ArknightsGacha()
    user = GachaUser()
    data = gacha.gacha(user, 30)
    io = BytesIO(await simulate_ten_generate(data[2]))
    image = Image.open(io, "r")
    image.show("res")
    image.save("example_sim.png")


asyncio.run(main())
