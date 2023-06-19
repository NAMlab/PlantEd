from __future__ import annotations

import json

from PlantEd.client.water import Water
from PlantEd.constants import LEAF_BIOMASS_GRAM_PER_MICROMOL, STEM_BIOMASS_GRAM_PER_MICROMOL, \
    ROOT_BIOMASS_GRAM_PER_MICROMOL, SEED_BIOMASS_GRAM_PER_MICROMOL, START_LEAF_BIOMASS_GRAM, START_STEM_BIOMASS_GRAM, \
    START_ROOT_BIOMASS_GRAM, START_SEED_BIOMASS_GRAM, SLA_IN_SQUARE_METER_PER_GRAM
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.starch import Starch

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
        self.leafs_biomass: float = START_LEAF_BIOMASS_GRAM/ LEAF_BIOMASS_GRAM_PER_MICROMOL
        self.stem_biomass: float = START_STEM_BIOMASS_GRAM / STEM_BIOMASS_GRAM_PER_MICROMOL
        self.root_biomass: float = START_ROOT_BIOMASS_GRAM / ROOT_BIOMASS_GRAM_PER_MICROMOL
        self.seed_biomass: float = START_SEED_BIOMASS_GRAM / SEED_BIOMASS_GRAM_PER_MICROMOL

        self.co2: float = 0
        self.photon: float = 0

        biomass = self.biomass_total_gram
        self.starch_pool: Starch = Starch(plant_weight_gram= biomass)
        self.water: Water = Water(plant_weight_gram= biomass)
        self.nitrate: Nitrate = Nitrate(plant_weight_gram= biomass)

        self.stomata_open:bool = False

    def __repr__(self):
        string =f"Plant object with following biomass values:" \
                f" Leafs {self.leafs_biomass:.4E} µmol" \
                f" Stem {self.stem_biomass:.4E} µmol" \
                f" Root {self.root_biomass:.4E} µmol" \
                f" Seed {self.seed_biomass:.4E} µmol" \
                f" - other values :" \
                f" CO2 uptake is {self.co2:.4E} µmol;" \
                f" Photon uptake is {self.photon:.4E} µmol;" \
                f" Starch is {str(self.starch_pool)};" \
                f" Water is {str(self.water)};" \
                f" Nitrate is {str(self.nitrate)}" \

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

        plant.stomata_open = dic["stomata_open"]

        plant.water = Water.from_dict(dic["water"])
        plant.nitrate = Nitrate.from_dict(dic["nitrate"])
        plant.starch_pool = Starch.from_dict(dic["starch"])

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
