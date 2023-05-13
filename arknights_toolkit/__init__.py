from pathlib import Path
from .gacha import ArknightsGacha, GachaUser
from .random_operator import RandomOperator
from .recruit import recruitment

__version__ = "0.5.5"

def need_init():
    file = Path(__file__).parent / "resource" / "ops_initialized"
    return not file.exists() or file.open('r', encoding='utf-8').read() != __version__
