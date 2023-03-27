import dataclasses
from dataclasses import dataclass
from typing import Final

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Water:
    """
    Klasse, die alle Informationen über den Wasservorrat beinhält.

    """

    water_pool: int = 0
    water_intake: int = 0
    water_intake_pool: int = 0
    max_water_pool: Final[int] = 1000000
    max_water_pool_consumption: Final[int] = 1

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def get_water_drain(self) -> int:
        return self.water_intake + self.max_water_pool

