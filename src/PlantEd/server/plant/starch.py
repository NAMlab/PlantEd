import logging
from dataclasses import dataclass
from typing import Final

from dataclasses_json import dataclass_json

# ↓ according to doi: 10.1073/pnas.021304198
gram_starch_per_gram_fresh_weight:Final[float] = 0.001

gram_starch_per_micromol_starch:Final[float] = 0.0001621406
micromol_starch_per_gram_starch:Final[float] = 1/ gram_starch_per_micromol_starch

logger = logging.getLogger(__name__)
logger.propagate = True


@dataclass_json
@dataclass
class Starch:
    """
    Class that manages the strength pool of a plant.
    Unless explicitly stated otherwise, all values are in micromol.

    Attributes:
        available_starch_pool (float): The starch usable by the plant in micromol.
        allowed_starch_pool_consumption (float): Percentage of the starch pool
            that the plant is allowed to consume during the next simulation step.
    """

    __available_starch_pool: float = 4 * micromol_starch_per_gram_starch
    __max_starch_pool: float = 0
    starch_out: float = 0
    starch_in: float = 0
    allowed_starch_pool_consumption: float = 100

    @property
    def available_starch_pool(self):
        return self.__available_starch_pool

    @available_starch_pool.setter
    def available_starch_pool(self, value):
        if self.__available_starch_pool > self.max_starch_pool:
            if value > 0:
                return

            else:
                self.__available_starch_pool = self.__available_starch_pool + value
                return

        self.__available_starch_pool = min(value, self.__max_starch_pool)

    @property
    def available_starch_pool_gram(self):
        return self.__available_starch_pool * gram_starch_per_micromol_starch
    @property
    def max_starch_pool(self):
        """
        max_starch_pool (float): The maximum amount of starch that can be
        stored is scaled according to the mass of the plant.
        (1g biomass approx 0.1 mg storage)
        """

        return self.__max_starch_pool

    def scale_pool_via_biomass(self, biomass_in_gram: float):
        max_starch_pool = biomass_in_gram * gram_starch_per_gram_fresh_weight
        max_starch_pool = max_starch_pool * micromol_starch_per_gram_starch
        logging.debug(f"Setting max_starch_pool to {max_starch_pool}."
                      f"Based on a biomass of {biomass_in_gram} grams.")

        self.__max_starch_pool = max_starch_pool

    def calc_available_starch_in_mol_per_gram_and_time(
            self,
            gram_of_organ:float,
            time_in_seconds:float,
    ):

        value = self.available_starch_pool / (gram_of_organ * time_in_seconds)
        value = value * self.allowed_starch_pool_consumption

        logging.debug(f"Within a time of {time_in_seconds} seconds, an organ "
                      f"with {gram_of_organ} grams of biomass has a "
                      f"maximum of {value} micromol/(second * gram) of starch available.")

        return value

