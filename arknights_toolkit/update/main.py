import re
from io import BytesIO
from enum import IntEnum
from pathlib import Path
from typing_extensions import TypedDict
from typing import Dict, List, Union, Optional

import httpx
import ujson as json
from PIL import Image
import lxml.etree as etree
from loguru import logger
from httpx._types import ProxiesTypes

__all__ = ["fetch", "fetch_info", "fetch_image", "fetch_profile_image"]

id_pat = re.compile(r"\|干员id=char_([^|]+?)\n\|")
rarity_pat = re.compile(r"\|稀有度=(\d+?)\n\|")
char_pat = re.compile(r"\|职业=([^|]+?)\n\|")
sub_char_pat = re.compile(r"\|分支=([^|]+?)\n\|")
race_pat = re.compile(r"\|种族=([^|]+?)\n\|")
org_pat = re.compile(r"\|所属国家=([^|]+?)\n\|")
org_pat1 = re.compile(r"\|所属组织=([^|]+?)\n\|")
org_pat2 = re.compile(r"\|所属团队=([^|]+?)\n\|")
art_pat = re.compile(r"\|画师=([^|]+?)\n\|")

base_path = Path(__file__).parent.parent / "resource"
operate_path = base_path / "operators"
operate_path.mkdir(parents=True, exist_ok=True)
info_path = base_path / "info.json"

