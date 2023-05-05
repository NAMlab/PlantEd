import dataclasses
import logging
from dataclasses import dataclass
from typing import Final

from dataclasses_json import dataclass_json

# ↓ value according to https://doi.org/10.1104/pp.105.074385
# ↓ only for Roots reported
# ↓ Arabidopsis thaliana
MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT = 7.9

# ↓ value according to https://doi.org/10.3389/fpls.2018.00884
# ↓ Arabidopsis thaliana
MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY = 0.00336
MAX_NITRATE_INTALE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND = MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY / 1000000 * 24 * 60 *60

logger = logging.getLogger(__name__)

@dataclass_json
@dataclass
class Nitrate:
    nitrate_pool: int = 10
    nitrate_delta_amount: int = 0

    __max_nitrate_pool: int = 0
    nitrate_intake: int = 0

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    @property
    def max_nitrate_pool(self):
        return self.__max_nitrate_pool

    def set_pool_to_high(self):
        self.nitrate_pool = self.__max_nitrate_pool

    def get_nitrate_percentage(self) -> float:
        """
        Method to retrieve the level of the nitrate pool as a decimal number.
        (NitratePool/ MaxNitratePool).

        """

        return self.nitrate_pool / self.__max_nitrate_pool

    def calc_available_nitrate_in_micromol_per_gram_and_time(
        self,
        gram_of_organ: float,
        time_in_seconds: float,
    ) -> float:

        try:
            value = self.nitrate_pool / (
                gram_of_organ * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organ "
                f"mass ({gram_of_organ}) are 0. "
                f"Therefore, the available micromole per time and "
                f"gram cannot be calculated."
            ) from e

        logger.debug(
            f"Within a time of {time_in_seconds} seconds, an organ "
            f"with {gram_of_organ} grams of biomass has a "
            f"maximum of {value} micromol/(second * gram) of water available."
        )

        return value

    def update_nitrate_pool_based_on_root_weight(self, root_weight_in_gram: float, time_in_seconds: int):
        self.nitrate_intake = MAX_NITRATE_INTALE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND * root_weight_in_gram * time_in_seconds

    def update_nitrate_pool_based_on_plant_weight(self, plant_weight_gram):
        new_max_pool = MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT * plant_weight_gram

        logger.debug(
            f"Setting max_nitrate_pool to {new_max_pool} micromol. Based on a biomass of {plant_weight_gram} grams.")

        self.__max_nitrate_pool = new_max_pool
