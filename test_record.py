import asyncio

from PIL import Image

from arknights_toolkit.record import ArkRecord

record = ArkRecord("./cache/img/", "./cache/record.db")
record.user_token_save("A7/6Nx23OGEXEjsJoIc/NUnb", "3165388245")


async def main():
    img: Image.Image = Image.open((await record.user_analysis("3165388245"))[1])
    img.show("res")


asyncio.run(main())
