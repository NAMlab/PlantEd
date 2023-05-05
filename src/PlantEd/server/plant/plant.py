from __future__ import annotations

import json
from typing import Final

from PlantEd.client.water import Water
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.starch import Starch

# ↓ value according to https://doi.org/10.1007/s13595-019-0911-2
# ↓ Leaf Mass per Area (LMA)
LMA_IN_GRAM_PER_SQUARE_METER: Final[float] = 40

# ↓ Specific leaf Area (SLA)
SLA_IN_SQUARE_METER_PER_GRAM: Final[float] = 1/LMA_IN_GRAM_PER_SQUARE_METER

LEAF_BIOMASS_GRAM_PER_MICROMOL = 899.477379 / 1000000
STEM_BIOMASS_GRAM_PER_MICROMOL = 916.2985939 / 1000000
ROOT_BIOMASS_GRAM_PER_MICROMOL = 956.3297883 / 1000000
SEED_BIOMASS_GRAM_PER_MICROMOL = 978.8487602 / 1000000

class Plant:
    """

    Attributes:
        leafs (list[Leaf]):
        leafs_biomass (float):
        stem_biomass (float):
        root_biomass (float):
        seed_biomass (float):

        co2 (float):
        photon (float):

        starch_pool (float): Starch Object represents the starch pool of
            the plant as well as starch production and consumption.

        water (Water):
        nitrate (Nitrate):

        photon_upper (float):
    """
    def __init__(self):
        self.leafs: list[Leaf] = []
        self.leafs_biomass: float = 0.1/ LEAF_BIOMASS_GRAM_PER_MICROMOL
        self.stem_biomass: float = 0.1 / STEM_BIOMASS_GRAM_PER_MICROMOL
        self.root_biomass: float = 1 / ROOT_BIOMASS_GRAM_PER_MICROMOL  # Corresponds to 1 gram root biomass.
        self.seed_biomass: float = 0.1 / SEED_BIOMASS_GRAM_PER_MICROMOL

        self.co2: float = 0
        self.photon: float = 0

        self.starch_pool: Starch = Starch()
        self.starch_pool.scale_pool_via_biomass(self.biomass_total_gram)

        self.water: Water = Water()
        self.nitrate: Nitrate = Nitrate()

        self.photon_upper: float = 0
        self.stomata_open:bool = False

    def __repr__(self):
        string =f"Plant object with following biomass values:" \
                f" Leafs {self.leafs_biomass:.4E} mol" \
                f" Stem {self.stem_biomass:.4E} mol" \
                f" Root {self.root_biomass:.4E} mol" \
                f" Seed {self.seed_biomass:.4E} mol" \
                f" - other values :" \
                f" CO2 uptake is {self.co2:.4E} mol;" \
                f" Photon uptake is {self.photon:.4E} mol with " \
                f"an upper bound of {self.photon_upper:.4E} " \
                f"mol/(g_leaf_biomass * seconds);" \
                f" Starch is {self.starch_pool} mol;" \
                f" Water is {str(self.water)};" \
                f" Nitrate is {str(self.nitrate)}" \

        return string

    def to_json(self) -> str:
        """
        Function that returns the plant object encoded in json. Using the
        from_json function a new plant object can be created whose instance
        variables are identical to those of the original object.

        Returns: A JSON string that contains all instance variables
        of the Plant Object.

        """

        return json.dumps(self.to_dict())

    def to_dict(self):
        """
        Function that returns the plant object encoded as :py:class:`dict`.
        Using the :py:meth:`from_dict` method a new plant object can be
        created whose instance variables are identical to those of the
        original object.

        Returns: The instance variables of the :py:class:`Plant` object
        encoded as a :py:class:`dict`.

        """
        dic = {}

        dic["leafs_biomass"] = self.leafs_biomass
        dic["stem_biomass"] = self.stem_biomass
        dic["root_biomass"] = self.root_biomass
        dic["seed_biomass"] = self.seed_biomass

        dic["co2"] = self.co2
        dic["photon"] = self.photon
        dic["starch_out"] = self.starch_out
        dic["starch_in"] = self.starch_in

        dic["water"] = self.water.to_dict()
        dic["nitrate"] = self.nitrate.to_json()

        dic["photon_upper"] = self.photon_upper

        return dic

    @classmethod
    def from_dict(cls, dic:dict) -> Plant:
        plant = Plant()

        plant.leafs_biomass = dic["leafs_biomass"]
        plant.stem_biomass = dic["stem_biomass"]
        plant.root_biomass = dic["root_biomass"]
        plant.seed_biomass = dic["seed_biomass"]

        plant.co2 = dic["co2"]
        plant.photon = dic["photon"]
        plant.starch_out = dic["starch_out"]
        plant.starch_in = dic["starch_in"]

        plant.water = Water.from_dict(dic["water"])
        plant.nitrate = Nitrate.from_json(dic["nitrate"])

        plant.photon_upper = dic["photon_upper"]

        return plant

    @classmethod
    def from_json(cls, string:str) -> Plant:
        dic = json.loads(string)

        return Plant.from_dict(dic = dic)

    @property
    def starch_out(self):
        return self.starch_pool.starch_out

    @starch_out.setter
    def starch_out(self, value):
        self.starch_pool.starch_out = value

    @property
    def starch_in(self):
        return self.starch_pool.starch_in

    @starch_in.setter
    def starch_in(self, value):
        self.starch_pool.starch_in = value

    @property
    def leafs_biomass_gram(self):
        return self.leafs_biomass * LEAF_BIOMASS_GRAM_PER_MICROMOL

    @property
    def stem_biomass_gram(self):
        return self.stem_biomass * STEM_BIOMASS_GRAM_PER_MICROMOL

    @property
    def root_biomass_gram(self):
        return self.root_biomass * ROOT_BIOMASS_GRAM_PER_MICROMOL

    @property
    def seed_biomass_gram(self):
        return self.seed_biomass * SEED_BIOMASS_GRAM_PER_MICROMOL

    @property
    def biomass_total(self):
        return self.leafs_biomass + self.stem_biomass + self.root_biomass + self.seed_biomass

    @property
    def biomass_total_gram(self):
        return self.leafs_biomass_gram + self.stem_biomass_gram + self.root_biomass_gram + self.seed_biomass_gram

    @property
    def specific_leaf_area_in_square_meter(self):
        return SLA_IN_SQUARE_METER_PER_GRAM * self.leafs_biomass_gram


    def set_water(self, water: Water):
        self.water = water

    def set_nitrate(self, nitrate: Nitrate):
        self.nitrate = nitrate

    def new_leaf(self, leaf: Leaf):
        self.leafs.append(leaf)

    def update_max_water_pool(self):
        self.water.update_max_water_pool(plant_biomass=self.biomass_total_gram)

    def update_max_starch_pool(self):
        self.starch_pool.scale_pool_via_biomass(biomass_in_gram= self.biomass_total_gram)

    def update_transpiration(self, transpiration_factor: float):
        self.water.update_transpiration(
            stomata_open= self.stomata_open,
            co2_uptake_in_micromol= self.co2,
            transpiration_factor = transpiration_factor,
        )

    def update_nitrate_pool_intake(self, seconds:int):
        self.nitrate.update_nitrate_pool_based_on_root_weight(
            root_weight_in_gram= self.root_biomass_gram,
            time_in_seconds= seconds
        )

    def update_max_nitrate_pool(self):
        self.nitrate.update_nitrate_pool_based_on_plant_weight(
            plant_weight_gram= self.biomass_total_gram
        )
