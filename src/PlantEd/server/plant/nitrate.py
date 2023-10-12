from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass

from PlantEd.constants import (
    MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT,
    START_NITRATE_POOL_IN_MICROMOL,
    PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
    PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP,
)

logger = logging.getLogger(__name__)


@dataclass
class Nitrate:
    # ToDo environment where the plant gets the nitrate from at the
    #  moment nitrate directly goes into the pool

    def __init__(self, plant_weight_gram: float):
        self.__max_nitrate_pool: int = 0
        self.update_nitrate_pool_based_on_plant_weight(
            plant_weight_gram=plant_weight_gram
        )

        if START_NITRATE_POOL_IN_MICROMOL > 0:
            nitrate_pool = START_NITRATE_POOL_IN_MICROMOL
        else:
            nitrate_pool = (
                abs(START_NITRATE_POOL_IN_MICROMOL) * self.__max_nitrate_pool
            )

        self.nitrate_pool: int = nitrate_pool

        self.nitrate_intake: int = 0

    def __repr__(self):
        string = (
            f"Nitrate object with following values:"
            f" nitrate_pool is {self.nitrate_pool} µmol"
            f" nitrate_intake is {self.nitrate_intake} µmol"
            f" max_nitrate_pool is {self.max_nitrate_pool} µmol."
        )

        return string

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    @property
    def missing_amount(self) -> float:
        """
        Provides the amount of water that can still be added to the pool.

        Returns:
            float: Amount of water that can still be added to the pool
             in micromol.
        """
        if self.nitrate_pool > self.__max_nitrate_pool:
            return 0

        return self.__max_nitrate_pool - self.nitrate_pool

    def to_dict(self) -> dict:
        dic = {}

        dic["nitrate_pool"] = self.nitrate_pool
        dic["nitrate_intake"] = self.nitrate_intake
        dic["max_nitrate_pool"] = self.__max_nitrate_pool

        return dic

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, dic: dict) -> Nitrate:
        nitrate = Nitrate(plant_weight_gram=0)

        nitrate.nitrate_pool = dic["nitrate_pool"]
        nitrate.nitrate_intake = dic["nitrate_intake"]
        nitrate.__max_nitrate_pool = dic["max_nitrate_pool"]

        return nitrate

    @classmethod
    def from_json(cls, string: str) -> Nitrate:
        dic = json.loads(string)
        return Nitrate.from_dict(dic=dic)

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
        # Pool usage factors (see constants.py)
        value = min(
            self.nitrate_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
            self.__max_nitrate_pool
            * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP,
        )

        try:
            value = value / (gram_of_organ * time_in_seconds)
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organ "
                f"mass ({gram_of_organ}) are 0. "
                f"Therefore, the available_absolute µmol per time and "
                f"gram cannot be calculated."
            ) from e

        logger.debug(
            f"Within a time of {time_in_seconds} seconds, an organ "
            f"with {gram_of_organ} grams of biomass has a "
            f"maximum of {value} µomol/(second * gram) of"
            f" nitrate available_absolute."
        )

        return value

    def update_nitrate_pool_based_on_plant_weight(self, plant_weight_gram):
        new_max_pool = (
            MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT * plant_weight_gram
        )

        logger.debug(
            f"Setting max_nitrate_pool to {new_max_pool} µmol."
            f" Based on a biomass of {plant_weight_gram} grams."
        )

        self.__max_nitrate_pool = new_max_pool
