from typing import TypedDict, Dict, List, NamedTuple
from dataclasses import dataclass, field


class Operator(NamedTuple):
    name: str
    rarity: int


class GachaData(TypedDict):
    name: str
    six_per: float
    five_per: float
    four_per: float
    operators: Dict[str, List[str]]  # 当期新 up 的干员不应该在里面
    up_limit: List[str]
    up_alert_limit: List[str]
    up_six_list: List[str]
    up_five_list: List[str]
    up_four_list: List[str]


@dataclass
class GachaUser:
    six_per: int = field(default=2)
    six_statis: int = field(default=0)


class UpdateChar(NamedTuple):
    name: str
    limit: bool
    chance: float


@dataclass
class UpdateResponse:
    title: str
    four_chars: List[UpdateChar]
    five_chars: List[UpdateChar]
    six_chars: List[UpdateChar]
    pool: str
