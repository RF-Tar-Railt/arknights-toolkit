from __future__ import annotations

from arclet.alconna import Arparma, Alconna, CommandMeta, Option, Args
from clilte import BasePlugin, PluginMetadata
import asyncio
from pathlib import Path
from arknights_toolkit.update.gacha import generate as generate_gacha
from arknights_toolkit.update.record import generate as generate_record

class Update(BasePlugin):
    def init(self) -> Alconna | str:
        alc = Alconna(
            "update",
            Option("gacha", Args["path", str], help_text="更新抽卡卡池数据"),
            Option("record", Args["path?", str], help_text="更新抽卡记录卡池数据"),
            meta=CommandMeta("更新部分资源")
        )
        alc.help_text = "更新部分资源"
        return alc

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            "update", "0.1.0", "update", ["update"], ["RF-Tar-Railt"], 20
        )

    def dispatch(self, result: Arparma) -> bool | None:
        if result.find("update"):
            if result.find("update.gacha"):
                asyncio.run(
                    generate_gacha(Path(result.query("update.gacha.path")).absolute())
                )
            if result.find("update.record"):
                path = Path(result.query(
                    "update.record.path",
                    Path(__file__).parent.parent.parent / "resource" / "record" / "pool_info.json"
                )).absolute()
                asyncio.run(generate_record(path))
            return False
        return True