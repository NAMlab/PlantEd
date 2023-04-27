import dataclasses
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class GrowthPercent:
    """
    Class, which describes the distribution of growth.
    The percentages are to be given as decimal numbers. I.e. 50% as 0.5.

    Attributes:
        leaf (float):
        stem (float):
        root (float):
        starch (float):
        flower (float):
        time_frame (int):
    """

    leaf: float
    stem: float
    root: float
    starch: float
    flower: float
    time_frame: float

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)
