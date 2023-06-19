from dataclasses import dataclass
from typing import Tuple

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass(kw_only=True)
class Leaf:
    pos_x: int
    pos_y: int
    t: Tuple[int, int]
    offset_x: int
    offset_y: int
    direction: int
    growth_index: int
    mass: float = 0.0001
    age: float = 0
    growth_time: int = 60 * 60 * 24 * 10  # was called lifetime
