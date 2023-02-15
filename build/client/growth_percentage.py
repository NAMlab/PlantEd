import dataclasses
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class GrowthPercent:
    """
    Klasse, die die verteilung der Stärke beschreibt. Alle Werte sind in Prozent.

    Attributes:
        leaf (float):
        stem (float):
        root (float):
        starch (float):
        flower (float):
    """

    leaf: float
    stem: float
    root: float
    starch: float
    flower: float

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)
