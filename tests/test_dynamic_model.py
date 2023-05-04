from copy import copy
from unittest import TestCase

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.fba.dynamic_model import DynamicModel


class TestDynamicModel(TestCase):
    def test_init_constraints(self):
        self.fail()

    def test_calc_growth_rate(self):
        self.fail()

    def test_open_stomata(self):
        self.fail()

    def test_update_transpiration_factor(self):
        self.fail()

    def test_update_transpiration(self):
        self.fail()

    def test_close_stomata(self):
        self.fail()

    def test_get_photon_upper(self):
        self.fail()

    def test_get_nitrate_pool(self):
        self.fail()

    def test_increase_nitrate_pool(self):
        self.fail()

    def test_get_nitrate_intake(self):
        self.fail()

    def test_stop_water_intake(self):
        self.fail()

    def test_enable_water_intake(self):
        self.fail()

    def test_set_bounds(self):
        self.fail()

    def test_get_bounds(self):
        self.fail()

    def test_increase_nitrate(self):
        self.fail()

    def test_set_stomata_automation(self):
        self.fail()

    def test_activate_starch_resource(self):
        self.fail()

    def test_deactivate_starch_resource(self):
        self.fail()

    def test_update(self):
        self.fail()

    def test_update_pools(self):
        self.fail()

    def test_update_bounds(self):
        self.fail()

    def test_update_constraints(self):
        dyn_model = DynamicModel()
        growth_percent = GrowthPercent(
            leaf= 50,
            stem= 0,
            root= 50,
            starch=0,
            flower=0,
            time_frame=6000,
        )

        leaf_old = dyn_model.plant.leafs_biomass_gram
        root_old = dyn_model.plant.root_biomass_gram

        dyn_model.calc_growth_rate(growth_percent)

        leaf_new = dyn_model.plant.leafs_biomass_gram
        root_new = dyn_model.plant.root_biomass_gram

        self.assertEqual(leaf_new- leaf_old, root_new- root_old)