from __future__ import annotations

from logging import log
from pathlib import Path

from loguru import logger
from nepattern import SwitchPattern
from clilte import BasePlugin, PluginMetadata
from arclet.alconna import Args, Option, Alconna, Arparma, CommandMeta, append


class Clear(BasePlugin):
    def init(self) -> Alconna | str:
        alc = Alconna(
            "clear",
            Option(
                "--select|-S",
                Args["flag", SwitchPattern({"IMG": 2, "REC": 1, "NON": 0})],
                action=append,
                help_text="选择特定的资源类型清除",
                compact=True,
            ),
            meta=CommandMeta("清除干员数据与图片资源"),
        )
        alc.help_text = "清除干员数据与图片资源"
        return alc

    def meta(self) -> PluginMetadata:
        return PluginMetadata("clear", "0.1.0", "clear", ["clear"], ["RF-Tar-Railt"], 10)

    def dispatch(self, result: Arparma) -> bool | None:
        if result.find("clear"):
            select = sum(set(result.query("init.select.flag", [1, 2])))
            base_path = Path(__file__).parent.parent.parent / "resource"
            if (base_path / "info.json").exists():
                (base_path / "info.json").unlink()
                logger.info("info.json has been removed")
            for img in (base_path / "operators").iterdir():
                if select & 0b01 and img.stem.startswith("profile"):
                    img.unlink(missing_ok=True)
                    logger.info(f"{img.name} has been removed")
                elif select & 0b10 and not img.stem.startswith("profile"):
                    img.unlink(missing_ok=True)
                    logger.info(f"{img.name} has been removed")
            (base_path / "ops_initialized").unlink(missing_ok=True)
            logger.success("resource has been cleared")
            return False
        return True

    @classmethod
    def supply_options(cls) -> list[Option] | None:
        return
