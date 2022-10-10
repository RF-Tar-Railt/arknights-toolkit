import json
import random
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Literal, Optional, TypedDict, overload
import re
import httpx
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

__all__ = ["Operator", "Guess", "GuessUnit", "OperatorWordle", "update"]

rarity_pat = re.compile(r"\|稀有度=(\d+?)\n\|.+?")
char_pat = re.compile(r"\|职业=([^|]+?)\n\|.+?")
sub_char_pat = re.compile(r"\|分支=([^|]+?)\n\|.+?")
race_pat = re.compile(r"\|种族=([^|]+?)\n\|.+?")
org_pat = re.compile(r"\|所属国家=([^|]+?)\n\|.+?")
org_pat1 = re.compile(r"\|所属组织=([^|]+?)\n\|.+?")
org_pat2 = re.compile(r"\|所属团队=([^|]+?)\n\|.+?")
art_pat = re.compile(r"\|画师=([^|]+?)\n\|.+?")
base = Path(__file__).parent / "resource" / "wordle"
sign = {
    "correct": Image.open(base / "correct.png"),
    "down": Image.open(base / "down.png"),
    "up": Image.open(base / "up.png"),
    "wrong": Image.open(base / "wrong.png"),
    "relate": Image.open(base / "relate.png"),
}
simple_sign = {"correct": "🟩", "down": "🟦", "up": "🟦", "wrong": "🟥", "relate": "🟨"}

state = Literal["correct", "down", "up", "wrong", "relate"]


class Operator(TypedDict):
    rarity: int
    org: str
    career: str
    race: str
    artist: str
    relate: Optional[List[str]]


class GuessUnit(TypedDict):
    rarity: state
    org: state
    career: state
    race: state
    artist: state
    name: str


@dataclass
class Guess:
    state: Literal["success", "guessing", "failed"]
    lines: List[GuessUnit]
    select: str


with (base / "relations.json").open("r", encoding="utf-8") as f:
    _data = json.load(f)
    relations: Dict[str, List[str]] = _data["org_related"]
    tables: Dict[str, Operator] = _data["table"]


def update(*names: str):
    for name in names:
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
        org = org3 if org3 else org2 if org2 else org1
        org = org or "/"
        art = art_pat.search(sub)[1]
        tables[name] = {
            "rarity": int(rarity),
            "org": org,
            "career": f"{char}-{sub_char}",
            "race": race,
            "artist": art,
        }
    with (base / "relations.json").open("w", encoding="utf-8") as _f:
        json.dump(_data, _f, ensure_ascii=False)


