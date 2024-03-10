import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, NamedTuple, Optional

from httpx import AsyncClient, ConnectError, TimeoutException
from httpx._types import ProxiesTypes
from loguru import logger
from lxml import etree


class UpdateChar(NamedTuple):
    name: str
    limit: bool
    chance: float


@dataclass
class UpdateResponse:
    title: str
    four_chars: List[UpdateChar]
    five_chars: List[UpdateChar]
    six_chars: List[UpdateChar]
    pool: str


pat1 = re.compile(r"(.*)(寻访|复刻).*?开启")
pat2 = re.compile(r"[【】]")
pat3 = re.compile(r"[（：]")
pat4 = re.compile(r"（|）：")
pat5 = re.compile(r"（在.*?以.*?(\d+).*?倍.*?）")
pat6 = re.compile(r"（占.*?的.*?(\d+).*?%）")


def fetch_chars(dom):
    contents = dom.xpath(
        "//div[@class='article-content']/p/text() | //div[@class='article-content']/p/span/text() | //div["
        "@class='article-content']/div[@class='media-wrap image-wrap']/img/@src "
    )
    title = ""
    pool_img = ""
    chars: List[str] = []
    up_chars: List[List[UpdateChar]] = [[], [], []]
    for index, content in enumerate(contents):
        if not pat1.search(content):
            continue
        title = pat2.split(content)
        title = "".join(title[1:-1]) if "-" in title else title[1]
        lines = [contents[index + _] for _ in range(8)] + [""]
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
            name = pat3.split(char)[1] if "★（" not in char else pat4.split(char)[2]
            names = name.replace("\\", "/").split("/")
            for name in names:
                limit = False
                if "[限定]" in name:
                    limit = True
                name = name.replace("[限定]", "").strip()
                zoom = 1.0
                if match := pat5.search(char) or pat6.search(char):
                    zoom = float(match[1])
                    zoom = zoom / 100 if zoom > 10 else zoom
                up_chars[6 - star].append(UpdateChar(name, limit, zoom))
        break  # 这里break会导致个问题：如果一个公告里有两个池子，会漏掉下面的池子，比如 5.19 的定向寻访。但目前我也没啥好想法解决
    return title, pool_img, up_chars


async def update(proxy: Optional[ProxiesTypes] = None):
    async with AsyncClient(verify=False, proxies=proxy) as client:
        result = (await client.get("https://ak.hypergryph.com/news.html")).text
        if not result:
            logger.warning("明日方舟 获取公告出错")
            raise TimeoutException("未找到明日方舟公告")
        dom = etree.HTML(result, etree.HTMLParser())
        activity_urls = dom.xpath(
            "//ol[@class='articleList' and @data-category-key='ACTIVITY']/li/a/@href"
        )
        # 按照公告的时间排序
        activity_urls.sort(key=lambda x: x.split("/")[-1], reverse=True)
        for activity_url in activity_urls[:20]:  # 减少响应时间, 10个就够了
            activity_url = f"https://ak.hypergryph.com{activity_url}"
            result = (await client.get(activity_url)).text
            if not result:
                logger.warning(f"明日方舟 获取公告 {activity_url} 出错")
                continue

            """因为鹰角的前端太自由了，这里重写了匹配规则以尽可能避免因为前端乱七八糟而导致的重载失败"""
            dom = etree.HTML(result, etree.HTMLParser())
            title, pool_img, up_chars = fetch_chars(dom)
            if not title or title.startswith("跨年欢庆"):
                continue
            logger.debug(f"成功获取 当前up信息; 当前up池: {title}")
            return UpdateResponse(
                title, up_chars[2], up_chars[1], up_chars[0], pool_img
            )
        raise TimeoutException("未找到明日方舟公告")


