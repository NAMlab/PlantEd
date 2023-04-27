from __future__ import annotations

import json

from PlantEd.client.water import Water
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.leaf import Leaf


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
        starch_out (float):
        starch_in (float):

        water (Water):
        nitrate (Nitrate):

        photon_upper (float):
    """
    def __init__(self):
        self.leafs: list[Leaf] = []
        self.leafs_biomass: float = 0.0000000000001
        self.stem_biomass: float = 0.0000000000001
        self.root_biomass: float = 1 / 899.477379  # Corresponds to a mole root biomass.
        self.seed_biomass: float = 0.0000000000001

        self.co2: float = 0
        self.photon: float = 0
        self.starch_out: float = 0
        self.starch_in: float = 0

        self.water: Water = Water()
        self.nitrate: Nitrate = Nitrate()

        self.photon_upper: float = 0

    def to_json(self):
        dic = {}

        dic["leafs_biomass"] = self.leafs_biomass
        dic["stem_biomass"] = self.stem_biomass
        dic["root_biomass"] = self.root_biomass
        dic["seed_biomass"] = self.seed_biomass

        dic["co2"] = self.co2
        dic["photon"] = self.photon
        dic["starch_out"] = self.starch_out
        dic["starch_in"] = self.starch_in

        dic["water"] = self.water.to_json()
        dic["nitrate"] = self.nitrate.to_json()

        dic["photon_upper"] = self.photon_upper

        return json.dumps(dic)

    @classmethod
    def from_json(cls, string:str) -> Plant:
        dic = json.loads(string)

        plant = Plant()

        plant.leafs_biomass = dic["leafs_biomass"]
        plant.stem_biomass = dic["stem_biomass"]
        plant.root_biomass = dic["root_biomass"]
        plant.seed_biomass = dic["seed_biomass"]

        plant.co2 = dic["co2"]
        plant.photon = dic["photon"]
        plant.starch_out = dic["starch_out"]
        plant.starch_in = dic["starch_in"]

        plant.water = Water.from_json(dic["water"])
        plant.nitrate = Nitrate.from_json(dic["nitrate"])

        plant.photon_upper = dic["photon_upper"]

        return plant

    @property
    def leafs_biomass_gram(self):
        return self.leafs_biomass * 899.477379

    @property
    def stem_biomass_gram(self):
        return self.stem_biomass * 916.2985939

    @property
    def root_biomass_gram(self):
        return self.root_biomass * 956.3297883

    @property
    def seed_biomass_gram(self):
        return self.seed_biomass * 978.8487602

    @property
    def biomass_total(self):
        return self.leafs_biomass + self.stem_biomass + self.root_biomass + self.seed_biomass

    @property
    def biomass_total_gram(self):
        return self.leafs_biomass_gram + self.stem_biomass_gram + self.root_biomass_gram + self.seed_biomass_gram


    def set_water(self, water: Water):
        self.water = water

    def set_nitrate(self, nitrate: Nitrate):
        self.nitrate = nitrate

    def new_leaf(self, leaf: Leaf):
        self.leafs.append(leaf)

    def update_max_water_pool(self):
        self.water.update_max_water_pool(plant_biomass=self.biomass_total)
