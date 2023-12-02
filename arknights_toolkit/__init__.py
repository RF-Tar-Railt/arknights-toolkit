from pathlib import Path

from packaging import version

from .gacha import ArknightsGacha, GachaUser
from .random_operator import RandomOperator
from .recruit import recruitment

__version__ = "0.6.3"


def need_init():
    file = Path(__file__).parent / "resource" / "ops_initialized"
    if not file.exists():
        return True
    with file.open("r", encoding="utf-8") as f:
        target = version.parse(f.read())
    source = version.parse(__version__)
    return target.major < source.major or target.minor < source.minor
