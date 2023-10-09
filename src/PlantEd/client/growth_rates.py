from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass
from typing import Literal, Final

from dataclasses_json import dataclass_json

logger = logging.getLogger(__name__)


FLUX_TO_GRAMM: Final[float] = 0.002299662183


@dataclass_json
@dataclass
class GrowthRates:
    """
    The unit of the data contained. Internally, as mol.

    Attributes:
        unit (str):
        leaf_rate (float):
        stem_rate (float):
        root_rate (float):
        starch_rate (float):
        starch_intake (float): actual starch consumption
        seed_rate (float):
        time_frame (float): The Timeframe
    """

    unit: Literal["mol"]
    leaf_rate: float
    stem_rate: float
    root_rate: float
    starch_rate: float
    starch_intake: float
    seed_rate: float
    time_frame: float

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def __radd__(self, other):
        return (
            other
            + self.leaf_rate
            + self.stem_rate
            + self.root_rate
            + self.starch_rate
            + self.starch_rate
            + self.seed_rate
        )
