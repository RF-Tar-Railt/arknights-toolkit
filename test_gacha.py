from arknights_toolkit.gacha import ArknightsGacha, GachaUser
from arknights_toolkit.gacha.simulate import simulate_image
from io import BytesIO
from PIL import Image
import asyncio


async def main():
    gacha = ArknightsGacha("exam_gacha.json")
    user = GachaUser()
    data = gacha.gacha_with_img(user, 300)
    #data = gacha.gacha(user, 300)
    io = BytesIO(data)

    #io = BytesIO(await simulate_image(data[5]))
    image = Image.open(io, "r")
    image.show("res")
    #image.save("example_sim.png")


asyncio.run(main())
