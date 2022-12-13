__version__ = "0.4.0"


from pathlib import Path
from loguru import logger
from .init import initialize

stub = Path(__file__).parent / "resource" / "ops_initialized"

if not stub.exists() or stub.open('r', encoding='utf-8').read() != __version__:
    logger.critical("Operator Resources has not initialized yet")
    logger.warning("Please execute arknights_toolkit.initialize()")
else:
    from .gacha import ArknightsGacha, GachaUser
    from .random_operator import RandomOperator
    from .recruit import recruitment
    from .info import query
    from .wordle import OperatorWordle
    from .record import ArkRecord
