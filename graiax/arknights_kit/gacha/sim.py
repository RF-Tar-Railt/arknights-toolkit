import json
import re
from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from loguru import logger
from lxml import etree
from PIL import Image, ImageEnhance

from .model import Operator

resource_path = Path(__file__).parent.parent / "resource"
char_pat = re.compile(r"\|职业=(.+?)\n\|.+?")

six_bgi = Image.open(resource_path / "back_six.png")
five_bgi = Image.open(resource_path / "back_five.png")
four_bgi = Image.open(resource_path / "back_four.png")
low_bgi = Image.new("RGBA", (124, 360), (49, 49, 49))
six_tail = Image.open(resource_path / "six_02.png")

six_line = Image.open(resource_path / "six_01.png")
five_line = Image.open(resource_path / "five.png")
four_line = Image.open(resource_path / "four.png")

star_circle = Image.open(resource_path / "star_02.png")
enhance_five_line = Image.new("RGBA", (124, 720), (0x60, 0x60, 0x60, 0x50))
enhance_four_line = Image.new("RGBA", (124, 720), (132, 108, 210, 0x10))
brighter = ImageEnhance.Brightness(six_line)
six_line = brighter.enhance(1.5)
brighter = ImageEnhance.Brightness(four_line)
four_line = brighter.enhance(0.9)
six_line_up = six_line.crop((0, 0, six_line.size[0], 256))
six_line_down = six_line.crop((0, 256, six_line.size[0], 512))
five_line_up = five_line.crop((0, 0, five_line.size[0], 256))
five_line_down = five_line.crop((0, 256, five_line.size[0], 512))
four_line_up = four_line.crop((0, 0, four_line.size[0], 256))
four_line_down = four_line.crop((0, 256, four_line.size[0], 512))
logger.debug("basic image loaded.")
characters = {
    "先锋": Image.open(resource_path / "图标_职业_先锋_大图_白.png"),
    "近卫": Image.open(resource_path / "图标_职业_近卫_大图_白.png"),
    "医疗": Image.open(resource_path / "图标_职业_医疗_大图_白.png"),
    "术师": Image.open(resource_path / "图标_职业_术师_大图_白.png"),
    "狙击": Image.open(resource_path / "图标_职业_狙击_大图_白.png"),
    "特种": Image.open(resource_path / "图标_职业_特种_大图_白.png"),
    "辅助": Image.open(resource_path / "图标_职业_辅助_大图_白.png"),
    "重装": Image.open(resource_path / "图标_职业_重装_大图_白.png"),
}
logger.debug("careers image loaded.")
stars = {
    5: Image.open(resource_path / "稀有度_白_5.png"),
    4: Image.open(resource_path / "稀有度_白_4.png"),
    3: Image.open(resource_path / "稀有度_白_3.png"),
    2: Image.open(resource_path / "稀有度_白_2.png"),
}
logger.debug("stars image loaded.")
with (resource_path / "careers.json").open("r", encoding="utf-8") as f:
    careers = json.load(f)
operators = {
    path.stem: Image.open(path) for path in (resource_path / "operators").iterdir()
}
logger.debug("operators image loaded.")


async def simulate_ten_generate(ops: List[Operator]):
    base = 20
    offset = 124
    l_offset = 14
    back_img = Image.open(resource_path / "back_image.png")
    async with httpx.AsyncClient() as async_httpx:
        for op in ops:
            name = op.name
            rarity = op.rarity - 1
            try:
                if name in operators:
                    avatar: Image.Image = operators[name]
                    logo: Image.Image = characters[careers[name]].resize(
                        (96, 96), Image.Resampling.LANCZOS
                    )
                else:
                    resp = await async_httpx.get(f"https://prts.wiki/w/文件:半身像_{name}_1.png")
                    root = etree.HTML(resp.text)
                    sub = root.xpath(f'//img[@alt="文件:半身像 {name} 1.png"]')[0]
                    avatar: Image.Image = Image.open(
                        BytesIO(
                            (
                                await async_httpx.get(
                                    f"https://prts.wiki{sub.xpath('@src').pop()}"
                                )
                            ).read()
                        )
                    ).crop((20, 0, offset + 20, 360))
                    with (resource_path / "operators" / f"{name}.png").open("wb+") as _f:
                        avatar.save(
                            _f, format="PNG", quality=100, subsampling=2, qtables="web_high"
                        )
                    resp1 = await async_httpx.get(
                        f"https://prts.wiki/index.php?title={name}&action=edit"
                    )
                    root1 = etree.HTML(resp1.text)
                    sub1 = root1.xpath('//textarea[@id="wpTextbox1"]')[0]
                    cr = char_pat.search(sub1.text)[1]
                    logo: Image.Image = characters[cr].resize(
                        (96, 96), Image.Resampling.LANCZOS
                    )
                    with (resource_path / "careers.json").open("w", encoding="utf-8") as jf:
                        careers[name] = cr
                        json.dump(careers, jf, ensure_ascii=False)
            except (ValueError, IndexError):
                resp = await async_httpx.get("https://prts.wiki/w/文件:半身像_无_1.png")
                root = etree.HTML(resp.text)
                sub = root.xpath('//img[@alt="文件:半身像 无 1.png"]')[0]
                logo: Image.Image = characters["近卫"].resize(
                    (96, 96), Image.Resampling.LANCZOS
                )
                avatar: Image.Image = Image.open(
                    BytesIO(
                        (
                            await async_httpx.get(
                                f"https://prts.wiki{sub.xpath('@src').pop()}"
                            )
                        ).read()
                    )
                ).crop((20, 0, offset + 20, 360))

            s_size = stars[rarity].size
            star = stars[rarity].resize(
                (int(s_size[0] * 0.6), int(47 * 0.6)), Image.Resampling.LANCZOS
            )
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
            format="PNG",
            quality=80,
            subsampling=2,
            qtables="web_high",
        )
        return imageio.getvalue()
