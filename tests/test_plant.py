import logging
from unittest import TestCase

from PlantEd.client.water import Water
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.plant import Plant
from PlantEd.server.plant.starch import Starch

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)


class TestPlant(TestCase):
    def test_to_json(self):
        plant = Plant(ground_grid_resolution=(20, 6))
        plant.leafs_biomass = 3
        plant.stem_biomass = 56
        plant.root_biomass = 24
        plant.seed_biomass = 18

        plant.co2 = 85
        plant.photon = 347

        starch = Starch(plant_weight_gram=254)
        plant.starch_pool = starch

        water = Water(plant_weight_gram=257)
        plant.water = water

        nitrate = Nitrate(plant_weight_gram=734)
        plant.nitrate = nitrate

        plant.stomata_open = True

        string_rep = plant.to_json()
        new_plant = Plant.from_json(string=string_rep)

        print(plant.to_dict())
        print(new_plant.to_dict())
        self.assertEqual(plant, new_plant)

    def test_to_dict(self):
        plant = Plant(ground_grid_resolution=(20, 6))
        plant.leafs_biomass = 3.4
        plant.stem_biomass = 2
        plant.root_biomass = 1
        plant.seed_biomass = 1.5

        self.assertEqual(plant, Plant.from_dict(plant.to_dict()))

    def test_from_dict(self):
        self.fail()

    def test_from_json(self):
        self.fail()

    def test_starch_out(self):
        self.fail()

    def test_starch_out(self):
        self.fail()

    def test_starch_in(self):
        self.fail()

    def test_starch_in(self):
        self.fail()

    def test_leafs_biomass_gram(self):
        self.fail()

    def test_stem_biomass_gram(self):
        self.fail()

    def test_root_biomass_gram(self):
        self.fail()

    def test_seed_biomass_gram(self):
        self.fail()

    def test_biomass_total(self):
        self.fail()

    def test_biomass_total_gram(self):
        self.fail()

    def test_specific_leaf_area_in_square_meter(self):
        self.fail()

    def test_set_water(self):
        self.fail()

    def test_set_nitrate(self):
        self.fail()

    def test_new_leaf(self):
        self.fail()

    def test_update_max_water_pool(self):
        self.fail()

    def test_update_max_starch_pool(self):
        self.fail()

    def test_update_transpiration(self):
        self.fail()

    def test_update_nitrate_pool_intake(self):
        self.fail()

    def test_update_max_nitrate_pool(self):
        self.fail()
