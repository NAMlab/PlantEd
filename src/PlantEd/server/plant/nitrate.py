import dataclasses
from dataclasses import dataclass
from typing import Final

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Nitrate:
    nitrate_pool: int = 0
    nitrate_delta_amount: int = 0
    max_nitrate_pool_low: Final[int] = 12000  # mikromol
    max_nitrate_pool_high: Final[int] = 100000  # mikromol
    max_nitrate_pool: int = max_nitrate_pool_high

    # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
    nitrate_intake: int = 0

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def set_pool_to_high(self):
        self.nitrate_pool = self.max_nitrate_pool_high

    def get_nitrate_percentage(self) -> float:
        """
        Method to retrieve the level of the nitrate pool as a decimal number.
        (NitratePool/ MaxNitratePool).

        """

        return self.nitrate_pool / self.max_nitrate_pool_high
