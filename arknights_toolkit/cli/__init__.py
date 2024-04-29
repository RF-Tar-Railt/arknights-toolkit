from clilte import CommandLine

from .plugins.init import Init
from .plugins.update import Update
from .plugins.clear import Clear

arkkit = CommandLine(
    "Command Line Interface for Arknights Toolkit",
    "0.6.0",
    rich=True,
    _name="arkkit",
    load_preset=True,
)
arkkit.add(Init, Clear, Update)
