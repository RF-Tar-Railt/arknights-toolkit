from arknights_toolkit.record import ArkRecord
from PIL import Image
import asyncio
record = ArkRecord("./cache/img/", "./cache/record.db")
record.user_token_save("A7/6Nx23OGEXEjsJoIc/NUnb", "3165388245")

async def main():
    img: Image.Image = Image.open(await record.user_analysis("3165388245"))
    img.show('res')

asyncio.run(main())
