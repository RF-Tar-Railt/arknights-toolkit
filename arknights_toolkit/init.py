import json
import re
from io import BytesIO
from pathlib import Path
from typing import List

import httpx
from loguru import logger
from lxml import etree
from PIL import Image

__all__ = ["initialize"]

rarity_pat = re.compile(r"\|稀有度=(\d+?)\n\|.+?")
char_pat = re.compile(r"\|职业=([^|]+?)\n\|.+?")
sub_char_pat = re.compile(r"\|分支=([^|]+?)\n\|.+?")
race_pat = re.compile(r"\|种族=([^|]+?)\n\|.+?")
org_pat = re.compile(r"\|所属国家=([^|]+?)\n\|.+?")
org_pat1 = re.compile(r"\|所属组织=([^|]+?)\n\|.+?")
org_pat2 = re.compile(r"\|所属团队=([^|]+?)\n\|.+?")
art_pat = re.compile(r"\|画师=([^|]+?)\n\|.+?")

career = {}
base_path = Path(__file__).parent / "resource"
operate_path = base_path / "operators"
operate_path.mkdir(parents=True, exist_ok=True)
wordle_path = base_path / "wordle"
record_path = base_path / "record"
if (base_path / "careers.json").exists():
    with (base_path / "careers.json").open("r", encoding="utf-8") as f:
        career.update(json.load(f))

all_orgs = set()
if (wordle_path / "relations.json").exists():
    with (wordle_path / "relations.json").open("r", encoding="utf-8") as f:
        operators = json.load(f)