async def fetch(table: dict, proxy: Optional[ProxiesTypes] = None):
    base_url = "https://prts.wiki/w/%E5%8D%A1%E6%B1%A0%E4%B8%80%E8%A7%88"
    async with AsyncClient(verify=False, proxies=proxy) as client:
        base = await client.get(base_url, timeout=30)
        root = etree.HTML(base.text, etree.HTMLParser())
        _table: etree._Element = root.xpath(
            "//table[@class='wikitable mw-collapsible fullline logo']"
        )[0]
        tbody: etree._Element = _table.getchildren()[0]
        trs: List[etree._Element] = tbody.getchildren()
        tds: List[etree._Element] = trs[2].getchildren()
        href = tds[0].find("a", None).get("href")
        link = f"https://prts.wiki{href}"
        if href.count("/") == 3:
            page = await client.get(link, timeout=30)
            root1 = etree.HTML(page.text, etree.HTMLParser())
            data = root1.xpath("//script[@id='data_operator']")[0].text.splitlines()
        else:
            page1 = await client.get(link, timeout=30)
            root2 = etree.HTML(page1.text, etree.HTMLParser())
            href1 = (
                root2.xpath("//div[@class='mw-parser-output']")[0]
                .getchildren()[1]
                .getchildren()[1]
                .getchildren()[0]
                .get("href")
            )
            link1 = f"https://prts.wiki{href1}"
            page2 = await client.get(link1, timeout=30)
            root3 = etree.HTML(page2.text, etree.HTMLParser())
            data = root3.xpath("//script[@id='data_operator']")[0].text.splitlines()

        for opt in data[1:]:
            if not opt[0].isdigit():
                continue
            rows = opt.split(",")[1:]
            table[rows[0]] = {
                "rarity": int(rows[1]) + 1,
                "approach": rows[2].split(" "),
                "is_old": datetime.fromisoformat(rows[3][:10])
                < datetime.fromisoformat("2020-05-01"),
            }


def make(table: dict, pool: dict):
    """生成卡池信息"""
    for name, info in table.items():
        if info["is_old"]:
            continue
        if "标准寻访" not in info["approach"]:
            continue
        if info["rarity"] == 6:
            if name in pool["up_six_list"]:
                continue
            pool["operators"]["六"].append(name)
        elif info["rarity"] == 5:
            if name in pool["up_five_list"]:
                continue
            pool["operators"]["五"].append(name)
        elif info["rarity"] == 4:
            if name in pool["up_four_list"]:
                continue
            pool["operators"]["四"].append(name)


async def generate(file: Path, proxy: Optional[ProxiesTypes] = None):
    try:
        response = await update(proxy)
    except (TimeoutException, ConnectError) as e:
        logger.warning(f"明日方舟 获取公告出错: {type(e)}({e})\n请检查网络或代理设置")
        return
    pool = {
        "name": response.title,
        "six_per": 0.5,
        "five_per": 0.5,
        "four_per": 0.2,
        "up_limit": [],
        "up_alert_limit": [],
        "up_five_list": [],
        "up_six_list": [],
        "up_four_list": [],
        "operators": {
            "三": [
                "空爆",
                "克洛丝",
                "史都华德",
                "炎熔",
                "香草",
                "翎羽",
                "芬",
                "玫兰莎",
                "月见夜",
                "泡普卡",
                "卡缇",
                "米格鲁",
                "斑点",
                "安赛尔",
                "芙蓉",
                "梓兰",
            ],
            "四": [],
            "五": [],
            "六": [],
        },
    }
    for char in response.six_chars:
        if char.limit:
            if not pool["up_limit"]:
                pool["up_limit"].append(char.name)
            else:
                pool["up_alert_limit"].append(char.name)
                continue
        else:
            pool["up_six_list"].append(char.name)
        pool["six_per"] = char.chance
    for char in response.five_chars:
        pool["up_five_list"].append(char.name)
        pool["five_per"] = char.chance
    for char in response.four_chars:
        pool["up_four_list"].append(char.name)
        pool["four_per"] = char.chance
    tablefile = Path(__file__).parent.parent / "resource" / "gacha" / "table.json"
    table = {}
    try:
        await fetch(table, proxy)
        with tablefile.open("w+", encoding="utf-8") as f:
            json.dump(table, f, ensure_ascii=False, indent=2)
    except (TimeoutException, ConnectError):
        if tablefile.exists():
            with tablefile.open("r", encoding="utf-8") as f:
                table = json.load(f)
        else:
            logger.warning("明日方舟 获取卡池干员出错\n请检查网络或代理设置")
    make(table, pool)
    with file.open("w+", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)
    logger.info(f"明日方舟 卡池信息已更新: {response.title}")
    return response
