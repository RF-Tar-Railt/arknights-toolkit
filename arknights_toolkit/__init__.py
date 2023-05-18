from pathlib import Path
from packaging import version
from .gacha import ArknightsGacha, GachaUser
from .random_operator import RandomOperator
from .recruit import recruitment

__version__ = "0.5.8"


def need_init():
    file = Path(__file__).parent / "resource" / "ops_initialized"
    with file.open("r", encoding="utf-8") as f:
        target = version.parse(f.read())
    source = version.parse(__version__)
    return not file.exists() or (
        target.major < source.major or target.minor < source.minor
    )
