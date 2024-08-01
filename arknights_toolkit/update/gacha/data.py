import random
import signal
from pathlib import Path
from typing import List, Optional

import ujson
from loguru import logger
from httpx import AsyncClient
from httpx._types import ProxiesTypes

from .model import GachaTableIndex, GachaTableDetails

INDEX_URL = "https://mirror.ghproxy.com/github.com/Kengxxiao/ArknightsGameData/blob/master/zh_CN/gamedata/excel/gacha_table.json"
DETAILS_URL = "https://weedy.baka.icu/gacha_table.json"

fetched_ops_path = Path(__file__).parent.parent.parent / "resource" / "info.json"


if fetched_ops_path.exists():
    with fetched_ops_path.open("r", encoding="utf-8") as f:
        fetched_ops = ujson.load(f)

    tables = fetched_ops["table"]

    try:
        mapping = {info["id"]: name for name, info in tables.items()}
    except KeyError:
        logger.critical("operator resources has been outdated")
        logger.error("please execute `arkkit init --cover` in your command line")
        signal.raise_signal(signal.SIGINT)
else:
    mapping = {}

rarity_table_file = Path(__file__).parent.parent.parent / "resource" / "gacha" / "rarity_table.json"

SPECIAL_NAMES = {"前路回响", "适合多种场合的强力干员"}


async def fetch(proxy: Optional[ProxiesTypes] = None):
    async with AsyncClient(verify=False, proxies=proxy, follow_redirects=True) as client:
        resp = await client.get(INDEX_URL)
        index_data: GachaTableIndex = ujson.loads(resp.text)
        resp1 = await client.get(DETAILS_URL)
        details_data: List[GachaTableDetails] = ujson.loads(resp1.text)["gachaPoolClient"]
    pools = index_data["gachaPoolClient"]
    target_id = sorted(
        (
            pool
            for pool in pools
            if pool["gachaPoolName"] not in SPECIAL_NAMES and not pool["gachaPoolName"].startswith("跨年欢庆")
        ),
        key=lambda x: x["openTime"],
        reverse=True,
    )[0]["gachaPoolId"]
    table = {}
    detail = next(
        (detail for detail in details_data if detail["gachaPoolId"] == target_id),
        None,
    )
    if detail is None:
        detail = random.choice([d for d in details_data if d["gachaPoolId"].startswith("NORM")])
    # print(detail["gachaPoolDetail"]["detailInfo"])
    current_limit = detail["gachaPoolDetail"]["detailInfo"]["limitedChar"]
    weight_limit = detail["gachaPoolDetail"]["detailInfo"]["weightUpCharInfoList"]
    for chars in detail["gachaPoolDetail"]["detailInfo"]["availCharInfo"]["perAvailList"]:
        for char in chars["charIdList"]:
            if current_limit and char in current_limit:
                continue
            if weight_limit and char in [char["charId"] for char in weight_limit]:
                continue
            try:
                table[mapping[char]] = chars["rarityRank"] + 1
            except KeyError:
                logger.critical(f"can't find {char} in mapping")
                logger.error("please execute `arkkit init` in your command line")
    with rarity_table_file.open("w+", encoding="utf-8") as f:
        ujson.dump(table, f, ensure_ascii=False)
    return table