else:
    operators = {
        "detail": "org_related 写的是目标->猜测的关系，目标为key",
        "org_related": {
            "汐斯塔": ["哥伦比亚", "黑钢国际", "莱茵生命"],
            "叙拉古": ["贾维团伙"],
            "乌萨斯学生自治团": ["乌萨斯", "罗德岛"],
            "格拉斯哥帮": ["维多利亚", "罗德岛"],
            "罗德岛": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P",
                "行动预备组A6",
                "行动组A4",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "雷姆必拓": [],
            "伊比利亚": [],
            "萨尔贡": [],
            "贾维团伙": ["叙拉古"],
            "莱茵生命": ["哥伦比亚", "黑钢国际", "汐斯塔"],
            "维多利亚": ["格拉斯哥帮"],
            "鲤氏侦探事务所": ["炎-龙门", "炎-岁", "炎", "龙门近卫局", "企鹅物流"],
            "罗德岛-精英干员": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P",
                "行动预备组A6",
                "行动组A4",
                "巴别塔",
                "罗德岛",
            ],
            "莱塔尼亚": [],
            "米诺斯": [],
            "拉特兰": [],
            "龙门近卫局": ["炎-龙门", "炎-岁", "炎", "鲤氏侦探事务所", "企鹅物流"],
            "黑钢国际": ["汐斯塔", "哥伦比亚", "莱茵生命"],
            "卡西米尔": ["红松骑士团"],
            "企鹅物流": ["炎-龙门", "炎-岁", "炎", "鲤氏侦探事务所", "龙门近卫局", "罗德岛"],
            "深海猎人": ["阿戈尔", "罗德岛"],
            "炎": ["炎-龙门", "炎-岁", "龙门近卫局", "鲤氏侦探事务所", "企鹅物流"],
            "喀兰贸易": [],
            "阿戈尔": ["深海猎人"],
            "巴别塔": ["罗德岛", "罗德岛-精英干员"],
            "哥伦比亚": ["汐斯塔", "黑钢国际", "莱茵生命"],
            "红松骑士团": ["卡西米尔", "罗德岛"],
            "炎-岁": ["炎-龙门", "龙门近卫局", "炎", "鲤氏侦探事务所", "企鹅物流", "罗德岛"],
            "乌萨斯": ["乌萨斯学生自治团"],
            "东": [],
            "行动预备组A6": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P",
                "罗德岛",
                "行动组A4",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "行动组A4": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "炎-龙门": ["炎-岁", "龙门近卫局", "炎", "鲤氏侦探事务所", "企鹅物流"],
            "S.W.E.E.P": [
                "行动预备组A4",
                "行动预备组A1",
                "行动组A4",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "行动预备组A1": [
                "行动预备组A4",
                "S.W.E.E.P",
                "行动组A4",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "萨米": [],
            "彩虹小队": [],
            "使徒": ["罗德岛"],
            "玻利瓦尔": [],
            "行动预备组A4": [
                "行动预备组A1",
                "S.W.E.E.P",
                "行动组A4",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
        },
    }

tot_pool_info_file = record_path / "pool_info.json"


def get_prts_pool_info(pinfo: dict):
    """获取prts中的卡池信息"""
    prts_url = "https://prts.wiki/w/%E5%8D%A1%E6%B1%A0%E4%B8%80%E8%A7%88/%E9%99%90%E6%97%B6%E5%AF%BB%E8%AE%BF"
    prts_res = httpx.get(prts_url)
    root = etree.HTML(prts_res.text, etree.HTMLParser())
    # 限定
    group_type_divs: List[etree._Element] = root.xpath("//div[@class='wikitable mw-collapsible fullline logo']")
    group_types = [1, 0]  # is_exclusive
    for g_type, type_div in zip(group_types, group_type_divs):
        trs: List[etree._Element] = type_div.xpath("//tr")
        for tr in trs[1:]:
            if not (td := tr.getchildren()):
                continue
            td0: etree._Element = td[0]
            # 不知道为什么prts在卡池名称前面加上了 寻访模拟/
            a_elem: etree._Element = td0.find("a")
            pname = a_elem.get('title').strip().strip("寻访模拟/")
            pinfo[pname] = {"is_exclusive": bool(g_type)}
    return pinfo


def update_pool_info():
    """更新卡池信息"""
    with tot_pool_info_file.open("r", encoding="utf-8") as fj:
        try:
            pool_info = json.load(fj)
        except Exception:
            pool_info = {}
    # 从prts获取卡池信息
    get_prts_pool_info(pool_info)
    with tot_pool_info_file.open("w", encoding="utf-8") as fj:
        json.dump(pool_info, fj, ensure_ascii=False, indent=2)
    # get_tot_pool_info(tot_pool_info_file)

def initialize(cover: bool = False, retry: int = 5):
    base = httpx.get(
        "https://prts.wiki/w/PRTS:文件一览/干员精英0头像"
    )
    root = etree.HTML(base.text, etree.HTMLParser())
    imgs: List[etree._Element] = (
        root.xpath('//div[@class="mw-parser-output"]')[0].getchildren()[0].getchildren()
    )
    names = []
    for img in imgs:
        img_elem: etree._Element = img.getchildren()[0]
        alt: str = img_elem.get("alt", "None")
        if alt.startswith("头像") and "(集成战略)" not in alt and "预备干员" not in alt:
            names.append(alt[3:-4])
    tables = operators.setdefault("table", {})
    for name in names:
        if not cover and name in career:
            continue
        logger.debug(f"handle info of {name} ...")
        resp = httpx.get(f"https://prts.wiki/index.php?title={name}&action=edit")
        root = etree.HTML(resp.text, etree.HTMLParser())
        sub = root.xpath('//textarea[@id="wpTextbox1"]')[0].text
        char = char_pat.search(sub)[1]
        sub_char = sub_char_pat.search(sub)[1]
        rarity = rarity_pat.search(sub)[1]
        try:
            race = race_pat.search(sub)[1]
        except TypeError:
            race = "/"
        try:
            org1 = org_pat.search(sub)[1]
        except TypeError:
            org1 = ""
        try:
            org2 = org_pat1.search(sub)[1]
        except TypeError:
            org2 = ""
        try:
            org3 = org_pat2.search(sub)[1]
        except TypeError:
            org3 = ""
        org = org3 or org2 or org1
        org = org or "/"
        art = art_pat.search(sub)[1]
        tables[name] = {
            "rarity": int(rarity),
            "org": org,
            "career": f"{char}-{sub_char}",
            "race": race,
            "artist": art,
        }
        career[name] = char
        if (operate_path / f"{name}.png").exists() and not cover:
            continue
        logger.debug(f"handle image of {name} ...")
        _retry = retry
        while _retry:
            try:
                resp = httpx.get(
                    f"https://prts.wiki/w/文件:半身像_{name}_1.png", timeout=20.0
                )
                root = etree.HTML(resp.text)
                sub = root.xpath(f'//img[@alt="文件:半身像 {name} 1.png"]')[0]
                avatar: Image.Image = Image.open(
                    BytesIO(
                        (
                            httpx.get(f"https://prts.wiki{sub.xpath('@src').pop()}")
                        ).read()
                    )
                ).crop((20, 0, 124 + 20, 360))
                with (operate_path / f"{name}.png").open("wb+") as img:
                    avatar.save(
                        img,
                        format="PNG",
                        quality=100,
                        subsampling=2,
                        qtables="web_high",
                    )
                resp = httpx.get(
                    f"https://prts.wiki/w/文件:头像_{name}.png", timeout=20.0
                )
                root = etree.HTML(resp.text)
                sub = root.xpath(f'//img[@alt="文件:头像 {name}.png"]')[0]
                with (operate_path / f"profile_{name}.png").open("wb+") as img:
                    img.write(httpx.get(f"https://prts.wiki{sub.xpath('@src').pop()}").read())
                logger.success(f"{name}({career[name]}) saved")
                break
            except Exception as e:
                _retry -= 1
                logger.warning(f"Fetch {name} failed. Caused by {e}")
                logger.debug("Retrying...")
        if not _retry:
            logger.error(f"Fetch {name} failed.")
            continue
    with (base_path / "careers.json").open("w+", encoding="utf-8") as _f:
        json.dump(career, _f, ensure_ascii=False)
    with (wordle_path / "relations.json").open("w+", encoding="utf-8") as _f:
        json.dump(operators, _f, ensure_ascii=False)
    logger.success("operator resources initialized")
    update_pool_info()
    logger.success("record pool info initialized")

    from . import __version__

    with (base_path / "ops_initialized").open("w+", encoding="utf-8") as _f:
        _f.write(__version__)
