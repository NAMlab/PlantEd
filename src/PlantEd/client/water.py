import dataclasses
import logging
from dataclasses import dataclass
from typing import Final, Annotated

from dataclasses_json import dataclass_json
from pydantic import confloat

logger = logging.getLogger(__name__)

MAX_WATER_POOL_PER_GRAMM = 0.05550843506179199 * 1000000


@dataclass_json
@dataclass
class Water:
    """
    Class, which contains all the information about the water reserve of
    the plant.
    """

    water_pool: int = 0
    water_intake: int = 0
    water_intake_pool: int = 0
    transpiration: float = 0
    max_water_pool: float = MAX_WATER_POOL_PER_GRAMM
    max_water_pool_consumption: Final[int] = 1

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def get_water_drain(self) -> float:
        return self.water_intake + self.max_water_pool

    @property
    def fill_percentage(self) -> confloat(ge=0, le=1):
        """
        Returns the percentage level of the water supply as float.
        """
        percentage = self.water_pool / self.max_water_pool

        if percentage > 1 or percentage < 0:
            logger.warning(
                f"The water pool is over 100% full or in the "
                f"minus. It is {percentage}, where water_pool is "
                f"{self.water_pool} and max_water_pool is "
                f"{self.max_water_pool}."
            )

        return percentage

    def update_max_water_pool(self, plant_biomass: float):
        """
        Updates the upper limit of the water pool based on the
        biomass of the plant.

        Args:
            plant_biomass: The current biomass of the plant in gram.

        """
        self.max_water_pool = plant_biomass * MAX_WATER_POOL_PER_GRAMM
