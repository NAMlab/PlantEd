from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass
from typing import Final

from pydantic import confloat

from PlantEd.exceptions.pools import NegativeBiomassError

logger = logging.getLogger(__name__)


MAX_WATER_POOL_PER_GRAMM = 0.05550843506179199 * 1000 * 0.8


@dataclass
class Water:
    """
    This class represents the water pool of the plant. All values
    are in micromol unless otherwise stated.
    """

    water_pool: int = 0
    water_intake: int = 0
    water_intake_pool: int = 0
    transpiration: float = 0
    __max_water_pool: float = 4 * MAX_WATER_POOL_PER_GRAMM
    max_water_pool_consumption: Final[int] = 1

    def __repr__(self):
        string = f"Water object with following values:" \
                 f" water_pool is {self.water_pool}, water_intake is {self.water_intake}" \
                 f" water_intake_pool is {self.water_intake_pool}, transpiration is {self.transpiration}" \
                 f" max_water_pool is {self.max_water_pool}."

        return string

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def get_water_drain(self) -> float:
        return self.water_intake + self.__max_water_pool

    @property
    def max_water_pool(self) -> float:
        """
        Provides the maximum water storage capacity of the plant in micromol.
        """

        return self.__max_water_pool
    @property
    def fill_percentage(self) -> confloat(ge=0, le=1):
        """
        Returns the percentage level of the water supply as float.
        """
        percentage = self.water_pool / self.__max_water_pool
        logger.debug(f"Water Percentage is: {percentage}, {self.water_pool}, {self.__max_water_pool}")
        if percentage > 1 or percentage < 0:
            logger.warning(
                f"The water pool is over 100% full or in the "
                f"minus. It is {percentage}, where water_pool is "
                f"{self.water_pool} and max_water_pool is "
                f"{self.__max_water_pool}."
            )

        logger.debug(f"Calculated water percentage is {percentage} from {self}")
        return percentage

    def to_dict(self) -> dict:
        """
        A method that stores the variables of the instance in a
        :py:class:`dict`. From this :py:class:`dict`, a :py:class:`Water`
        object can be created with the same variables as the original.
        """

        dic =  {}
        dic["water_pool"] = self.water_pool
        dic["water_intake"] = self.water_intake
        dic["water_intake_pool"] = self.water_intake_pool
        dic["transpiration"] = self.transpiration
        dic["max_water_pool"] = self.__max_water_pool
        dic["max_water_pool_consumption"] = self.max_water_pool_consumption

        return dic

    @classmethod
    def from_dict(cls, dic:dict) -> Water:

        water = Water()

        water.water_pool = dic["water_pool"]
        water.water_intake = dic["water_intake"]
        water.water_intake_pool = dic["water_intake_pool"]
        water.transpiration = dic["transpiration"]
        water.__max_water_pool = dic["max_water_pool"]
        water.max_water_pool_consumption = dic["max_water_pool_consumption"]

        return water

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, string:str) -> Water:
        dic = json.loads(string)

        return Water.from_dict(dic = dic)



    def update_max_water_pool(self, plant_biomass: float):
        """
        Updates the upper limit of the water pool based on the
        biomass of the plant.

        Args:
            plant_biomass: The current biomass of the plant in gram.

        """
        if plant_biomass < 0:
            raise NegativeBiomassError("The given biomass of the plant is negative.")

        self.__max_water_pool = plant_biomass * MAX_WATER_POOL_PER_GRAMM

    def calc_available_water_in_mol_per_gram_and_time(
        self,
        gram_of_organ: float,
        time_in_seconds: float,
    ) -> float:

        try:
            value = self.water_pool / (
                gram_of_organ * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({gram_of_organ}) are 0. "
                f"Therefore, the available micromole per time and "
                f"gram cannot be calculated."
            ) from e

        logging.debug(
            f"Within a time of {time_in_seconds} seconds, an organ "
            f"with {gram_of_organ} grams of biomass has a "
            f"maximum of {value} micromol/(second * gram) of water available."
        )

        return value