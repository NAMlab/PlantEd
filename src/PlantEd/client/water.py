from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass
from typing import Final

from pydantic import confloat

from PlantEd.constants import MAX_WATER_POOL_PER_GRAMM, START_WATER_POOL_IN_MICROMOL, \
    PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP, PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP
from PlantEd.exceptions.pools import NegativeBiomassError

logger = logging.getLogger(__name__)



@dataclass
class Water:
    """
    This class represents the water pool of the plant. All values
    are in µmol unless otherwise stated.
    """

    def __init__(self, plant_weight_gram: float):

        self.__max_water_pool: float = 0
        self.update_max_water_pool(plant_biomass= plant_weight_gram)

        if START_WATER_POOL_IN_MICROMOL > 0:
            water_pool = START_WATER_POOL_IN_MICROMOL
        else:
            water_pool = abs(START_WATER_POOL_IN_MICROMOL) * self.__max_water_pool

        self.__water_pool: float = water_pool
        self.water_intake: int = 0
        self.water_intake_pool: int = 0
        self.transpiration: float = 0

    def __repr__(self):
        string = f"Water object with following values:" \
                 f" water_pool is {self.water_pool} µmol, water_intake is {self.water_intake} µmol" \
                 f" water_intake_pool is {self.water_intake_pool} µmol, transpiration is {self.transpiration} µmol" \
                 f" max_water_pool is {self.max_water_pool} µmol."

        return string

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    @property
    def water_pool(self):
        return self.__water_pool

    @water_pool.setter
    def water_pool(self, value: float):
        self.__water_pool = min(self.__max_water_pool, value)


    def get_water_drain(self) -> float:
        return self.water_intake + self.__max_water_pool

    @property
    def max_water_pool(self) -> float:
        """
        Provides the maximum water storage capacity of the plant in µmol.
        """

        return self.__max_water_pool
    @property
    def fill_percentage(self) -> confloat(ge=0, le=1):
        """
        Returns the percentage level of the water supply as float.
        """
        percentage = self.water_pool / self.__max_water_pool
        if percentage > 1 or percentage < 0:
            logger.warning(
                f"The water pool is over 100% full or in the "
                f"minus. It is {percentage}, where water_pool is "
                f"{self.water_pool} µmol and max_water_pool is "
                f"{self.__max_water_pool} µmol."
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

        return dic

    @classmethod
    def from_dict(cls, dic:dict) -> Water:

        water = Water(plant_weight_gram=0)

        water.__water_pool = dic["water_pool"]
        water.water_intake = dic["water_intake"]
        water.water_intake_pool = dic["water_intake_pool"]
        water.transpiration = dic["transpiration"]
        water.__max_water_pool = dic["max_water_pool"]

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

        new_max_water_pool = plant_biomass * MAX_WATER_POOL_PER_GRAMM

        logger.debug(f"Setting new_max_water_pool to {new_max_water_pool} µmol.Based on a biomass of {plant_biomass} grams.")

        self.__max_water_pool = new_max_water_pool

    def calc_available_water_in_mol_per_gram_and_time(
        self,
        gram_of_organ: float,
        time_in_seconds: float,
    ) -> float:

        # Pool usage factors (see constants.py)
        value = min(self.water_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
                    self.__max_water_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP)

        try:
            value = value / (
                gram_of_organ * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({gram_of_organ}) are 0. "
                f"Therefore, the available µmole per time and "
                f"gram cannot be calculated."
            ) from e

        logger.debug(
            f"Within a time of {time_in_seconds} seconds, an organ "
            f"with {gram_of_organ} grams of biomass has a "
            f"maximum of {value} µmol/(second * gram) of water available."
        )

        return value

    def update_transpiration(self, stomata_open: bool, co2_uptake_in_micromol: float, transpiration_factor:float):
        transpiration = 0
        if stomata_open:
            if co2_uptake_in_micromol > 0:
                transpiration = co2_uptake_in_micromol * transpiration_factor

        logger.debug(f"Setting transpiration to {transpiration}. Based on CO2 intake of {co2_uptake_in_micromol} and a transpiration_factor of {transpiration_factor}" )
        self.transpiration = transpiration
