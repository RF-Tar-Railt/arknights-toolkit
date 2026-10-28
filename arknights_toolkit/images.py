from collections.abc import Iterator, MutableMapping
from functools import lru_cache
from typing import Dict
from pathlib import Path

from loguru import logger
from PIL import Image, ImageEnhance, ImageFont

from . import need_init

resource_path = Path(__file__).parent / "resource"
gacha_path = resource_path / "gacha"
wordle_path = resource_path / "wordle"
record_path = resource_path / "record"


@lru_cache(maxsize=8)
def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        return ImageFont.load_default()  # type: ignore


def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    return _load_font(str(Path(font_path).resolve()), size)


six_bgi: Image.Image = Image.open(gacha_path / "back_six.png")
five_bgi: Image.Image = Image.open(gacha_path / "back_five.png")
four_bgi: Image.Image = Image.open(gacha_path / "back_four.png")
low_bgi: Image.Image = Image.new("RGBA", (124, 360), (49, 49, 49))
six_tail: Image.Image = Image.open(gacha_path / "six_02.png")

six_line: Image.Image = Image.open(gacha_path / "six_01.png")
five_line: Image.Image = Image.open(gacha_path / "five.png")
four_line: Image.Image = Image.open(gacha_path / "four.png")

star_circle: Image.Image = Image.open(gacha_path / "star_02.png")
enhance_five_line: Image.Image = Image.new("RGBA", (124, 720), (0x60, 0x60, 0x60, 0x50))
enhance_four_line: Image.Image = Image.new("RGBA", (124, 720), (132, 108, 210, 0x10))
brighter = ImageEnhance.Brightness(six_line)
six_line: Image.Image = brighter.enhance(1.5)
brighter = ImageEnhance.Brightness(four_line)
four_line: Image.Image = brighter.enhance(0.9)
six_line_up: Image.Image = six_line.crop((0, 0, six_line.size[0], 256))
six_line_down: Image.Image = six_line.crop((0, 256, six_line.size[0], 512))
five_line_up: Image.Image = five_line.crop((0, 0, five_line.size[0], 256))
five_line_down: Image.Image = five_line.crop((0, 256, five_line.size[0], 512))
four_line_up: Image.Image = four_line.crop((0, 0, four_line.size[0], 256))
four_line_down: Image.Image = four_line.crop((0, 256, four_line.size[0], 512))
logger.debug("basic image loaded.")
characters: Dict[str, Image.Image] = {
    "先锋": Image.open(gacha_path / "图标_职业_先锋_大图_白.png"),
    "近卫": Image.open(gacha_path / "图标_职业_近卫_大图_白.png"),
    "医疗": Image.open(gacha_path / "图标_职业_医疗_大图_白.png"),
    "术师": Image.open(gacha_path / "图标_职业_术师_大图_白.png"),
    "狙击": Image.open(gacha_path / "图标_职业_狙击_大图_白.png"),
    "特种": Image.open(gacha_path / "图标_职业_特种_大图_白.png"),
    "辅助": Image.open(gacha_path / "图标_职业_辅助_大图_白.png"),
    "重装": Image.open(gacha_path / "图标_职业_重装_大图_白.png"),
}
logger.debug("careers image loaded.")
stars: Dict[int, Image.Image] = {
    5: Image.open(gacha_path / "稀有度_白_5.png"),
    4: Image.open(gacha_path / "稀有度_白_4.png"),
    3: Image.open(gacha_path / "稀有度_白_3.png"),
    2: Image.open(gacha_path / "稀有度_白_2.png"),
}
logger.debug("stars image loaded.")

sign: Dict[str, Image.Image] = {
    "correct": Image.open(wordle_path / "correct.png"),
    "down": Image.open(wordle_path / "down.png"),
    "up": Image.open(wordle_path / "up.png"),
    "wrong": Image.open(wordle_path / "wrong.png"),
    "relate": Image.open(wordle_path / "relate.png"),
}
logger.debug("wordle sign image loaded.")

# 顶部路径
title_image: Image.Image = Image.open(record_path / "titleimage.png")
# 底部图像
bottom_image: Image.Image = Image.open(record_path / "bottom.png")
# 六星渐变图像
rainbow_image: Image.Image = Image.open(record_path / "rainbow.png")
logger.debug("record base image loaded.")

if need_init():
    import signal

    logger.critical("operator resources has not initialized yet")
    logger.error("please execute `arkkit init` in your command line")
    signal.raise_signal(signal.SIGINT)


@lru_cache(maxsize=16)
def _load_image(path: str) -> Image.Image:
    with Image.open(path) as image:
        return image.copy()


class LazyImageMap(MutableMapping[str, Image.Image]):
    """Keep image paths indexed and load each image only when it is requested."""

    def __init__(self, directory: Path):
        self.directory = directory
        self._paths: Dict[str, Path] = {}
        self._images: Dict[str, Image.Image] = {}
        self.update_paths()

    def update_paths(self) -> None:
        self._paths.update(
            {path.stem: path for path in self.directory.iterdir() if path.is_file()}
        )

    def __getitem__(self, key: str) -> Image.Image:
        if key in self._images:
            return self._images[key]
        if key not in self._paths:
            raise KeyError(key)
        return _load_image(str(self._paths[key]))

    def __setitem__(self, key: str, value: Image.Image) -> None:
        self._images[key] = value

    def __delitem__(self, key: str) -> None:
        del self._images[key]
        self._paths.pop(key, None)

    def __iter__(self) -> Iterator[str]:
        return iter(dict.fromkeys((*self._paths, *self._images)))

    def __len__(self) -> int:
        return len(set(self._paths) | set(self._images))

    def __contains__(self, key: object) -> bool:
        return key in self._paths or key in self._images


operators = LazyImageMap(resource_path / "operators")
logger.debug("operators image paths indexed; images will load on demand.")


def update_operators():
    operators.update_paths()
