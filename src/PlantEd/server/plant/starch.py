import logging
from dataclasses import dataclass
from typing import Final

from dataclasses_json import dataclass_json

from PlantEd.exceptions.pools import NegativePoolError

# ↓ according to doi: 10.1073/pnas.021304198
gram_starch_per_gram_fresh_weight: Final[float] = 0.0015

# ↓ according to https://doi.org/10.1046/j.0028-646X.2001.00320.x
gram_fresh_weight_per_gram_dry_weight: Final[float] = 5.0

gram_starch_per_micromol_starch: Final[float] = 0.0001621406
micromol_starch_per_gram_starch: Final[float] = (
    1 / gram_starch_per_micromol_starch
)

logger = logging.getLogger(__name__)
logger.propagate = True


@dataclass_json
@dataclass
class Starch:
    """
    Class that manages the strength pool of a plant.
    Unless explicitly stated otherwise, all values are in micromol.

    Attributes:
        allowed_starch_pool_consumption (float): Percentage of the starch pool
            that the plant is allowed to consume during the next simulation
            step.
    """

    def __init__(self):
        self.__available_starch_pool: float = (
            4.0 * micromol_starch_per_gram_starch
        )
        self.__max_starch_pool: float = 0.0
        self.starch_out: float = 0.0
        self.starch_in: float = 0.0
        self.allowed_starch_pool_consumption: float = 100.0

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
                "The Starch Pool is to be set below zero."
                " This should not happen and indicates "
                "a calculation error."
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
        float: The stored strength converted to grams.
        """
        return self.__available_starch_pool * gram_starch_per_micromol_starch

    @property
    def starch_usage_in_gram(self) -> float:
        """
        float: The used starch of the model in gram in the last simulation.
        """
        return self.starch_in * gram_starch_per_micromol_starch

    @property
    def starch_production_in_gram(self) -> float:
        """
        float: The produced starch of the model in gram in the last simulation.
        """
        return self.starch_out * gram_starch_per_micromol_starch

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

        max_starch_pool_in_gram = biomass_in_gram * gram_fresh_weight_per_gram_dry_weight * gram_starch_per_gram_fresh_weight
        max_starch_pool_in_micromol = max_starch_pool_in_gram * micromol_starch_per_gram_starch
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

        Returns: Maximum usable starch in micromol / (second * gram_of_organ).
        """

        try:
            value = self.available_starch_pool / (
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
