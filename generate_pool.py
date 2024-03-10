import httpx
from lxml import etree
from typing import List
import json

def get_prts_pool_info(pinfo: dict):
    """获取prts中的卡池信息"""
    prts_url = "https://prts.wiki/w/%E5%8D%A1%E6%B1%A0%E4%B8%80%E8%A7%88/%E9%99%90%E6%97%B6%E5%AF%BB%E8%AE%BF"
    prts_res = httpx.get(prts_url)
    with open("test.html", "w+", encoding='utf-8') as f:
        f.write(prts_res.text)
    root = etree.HTML(prts_res.text, etree.HTMLParser())
    # 限定
    group_type_tables: List[etree._Element] = root.xpath("//table[@class='wikitable mw-collapsible fullline logo']")
    group_types = [1, 0]  # is_exclusive
    for g_type, type_div in zip(group_types, group_type_tables):
        trs: List[etree._Element] = type_div.getchildren()[0].getchildren()
        for tr in trs[1:]:
            if not (td := tr.getchildren()):
                continue
            td0: etree._Element = td[0]
            if (a_elem := td0.find("a", None)) is not None:
                pname = a_elem.get('title').strip().strip("寻访模拟/")
                pinfo[pname] = {"is_exclusive": bool(g_type)}
    return pinfo

with open("test.json", "w+", encoding='utf-8') as f:
    json.dump(get_prts_pool_info({}), f, ensure_ascii=False, indent=2)
