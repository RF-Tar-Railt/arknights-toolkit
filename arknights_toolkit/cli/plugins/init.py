from __future__ import annotations

import asyncio
from pathlib import Path

from arclet.alconna import (
    Alconna,
    Args,
    Arparma,
    CommandMeta,
    Option,
    append,
    store_true,
)
from clilte import BasePlugin, PluginMetadata
from nepattern import SwitchPattern


class Init(BasePlugin):
    def init(self) -> Alconna | str:
        alc = Alconna(
            "init",
            Option(
                "--select|-S",
                Args["flag", SwitchPattern({"IMG": 2, "REC": 1, "NON": 0})],
                action=append,
                help_text="选择特定的资源类型下载",
                compact=True,
            ),
            Option(
                "--cover|-C", default=False, action=store_true, help_text="是否覆盖已有的资源文件"
            ),
            meta=CommandMeta("初始化干员数据与图片资源"),
        )
        alc.help_text = "初始化干员数据与图片资源"
        return alc

    def meta(self) -> PluginMetadata:
        return PluginMetadata("init", "0.1.0", "init", ["init"], ["RF-Tar-Railt"], 10)

    def dispatch(self, result: Arparma) -> bool | None:
        if result.find("init"):
            from arknights_toolkit.update.main import fetch

            select = sum(set(result.query("init.select.flag", [1, 2])))
            asyncio.run(fetch(select, result.query[bool]("init.cover.value", False), proxy=result.query[str]("proxy.url")))
            from arknights_toolkit import __version__

            base_path = Path(__file__).parent.parent.parent / "resource"
            with (base_path / "ops_initialized").open("w+", encoding="utf-8") as _f:
                _f.write(__version__)
            return False
        return True

    def supply_options(self):
        return [
            Option(
                "--proxy|-P", Args["url", str], help_text="设置代理地址", compact=True
            )
        ]
