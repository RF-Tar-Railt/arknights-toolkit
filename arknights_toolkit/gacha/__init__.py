from pathlib import Path

from loguru import logger

from .main import ArknightsGacha
from .model import GachaUser

if not (Path(__file__).parent.parent / "resource" / "ops_initialized").exists():
    logger.critical("Operator Resources has not initialized yet")
    logger.warning("Please execute ArknightsGacha.initialize()")
    logger.warning("Otherwise, you can't use simulate-image function")
else:
    from .simulate import simulate_image