if not info_path.exists():
    infos = {
        "detail": "org_related 写的是目标->猜测的关系，目标为key",
        "org_related": {
            "汐斯塔": ["哥伦比亚", "黑钢国际", "莱茵生命"],
            "叙拉古": ["贾维团伙"],
            "乌萨斯学生自治团": ["乌萨斯"],
            "格拉斯哥帮": ["维多利亚"],
            "罗德岛": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P.",
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
            "深池": ["维多利亚"],
            "维多利亚": ["格拉斯哥帮", "深池"],
            "鲤氏侦探事务所": ["炎-龙门", "炎-岁", "炎", "龙门近卫局", "企鹅物流"],
            "罗德岛-精英干员": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P.",
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
            "企鹅物流": ["炎-龙门", "炎-岁", "炎", "鲤氏侦探事务所", "龙门近卫局"],
            "深海猎人": ["阿戈尔"],
            "炎": ["炎-龙门", "炎-岁", "龙门近卫局", "鲤氏侦探事务所", "企鹅物流"],
            "喀兰贸易": [],
            "谢拉格": ["喀兰贸易"],
            "阿戈尔": ["深海猎人"],
            "巴别塔": ["罗德岛", "罗德岛-精英干员"],
            "哥伦比亚": ["汐斯塔", "黑钢国际", "莱茵生命"],
            "红松骑士团": ["卡西米尔"],
            "炎-岁": ["炎-龙门", "龙门近卫局", "炎", "鲤氏侦探事务所", "企鹅物流", "罗德岛"],
            "乌萨斯": ["乌萨斯学生自治团"],
            "东": [],
            "行动预备组A6": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P.",
                "罗德岛",
                "行动组A4",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "行动组A4": [
                "行动预备组A4",
                "行动预备组A1",
                "S.W.E.E.P.",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "炎-龙门": ["炎-岁", "龙门近卫局", "炎", "鲤氏侦探事务所", "企鹅物流"],
            "S.W.E.E.P.": [
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
                "S.W.E.E.P.",
                "行动组A4",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
            "萨米": [],
            "彩虹小队": [],
            "莱欧斯小队": [],
            "使徒": ["罗德岛"],
            "玻利瓦尔": [],
            "行动预备组A4": [
                "行动预备组A1",
                "S.W.E.E.P.",
                "行动组A4",
                "罗德岛",
                "行动预备组A6",
                "巴别塔",
                "罗德岛-精英干员",
            ],
        },
        "table": {},
    }
    with info_path.open("w+", encoding="utf-8") as f:
        json.dump(infos, f, ensure_ascii=False, indent=2)


async def fetch_image(name: str, charid: str, client: httpx.AsyncClient, retry: int):
    level = 2 if name == "阿米娅(近卫)" else 1
    _retry = retry
    while _retry:
        logger.debug(f"handle image of {name} ...")
        try:
            resp = await client.get(
                f"https://torappu.prts.wiki/assets/char_portrait/{charid}_{level}.png", timeout=20.0
            )
            if resp.status_code != 200:
                raise RuntimeError(f"status code: {resp.status_code}")
            # root = etree.HTML(resp.text)
            # sub = root.xpath(f'//img[@alt="文件:半身像 {name} {level}.png"]')[0]
            avatar: Image.Image = Image.open(BytesIO(resp.content)).crop((20, 0, 124 + 20, 360))
            with (operate_path / f"{name}.png").open("wb") as f:
                avatar.save(f, format="PNG", quality=100, subsampling=2, qtables="web_high")
            logger.success(f"{name} image saved")
            return avatar
        except Exception as e:
            logger.error(f"failed to get image of {name}: {e}")
            _retry -= 1
    if not _retry:
        logger.error(f"failed to get image of {name} after {retry} retries")


async def fetch_profile_image(name: str, charid: str, client: httpx.AsyncClient, retry: int):
    _retry = retry
    while _retry:
        logger.debug(f"handle profile image of {name} ...")
        try:
            resp = await client.get(
                (
                    f"https://torappu.prts.wiki/assets/char_avatar/{charid}_2.png"
                    if name == "阿米娅(近卫)"
                    else f"https://torappu.prts.wiki/assets/char_avatar/{charid}.png"
                ),
                timeout=20.0,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"status code: {resp.status_code}")
            with (operate_path / f"profile_{name}.png").open("wb+") as img:
                img.write(resp.content)
            logger.success(f"{name} profile image saved")
            break
        except Exception as e:
            logger.error(f"failed to get profile image of {name}: {e}")
            _retry -= 1
    if not _retry:
        logger.error(f"failed to get profile image of {name} after {retry} retries")


async def fetch_info(name: str, client: httpx.AsyncClient):
    logger.debug(f"handle info of {name} ...")
    resp = await client.get(f"https://prts.wiki/index.php?title={name}&action=edit", timeout=20.0)
    root = etree.HTML(resp.text, etree.HTMLParser())
    sub = root.xpath('//textarea[@id="wpTextbox1"]')[0].text
    op_id = id_pat.search(sub)[1]  # type: ignore
    char = char_pat.search(sub)[1]  # type: ignore
    sub_char = sub_char_pat.search(sub)[1]  # type: ignore
    rarity = rarity_pat.search(sub)[1]  # type: ignore
    try:
        race = race_pat.search(sub)[1]  # type: ignore
    except TypeError:
        race = "/"
    try:
        org1 = org_pat.search(sub)[1]  # type: ignore
    except TypeError:
        org1 = ""
    try:
        org2 = org_pat1.search(sub)[1]  # type: ignore
    except TypeError:
        org2 = ""
    try:
        org3 = org_pat2.search(sub)[1]  # type: ignore
    except TypeError:
        org3 = ""
    org = org3 or org2 or org1
    org = org or "/"
    art = art_pat.search(sub)[1]  # type: ignore
    logger.success(f"{name}({char}) info fetched")
    return {
        "id": f"char_{op_id}",
        "rarity": int(rarity),
        "org": org,
        "career": f"{char}-{sub_char}",
        "race": race,
        "artist": art,
    }


class FetchFlag(IntEnum):
    IMG = 2
    REC = 1
    NON = 0


"""
chara.charId=charid,
chara._pageName=干员,
chara.charIndex=干员序号,
chara.rarity=稀有度,
chara.nation=国家,
chara.org=组织,
chara.team=团队,
chara.profession=职业,
chara.subProfession=子职业,
chara_extra_info.race=种族,
chara.painter=画师,
"""


class Chara(TypedDict):
    charid: str
    干员: str
    干员序号: int
    稀有度: int
    国家: str
    组织: str
    团队: str
    职业: str
    子职业: str
    种族: str
    画师: str


def _transform(data: Chara):
    org = data["团队"] or data["组织"] or data["国家"]
    return {
        "id": data["charid"],
        "rarity": int(data["稀有度"]),
        "org": org or "/",
        "career": f"{data['职业']}-{data['子职业']}",
        "race": data["种族"] or "/",
        "artist": data["画师"],
    }


cargo_query = "https://prts.wiki/api.php?action=cargoquery&format=json&limit=500&tables=chara%2Cchara_data%2Cchara_extra_info%2Cchar_obtain&fields=chara.charId%3Dcharid%2C%20chara._pageName%3D%E5%B9%B2%E5%91%98%2C%20chara.charIndex%3D%E5%B9%B2%E5%91%98%E5%BA%8F%E5%8F%B7%2C%20chara.rarity%3D%E7%A8%80%E6%9C%89%E5%BA%A6%2C%20chara.nation%3D%E5%9B%BD%E5%AE%B6%2C%20chara.org%3D%E7%BB%84%E7%BB%87%2C%20chara.team%3D%E5%9B%A2%E9%98%9F%2C%20chara.profession%3D%E8%81%8C%E4%B8%9A%2C%20chara.subProfession%3D%E5%AD%90%E8%81%8C%E4%B8%9A%2C%20chara_extra_info.race%3D%E7%A7%8D%E6%97%8F%2C%20chara.painter%3D%E7%94%BB%E5%B8%88%2C&where=chara.charIndex%3E0&join_on=chara._pageName%3Dchara_data._pageName%2Cchara._pageName%3Dchara_extra_info._pageName%2Cchara._pageName%3Dchar_obtain._pageName&utf8=1"


async def fetch(
    select: Union[int, FetchFlag] = 0b11,
    cover: bool = False,
    retry: int = 5,
    proxy: Optional[ProxiesTypes] = None,
):
    if select < 0 or select > 3:
        raise ValueError(select)
    with info_path.open("r+", encoding="utf-8") as _f:
        _infos = json.load(_f)
    tables = _infos.setdefault("table", {})
    async with httpx.AsyncClient(verify=False, proxies=proxy) as client:
        queries: List[Dict[str, Chara]] = (await client.get(cargo_query)).json()["cargoquery"]
        tables.update({raw["title"]["干员"]: _transform(raw["title"]) for raw in queries})
        for name in tables:
            try:
                # if name not in tables or cover:
                #     tables[name] = await fetch_info(name, client)
                if select & 0b10 and (not (operate_path / f"{name}.png").exists() or cover):
                    await fetch_image(name, tables[name]["id"], client, retry)
                if select & 0b01 and (not (operate_path / f"profile_{name}.png").exists() or cover):
                    await fetch_profile_image(name, tables[name]["id"], client, retry)
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.error(f"拉取 {name} 失败: {type(e)}({e})\n请检查网络或代理设置")
                continue

    with info_path.open("w+", encoding="utf-8") as _f:
        json.dump(_infos, _f, ensure_ascii=False, indent=2)
    logger.success("operator resources updated")
    return True
