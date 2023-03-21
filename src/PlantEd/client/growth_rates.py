from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass
from typing import Literal, Final

from dataclasses_json import dataclass_json

from PlantEd.utils.gametime import GameTime

logger = logging.getLogger(__name__)


FLUX_TO_GRAMM: Final[float] = 0.002299662183


@dataclass_json
@dataclass
class GrowthRates:
    """
    The unit of the data contained. Internally, either 1flux/s is used
    or grams within a specified context.

    Attributes:
        unit (str):
        leaf_rate (float):
        stem_rate (float):
        root_rate (float):
        starch_rate (float):
        starch_intake (float): actual starch consumption
        seed_rate (float):
    """

    unit: Literal["1flux/s", "grams"]
    leaf_rate: float
    stem_rate: float
    root_rate: float
    starch_rate: float
    starch_intake: float
    seed_rate: float

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def flux2grams(self, gametime: GameTime) -> GrowthRates:
        """
        Method to obtain the GrowthRates in grams for the specified time period.

        Args:
            gametime: Gametime object that defines the speed and thus also
            the time period for the GrowthRates. The GAMESPEED variable is
            used here.

        Returns: The growth rates of all organs in grams for the specified time.

        """
        gamespeed = gametime.GAMESPEED

        logger.debug(
            f"Create GrowthRates object in grams from {self} for a period of {gamespeed} seconds."
        )

        leaf = self.leaf_rate * gamespeed * FLUX_TO_GRAMM
        stem = self.stem_rate * gamespeed * FLUX_TO_GRAMM
        root = self.root_rate * gamespeed * FLUX_TO_GRAMM
        starch = self.starch_rate * gamespeed
        starch_intake = self.starch_intake * gamespeed
        seed = self.seed_rate * gamespeed

        growth_rates_grams = GrowthRates(
            unit="grams",
            leaf_rate=leaf,
            stem_rate=stem,
            root_rate=root,
            starch_rate=starch,
            starch_intake=starch_intake,
            seed_rate=seed,
        )

        return growth_rates_grams

    def __radd__(self, other):
        return (
            other
            + self.leaf_rate
            + self.stem_rate
            + self.root_rate
            + self.starch_rate
            + self.starch_rate
            + self.seed_rate
        )
