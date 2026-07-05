from clilte import CommandLine

from .plugins.init import Init
from .plugins.clear import Clear
from .plugins.update import Update

arkkit = CommandLine(
    "Command Line Interface for Arknights Toolkit",
    "0.8.1",
    rich=True,
    _name="arkkit",
    load_preset=True,
)
arkkit.add(Init, Clear, Update)
