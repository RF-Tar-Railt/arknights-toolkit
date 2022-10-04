import asyncio
import json
import re
from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from loguru import logger
from lxml import etree
from PIL import Image

char_pat = re.compile(r"\|职业=(.+?)\n\|.+?")

career = {}
base_path = Path(__file__).parent.parent / "resource" / "operators"
base_path.mkdir(parents=True, exist_ok=True)
if (base_path.parent / "careers.json").exists():
    with (base_path.parent / "careers.json").open("r", encoding="utf-8") as f:
        career.update(json.load(f))


async def download(ops: List[str], retry: int = 5):
    async with httpx.AsyncClient() as async_httpx:
        for name in ops:
            if (base_path / f"{name}.png").exists():
                continue
            while retry:
                try:
                    resp = await async_httpx.get(
                        f"https://prts.wiki/w/文件:半身像_{name}_1.png", timeout=20.0
                    )
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
                    ).crop((20, 0, 124 + 20, 360))
                    with (base_path / f"{name}.png").open("wb+") as img:
                        avatar.save(
                            img,
                            format="PNG",
                            quality=100,
                            subsampling=2,
                            qtables="web_high",
                        )
                    resp1 = await async_httpx.get(
                        f"https://prts.wiki/index.php?title={name}&action=edit"
                    )
                    root1 = etree.HTML(resp1.text)
                    sub1 = root1.xpath('//textarea[@id="wpTextbox1"]')[0]
                    career[name] = char_pat.search(sub1.text)[1]
                    logger.success(f"{name}({career[name]}) saved")
                    break
                except Exception as e:
                    retry -= 1
                    logger.warning(f"Fetch {name} failed. Caused by {e}")
                    logger.debug("Retrying...")
                    await asyncio.sleep(2)
            if not retry:
                with (base_path.parent / "careers.json").open(
                    "w+", encoding="utf-8"
                ) as f:
                    json.dump(career, f, ensure_ascii=False)
                logger.critical(f"Fetch {name} failed. Exiting...")
                return
            await asyncio.sleep(3)
        with (base_path.parent / "careers.json").open("w+", encoding="utf-8") as f:
            json.dump(career, f, ensure_ascii=False)
        with (base_path.parent / "ops_initialized").open("w+", encoding="utf-8") as f:
            f.write("initialized")
