from PlantEd.client.water import Water
from PlantEd.client.growth_rates import GrowthRates
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.leaf import Leaf


class Plant:

    def __init__(self):

        self.leafs: list[Leaf] = []
        self.leafs_biomass: int = 0

        self.water: Water = Water()
        self.nitrate: Nitrate = Nitrate()

    def set_water(self, water: Water):
        self.water = water

    def set_nitrate(self, nitrate:Nitrate):
        self.nitrate = nitrate


    def new_leaf(self, leaf: Leaf):
        self.leafs.append(leaf)

    def increase_biomass(self, growthrates:GrowthRates):

        assert growthrates.unit == "grams"

        self.leafs_biomass += growthrates.leaf_rate

