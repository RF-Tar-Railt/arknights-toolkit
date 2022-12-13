from arknights_toolkit import ArkRecord
from PIL import Image
record = ArkRecord("./cache/img/", "./cache/record.db")
record.user_token_save("A7/6Nx23OGEXEjsJoIc/NUnb", "3165388245")

img: Image.Image = Image.open(record.user_analysis("3165388245"))
img.show('res')
