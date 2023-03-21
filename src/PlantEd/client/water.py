import dataclasses
import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Water:
    """
    Klasse, die alle Informationen über den Wasservorrat beinhält.

    """

    water_pool: int
    max_water_pool: int

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)