class OperatorWordle:
    def __init__(self, path: str, max_guess: int = 8):
        self.base_dir = Path(path)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.base_dir.is_dir():
            raise NotADirectoryError(path)
        self.max_guess = max_guess

    def restart(self, uid: str):
        data_path = self.base_dir / f"{uid}.json"
        data_path.unlink(missing_ok=True)

    def select(self, uid: str):
        selected_name = random.choice(list(tables.keys()))
        selected = tables[selected_name]
        with (self.base_dir / f"{uid}.json").open("w+", encoding="utf-8") as _f:
            json.dump(
                {
                    "select": selected,
                    "select_name": selected_name,
                    "select_time": 0,
                    "units": [],
                },
                _f,
                ensure_ascii=False,
                indent=2,
            )
        return selected_name, selected

    def guess(self, name: str, uid: str) -> Guess:
        data_path = self.base_dir / f"{uid}.json"
        if not data_path.exists():
            old_res = []
            select_time = 0
            selected_name, selected = self.select(uid)
        else:
            with data_path.open("r", encoding="utf-8") as _f:
                sdata = json.load(_f)
                selected_name = sdata["select_name"]
                selected = sdata["select"]
                old_res = sdata["units"]
                select_time = sdata["select_time"]
        if name not in tables:
            raise ValueError("干员不存在")
        res = {
            "rarity": "correct",
            "org": "correct",
            "career": "correct",
            "race": "correct",
            "artist": "correct",
            "name": name,
        }
        if name == selected_name:
            data_path.unlink()
            return Guess("success", old_res + [res], selected_name)
        select_time += 1
        guess_op = tables[name]
        if guess_op["rarity"] < selected["rarity"]:
            res["rarity"] = "up"
        elif guess_op["rarity"] > selected["rarity"]:
            res["rarity"] = "down"

        if guess_op["org"] != selected["org"]:
            if selected_name in guess_op.get("relate", []) or name in selected.get(
                "relate", []
            ):
                res["org"] = "relate"
            elif guess_op["org"] in relations[selected["org"]]:
                res["org"] = "relate"
            else:
                res["org"] = "wrong"

        if guess_op["career"] != selected["career"]:
            g_cs = guess_op["career"].split("-")
            res["career"] = (
                "relate" if selected["career"].startswith(g_cs[0]) else "wrong"
            )

        if guess_op["race"] != selected["race"]:
            res["race"] = "wrong"

        if guess_op["artist"] != selected["artist"]:
            res["artist"] = "wrong"
        if select_time >= self.max_guess:
            data_path.unlink()
            return Guess("failed", old_res + [res], selected_name)
        with data_path.open("w+", encoding="utf-8") as _f:
            json.dump(
                {
                    "select": selected,
                    "select_name": selected_name,
                    "select_time": select_time,
                    "units": old_res + [res],
                },
                _f,
                ensure_ascii=False,
                indent=2,
            )
        return Guess("guessing", old_res + [res], selected_name)

    @overload
    def draw(self, res: Guess, simple=True) -> str:
        ...

    @overload
    def draw(self, res: Guess, simple=False) -> bytes:
        ...

    def draw(self, res: Guess, simple: bool = False):
        if simple:
            ans = f"干员猜猜乐 {len(res.lines)}/{self.max_guess}\n"
            for unit in res.lines:
                ans += simple_sign[unit["rarity"]]
                ans += simple_sign[unit["org"]]
                ans += simple_sign[unit["career"]]
                ans += simple_sign[unit["race"]]
                ans += simple_sign[unit["artist"]]
                ans += unit["name"]
                ans += "\n"
            return ans

        back_img = Image.new("RGB", (600, 80 * (len(res.lines) + 2)), (0, 0, 0))
        draw = ImageDraw.Draw(back_img)
        font_base = ImageFont.truetype("simhei.ttf", 20)
        draw.text((20, 45), "稀有度", fill="white", font=font_base)
        draw.text((130, 45), "阵营", fill="white", font=font_base)
        draw.text((230, 45), "职业", fill="white", font=font_base)
        draw.text((330, 45), "种族", fill="white", font=font_base)
        draw.text((430, 45), "画师", fill="white", font=font_base)
        draw.text((530, 45), "名称", fill="white", font=font_base)
        for index, unit in enumerate(res.lines):
            slot = sign[unit["rarity"]].copy()
            size = slot.size
            slot.thumbnail(size)
            back_img.paste(slot, (10, 80 * (index + 1)), slot)
            slot = sign[unit["org"]].copy()
            size = slot.size
            slot.thumbnail(size)
            back_img.paste(slot, (110, 80 * (index + 1)), slot)
            slot = sign[unit["career"]].copy()
            size = slot.size
            slot.thumbnail(size)
            back_img.paste(slot, (210, 80 * (index + 1)), slot)
            slot = sign[unit["race"]].copy()
            size = slot.size
            slot.thumbnail(size)
            back_img.paste(slot, (310, 80 * (index + 1)), slot)
            slot = sign[unit["artist"]].copy()
            size = slot.size
            slot.thumbnail(size)
            back_img.paste(slot, (410, 80 * (index + 1)), slot)
            length = len(unit["name"])
            length = max(length, 4)
            font_size = int(4 * font_base.size / length)
            font = font_base.font_variant(size=font_size)
            width_offset = (100 - font.getbbox(unit["name"])[2]) // 2
            height_offset = (80 - font.getbbox(unit["name"])[3]) // 2
            draw.text(
                (500 + width_offset, 80 * (index + 1) + height_offset),
                unit["name"],
                fill="pink",
                font=font,
            )
        if res.state == "failed":
            text = f"失败了！这只神秘的干员是{res.select}！"
        elif res.state == "success":
            text = f"成功了！这只神秘的干员是{res.select}！"
        else:
            text = f"你有{len(res.lines)}/{self.max_guess}次机会猜测这只神秘干员，试试看！"
        width = font_base.getbbox(text)
        draw.text(
            ((600 - width[2]) // 2, 80 * (len(res.lines) + 1) + 30),
            text,
            fill="white",
            font=font_base,
        )
        imageio = BytesIO()
        back_img.save(
            imageio,
            format="PNG",
            quality=90,
            subsampling=2,
            qtables="web_high",
        )
        return imageio.getvalue()


if __name__ == "__main__":
    guess = OperatorWordle("./")
    while True:
        name = input(">>> ")
        my_res = guess.guess(name, "aaa")
        print(guess.draw(my_res, simple=True))
        if my_res.state != "guessing":
            break
