from __future__ import annotations

from arclet.alconna import Arparma, Alconna, CommandMeta, Option, store_true
from clilte import BasePlugin, PluginMetadata
import asyncio
from arknights_toolkit.update.main import fetch
from pathlib import Path

class Init(BasePlugin):
    def init(self) -> Alconna | str:
        alc = Alconna(
            "init",
            Option("--cover", default=False, action=store_true, help_text="是否覆盖已有的资源文件"),
            meta=CommandMeta("初始化干员数据与图片资源")
        )
        alc.help_text = "初始化干员数据与图片资源"
        return alc

    def meta(self) -> PluginMetadata:
        return PluginMetadata(
            "init", "0.1.0", "init", ["init"], ["RF-Tar-Railt"], 10
        )

    def dispatch(self, result: Arparma) -> bool | None:
        if result.find("init"):
            asyncio.run(fetch(result.query("cover.value")))
            from arknights_toolkit import __version__
            base_path = Path(__file__).parent.parent.parent / "resource"
            with (base_path / "ops_initialized").open("w+", encoding="utf-8") as _f:
                _f.write(__version__)
            return False
        return True