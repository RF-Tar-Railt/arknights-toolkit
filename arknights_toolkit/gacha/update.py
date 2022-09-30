"""
Copy from nonebot_plugin_gamedraw
"""
import re
from typing import List

import httpx
from loguru import logger
from lxml import etree

from .model import UpdateChar, UpdateResponse


async def update():
    """
    从方舟官网处获取卡池更新信息

    :return: 更新结果
    """
    async with httpx.AsyncClient() as async_httpx:
        result = (await async_httpx.get("https://ak.hypergryph.com/news.html")).text
        if not result:
            logger.warning("明日方舟 获取公告出错")
            return
        dom = etree.HTML(result, etree.HTMLParser())
        activity_urls = dom.xpath(
            "//ol[@class='articleList' and @data-category-key='ACTIVITY']/li/a/@href"
        )
        up_chars: List[List[UpdateChar]] = [[], [], []]
        pool_img = ""
        for activity_url in activity_urls[:20]:  # 减少响应时间, 10个就够了
            activity_url = f"https://ak.hypergryph.com{activity_url}"
            result = (await async_httpx.get(activity_url)).text
            if not result:
                logger.warning(f"明日方舟 获取公告 {activity_url} 出错")
                continue

            """因为鹰角的前端太自由了，这里重写了匹配规则以尽可能避免因为前端乱七八糟而导致的重载失败"""
            dom = etree.HTML(result, etree.HTMLParser())
            contents = dom.xpath(
                "//div[@class='article-content']/p/text() | //div[@class='article-content']/p/span/text() | //div["
                "@class='article-content']/div[@class='media-wrap image-wrap']/img/@src "
            )
            title = ""
            chars: List[str] = []
            for index, content in enumerate(contents):
                if not re.search("(.*)(寻访|复刻).*?开启", content):
                    continue
                title = re.split(r"[【】]", content)
                title = "".join(title[1:-1]) if "-" in title else title[1]
                lines = [contents[index - 2 + _] for _ in range(8)] + [""]
                for idx, line in enumerate(lines):
                    """因为 <p> 的诡异排版，所以有了下面的一段"""
                    if "★★" in line and "%" in line:
                        chars.append(line)
                    elif "★★" in line and "%" in lines[idx + 1]:
                        chars.append(line + lines[idx + 1])
                pool_img = contents[index - 2]
                r"""两类格式：用/分割，用\分割；★+(概率)+名字，★+名字+(概率)"""
                for char in chars:
                    star = char.split("（")[0].count("★")
                    name = (
                        re.split(r"[（：]", char)[1]
                        if "★（" not in char
                        else re.split("（|）：", char)[2]
                    )
                    names = name.replace("\\", "/").split("/")
                    for name in names:
                        limit = False
                        if "[限定]" in name:
                            limit = True
                        name = name.replace("[限定]", "").strip()
                        zoom = 1.0
                        if match := re.search(r"（在.*?以.*?(\d+).*?倍.*?）", char) or re.search(
                                r"（占.*?的.*?(\d+).*?%）", char
                        ):
                            zoom = float(match[1])
                            zoom = zoom / 100 if zoom > 10 else zoom
                        up_chars[6 - star].append(UpdateChar(name, limit, zoom))
                break  # 这里break会导致个问题：如果一个公告里有两个池子，会漏掉下面的池子，比如 5.19 的定向寻访。但目前我也没啥好想法解决
            if not title:
                continue
            logger.debug(f"成功获取 当前up信息; 当前up池: {title}")
            return UpdateResponse(title, up_chars[2], up_chars[1], up_chars[0], pool_img)
