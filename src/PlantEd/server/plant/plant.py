from __future__ import annotations

import json
import logging

import numpy as np

from PlantEd.client.water import Water
from PlantEd.constants import (
    START_LEAF_BIOMASS_GRAM,
    START_STEM_BIOMASS_GRAM,
    START_ROOT_BIOMASS_GRAM,
    START_SEED_BIOMASS_GRAM,
    SLA_IN_SQUARE_METER_PER_GRAM,
)
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.starch import Starch
from PlantEd.utils.LSystem import LSystem, DictToRoot
from PlantEd import config

logger = logging.getLogger(__name__)

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

    def __init__(self, ground_grid_resolution: tuple[int, int]):
        self.leafs: list[Leaf] = []
        self.leafs_biomass: float = START_LEAF_BIOMASS_GRAM
        self.stem_biomass: float = START_STEM_BIOMASS_GRAM
        self.__root_biomass: float = START_ROOT_BIOMASS_GRAM
        self.seed_biomass: float = START_SEED_BIOMASS_GRAM

        self.co2: float = 0
        self.co2_uptake_in_micromol_per_second_and_gram: float = 0
        self.photon: float = 0

        biomass = self.biomass_total_gram
        self.starch_pool: Starch = Starch(plant_weight_gram=biomass)
        self.water: Water = Water(plant_weight_gram=biomass)
        self.nitrate: Nitrate = Nitrate(plant_weight_gram=biomass)

        self.stomata_open: bool = False

        self.root: LSystem = LSystem(
            root_grid=np.zeros(
                ground_grid_resolution
            ),  # same resolution as environment grids
            water_grid_pos=(0, 900),  # hardcoded at ui [game.py 310]
        )

    def __repr__(self):
        string = (
            f"Plant object with following biomass values:"
            f" Leafs {self.leafs_biomass:.4E} gram"
            f" Stem {self.stem_biomass:.4E} gram"
            f" Root {self.root_biomass:.4E} gram"
            f" Seed {self.seed_biomass:.4E} gram"
            f" - other values :"
            f" CO2 uptake is {self.co2:.4E} µmol"
            f" Photon uptake is {self.photon:.4E} µmol"
            f" Starch is {str(self.starch_pool)} µmol"
            f" Water is {str(self.water)} µmol"
            f" Nitrate is {str(self.nitrate)} µmol"
        )
        return string

    def __eq__(self, other):
        if not isinstance(other, Plant):
            return False

        own_vars = vars(self)
        other_vars = vars(other)

        for key in own_vars:
            if own_vars[key] != other_vars[key]:
                print(key)
                return False

        return True

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

        dic["stomata_open"] = self.stomata_open

        dic["water"] = self.water.to_dict()
        dic["nitrate"] = self.nitrate.to_dict()
        dic["starch"] = self.starch_pool.to_dict()

        dic["root"] = self.root.to_dict()

        return dic

    @classmethod
    def from_dict(cls, dic:dict) -> Plant:
        # Todo dirty hardcoded change
        plant = Plant((20,6))
        plant.leafs_biomass = dic["leafs_biomass"]
        plant.stem_biomass = dic["stem_biomass"]
        plant.root_biomass = dic["root_biomass"]

        plant.seed_biomass = dic["seed_biomass"]

        plant.co2 = dic["co2"]
        plant.photon = dic["photon"]

        plant.stomata_open = dic["stomata_open"]

        plant.water = Water.from_dict(dic["water"])
        plant.nitrate = Nitrate.from_dict(dic["nitrate"])
        plant.starch_pool = Starch.from_dict(dic["starch"])

        plant.root = DictToRoot.load_root_system(dic["root"])
        plant.root.root_grid = plant.root.root_grid.transpose()
        return plant

    @classmethod
    def from_json(cls, string: str) -> Plant:
        dic = json.loads(string)

        return Plant.from_dict(dic=dic)

    @property
    def root_biomass(self):
        return self.__root_biomass

    @root_biomass.setter
    def root_biomass(self, value):
        diff = value - self.root_biomass
        if diff < 0:
            logger.error(f"Root mass is decreasing. This is ignored! ")
            return

        self.root.update(diff)
        self.__root_biomass = value

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
        return self.leafs_biomass

    @property
    def stem_biomass_gram(self):
        return self.stem_biomass

    @property
    def root_biomass_gram(self):
        return self.root_biomass

    @property
    def seed_biomass_gram(self):
        return self.seed_biomass

    @property
    def biomass_total(self):
        return (
            self.leafs_biomass
            + self.stem_biomass
            + self.root_biomass
            + self.seed_biomass
        )

    @property
    def biomass_total_gram(self):
        return (
            self.leafs_biomass_gram
            + self.stem_biomass_gram
            + self.root_biomass_gram
            + self.seed_biomass_gram
        )

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
        self.starch_pool.scale_pool_via_biomass(biomass_in_gram=self.biomass_total_gram)

    def update_transpiration(self):
        self.water.update_transpiration(
            stomata_open=self.stomata_open,
            co2_uptake_in_micromol_per_second_and_gram=self.co2_uptake_in_micromol_per_second_and_gram,
            transpiration_factor=self.water.transpiration_factor,
        )

    def get_transpiration_in_micromol(self, time_in_s: int):
        return self.water.transpiration * self.leafs_biomass_gram * time_in_s

    def update_nitrate_pool_intake(self, seconds: int):
        self.nitrate.update_nitrate_pool_based_on_root_weight(
            root_weight_in_gram=self.root_biomass_gram, time_in_seconds=seconds
        )

    def update_max_nitrate_pool(self):
        self.nitrate.update_nitrate_pool_based_on_plant_weight(
            plant_weight_gram=self.biomass_total_gram
        )
