import dataclasses
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class GrowthRates:
    """
    Klasse, die alle Informationen der growth rate beinhält.

    Attributes:
        leaf_rate (float):
        stem_rate (float):
        root_rate (float):
        starch_rate (float):
        starch_intake (float):
        seed_rate (float):
    """

    leaf_rate: float
    stem_rate: float
    root_rate: float
    starch_rate: float
    starch_intake: float
    seed_rate: float

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)
