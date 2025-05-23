import json
import random
from io import BytesIO
from typing import List, Optional

import httpx
from PIL import ImageDraw, ImageFont
from httpx._types import ProxyTypes

from ..images import *
from .model import Operator
from ..update.main import fetch_info, fetch_image

resource_path = Path(__file__).parent.parent / "resource"

font_base = ImageFont.truetype(str((resource_path / "HarmonyOS_Sans_SC_Medium.ttf").absolute()), 32)


async def simulate_image(ops: List[Operator], proxy: Optional[ProxyTypes] = None):
    """
    依据抽卡结果生成模拟十连图片

    :param ops: 抽卡结果
    :param proxy: 代理
    :return: 图片的bytes
    """
    base = 20
    offset = 124
    l_offset = 14
    back_img = Image.new("RGB", (1280, 720), (0, 0, 0))
    back_img.paste(Image.open(resource_path / "gacha" / "back_image.png"), (0, 0))
    with (resource_path / "info.json").open("r", encoding="utf-8") as f:
        infos = json.load(f)
        table = infos["table"]
    async with httpx.AsyncClient(verify=False, proxy=proxy) as async_httpx:
        for op in ops[:10]:
            name = op.name
            rarity = op.rarity - 1
            try:
                if name in operators and name in table:
                    avatar: Image.Image = operators[name]
                    logo: Image.Image = characters[table[name]["career"][:2]].resize(
                        (96, 96), Image.Resampling.LANCZOS
                    )
                else:
                    info = await fetch_info(name, async_httpx)
                    avatar = await fetch_image(name, info["id"], async_httpx, 1)  # type: ignore
                    if not avatar:
                        raise ValueError
                    logo: Image.Image = characters[info["career"][:2]].resize(
                        (96, 96), Image.Resampling.LANCZOS
                    )
                    with (resource_path / "info.json").open("w+", encoding="utf-8") as jf:
                        table[name] = info
                        json.dump(infos, jf, ensure_ascii=False, indent=2)
            except (
                AttributeError,
                TypeError,
                ValueError,
                IndexError,
                httpx.TimeoutException,
                httpx.ConnectError,
            ):
                logo: Image.Image = characters[random.choice(list(characters))].resize(
                    (96, 96), Image.Resampling.LANCZOS
                )
                avatar: Image.Image = Image.open(
                    Path(__file__).parent.parent / "resource" / "gacha" / "半身像_无_1.png"
                ).resize((offset, 360), Image.Resampling.LANCZOS)
                _draw = ImageDraw.Draw(avatar)
                _draw.text((46, 100), "\n".join(name), fill="white", font=font_base)
            s_size = stars[rarity].size
            star = stars[rarity].resize((int(s_size[0] * 0.6), int(47 * 0.6)), Image.Resampling.LANCZOS)
            s_offset = (offset - int(star.size[0])) // 2

            if rarity == 5:
                back_img.paste(six_line_up, (base, 0), six_line_up)
                back_img.paste(six_line_down, (base, 720 - 256), six_line_down)
                back_img.paste(six_tail, (base, 0), six_tail)
                back_img.paste(
                    six_tail.transpose(Image.Transpose.ROTATE_180),
                    (base, 720 - 256),
                    six_tail.transpose(Image.Transpose.ROTATE_180),
                )
                basei = six_bgi.copy()
            elif rarity == 4:
                back_img.paste(enhance_five_line, (base, 0), enhance_five_line)
                back_img.paste(five_line_up, (base, 0), five_line_up)
                back_img.paste(five_line_down, (base, 720 - 256), five_line_down)
                basei = five_bgi.copy()
            elif rarity == 3:
                back_img.paste(enhance_four_line, (base, 0), enhance_four_line)
                back_img.paste(four_line_up, (base, 0), four_line_up)
                back_img.paste(four_line_down, (base, 720 - 256), four_line_down)
                back_img.paste(star_circle, (base - 2, 180 - 64), star_circle)
                basei = four_bgi.copy()
            else:
                basei = low_bgi.copy()
            size = avatar.size
            avatar.thumbnail(size)
            basei.paste(avatar, (0, 0), avatar)
            back_img.paste(basei, (base, 180))
            s_size = star.size
            star.thumbnail(s_size)
            back_img.paste(star, (base + s_offset, 166), star)
            l_size = logo.size
            logo.thumbnail(l_size)
            back_img.paste(logo, (base + l_offset, 492), logo)
            base += offset
        imageio = BytesIO()
        back_img.save(
            imageio,
            format="JPEG",
            quality=95,
            subsampling=2,
            qtables="web_high",
        )
        update_operators()
        return imageio.getvalue()
