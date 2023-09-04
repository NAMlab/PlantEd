from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from PlantEd.constants import GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT, GRAM_STARCH_PER_GRAM_FRESH_WEIGHT, \
    MICROMOL_STARCH_PER_GRAM_STARCH, GRAM_STARCH_PER_MICROMOL_STARCH, START_STARCH_POOL_IN_MICROMOL, \
    PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP, PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP
from PlantEd.exceptions.pools import NegativePoolError

logger = logging.getLogger(__name__)

@dataclass
class Starch:
    """
    Class that manages the strength pool of a plant.
    Unless explicitly stated otherwise, all values are in micromol.

    Attributes:
        allowed_starch_pool_consumption (float): Percentage of the starch pool
            that the plant is allowed to consume during the next simulation
            step. 50% corresponds to an allowed_starch_pool_consumption of 0.5.
    """

    def __init__(self, plant_weight_gram: float):
        self.__max_starch_pool: float = 0.0
        self.scale_pool_via_biomass( biomass_in_gram= plant_weight_gram)

        self.starch_out: float = 0.0
        self.starch_in: float = 0.0
        self.allowed_starch_pool_consumption: float = 1.0

        if START_STARCH_POOL_IN_MICROMOL > 0:
            available_starch_pool = START_STARCH_POOL_IN_MICROMOL
        else:
            available_starch_pool = abs(START_STARCH_POOL_IN_MICROMOL) * self.__max_starch_pool
        self.__available_starch_pool: float = available_starch_pool

    def __repr__(self):
        string = f"Starch object with following values:" \
                 f" available starch pool is {self.__available_starch_pool} micromol," \
                 f" __max_starch_pool is {self.__max_starch_pool}," \
                 f" starch_out is {self.starch_out}, starch_in is {self.starch_in}," \
                 f" allowed_starch_pool_consumption is {self.allowed_starch_pool_consumption}"

        return string

    def to_dict(self) -> dict:
        dic = {}

        dic["max_starch_pool"] = self.__max_starch_pool
        dic["starch_out"] = self.starch_out
        dic["starch_in"] = self.starch_in
        dic["allowed_starch_pool_consumption"] = self.allowed_starch_pool_consumption
        dic["available_starch_pool"] = self.__available_starch_pool

        return dic

    def to_json(self) -> str:

        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, dic:dict) -> Starch:
        starch = Starch(plant_weight_gram= 0)

        starch.__max_starch_pool = dic["max_starch_pool"]
        starch.starch_out = dic["starch_out"]
        starch.starch_in = dic["starch_in"]
        starch.allowed_starch_pool_consumption = dic["allowed_starch_pool_consumption"]
        starch.__available_starch_pool = dic["available_starch_pool"]

        return starch

    @classmethod
    def from_json(cls, string:str) -> Starch:
        dic = json.loads(string)

        return Starch.from_dict(dic= dic)

    @property
    def available_starch_pool(self) -> float:
        """
        float: The stored starch in micromol. This value can be greater than
        `max_starch_pool` due to initialization. However, so only consumed and
        not increased. Only after `available_starch_pool` falls below
        `max_starch_pool` can `available_starch_pool` increase. From this point
        on, however, `available_starch_pool` can no longer become larger
        than `max_starch_pool`. Setting `available_starch_pool` to a negative
        number raises a :py:class:`NegativePoolError`.
        """
        return self.__available_starch_pool

    @available_starch_pool.setter
    def available_starch_pool(self, value: float):
        if value < 0:
            raise NegativePoolError(
                f"The Starch Pool is to be set below zero ({value})."
                f" This should not happen and indicates "
                f"a calculation error."
            )

        pool_change = value - self.__available_starch_pool

        if self.__available_starch_pool > self.max_starch_pool:
            if pool_change > 0:
                return

            else:
                self.__available_starch_pool = value
                return

        self.__available_starch_pool = min(value, self.__max_starch_pool)

    @property
    def available_starch_pool_gram(self) -> float:
        """
        float: The stored starch converted to grams.
        """
        return self.__available_starch_pool * GRAM_STARCH_PER_MICROMOL_STARCH

    @property
    def starch_usage_in_gram(self) -> float:
        """
        float: The used starch of the model in gram in the last simulation.
        """
        return self.starch_in * GRAM_STARCH_PER_MICROMOL_STARCH

    @property
    def starch_production_in_gram(self) -> float:
        """
        float: The produced starch of the model in gram in the last simulation.
        """
        return self.starch_out * GRAM_STARCH_PER_MICROMOL_STARCH

    @property
    def max_starch_pool(self) -> float:
        """
        max_starch_pool (float): The maximum amount of starch that can be
        stored is scaled according to the mass of the plant.
        (1g biomass approx 0.1 mg storage)
        """

        return self.__max_starch_pool

    def scale_pool_via_biomass(self, biomass_in_gram: float):
        """
        Method that calculates the maximum starch pool based on the
        biomass of the whole plant and updates max_starch_pool.


        Args:
            biomass_in_gram: The biomass of the whole plant in gram.

        """

        max_starch_pool_in_gram = biomass_in_gram * GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT * GRAM_STARCH_PER_GRAM_FRESH_WEIGHT
        max_starch_pool_in_micromol = max_starch_pool_in_gram * MICROMOL_STARCH_PER_GRAM_STARCH
        logging.debug(
            f"Setting max_starch_pool to {max_starch_pool_in_micromol} micromol."
            f"Based on a biomass of {biomass_in_gram} grams."
        )

        self.__max_starch_pool = max_starch_pool_in_micromol

    def calc_available_starch_in_mol_per_gram_and_time(
        self,
        gram_of_organ: float,
        time_in_seconds: float,
    ) -> float:
        """
        Method that calculates the maximum extractable starch from the pool.
        This is done on the basis of a time period and the mass of the
        organ that has access to this reservoir. The value calculated
        here corresponds to the `upper_bound` within a
        :py:class:`cobra.Reaction`.
        The unit is micromol / (second * gram_of_organ).
        Args:
            gram_of_organ: The organ mass in gram.
            time_in_seconds: The time span over which the pool is accessed in
                seconds.

        Returns: Maximum usable starch in micromol / (second * gram).
        """

        # Pool usage factors (see constants.py)
        value = min(self.available_starch_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
                    self.__max_starch_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP)

        try:
            value = value / (
                gram_of_organ * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({gram_of_organ}) are 0. "
                f"Therefore, the available micromole per time and "
                f"gram cannot be calculated."
            ) from e

        value = value * self.allowed_starch_pool_consumption

        logging.debug(
            f"Within a time of {time_in_seconds} seconds, an organ "
            f"with {gram_of_organ} grams of biomass has a "
            f"maximum of {value} micromol/(second * gram) of starch available."
        )

        return value
