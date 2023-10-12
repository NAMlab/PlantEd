import logging
from unittest import TestCase, skip

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.server.environment.environment import Environment
from PlantEd.server.fba.dynamic_model import (
    DynamicModel,
    NITRATE,
    PHOTON,
    CO2,
    STARCH_OUT,
    STARCH_IN,
    WATER,
)
from PlantEd.server.plant.leaf import Leaf


class TestDynamicModel(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    @skip(
        "Should be replaced by shorter methods."
        " This requires splitting 'calc_growth_rate' from dynamic_model."
    )
    def test_calc_growth_rate(self):
        self.fail()

    def test_open_stomata(self):
        model = DynamicModel(enviroment=Environment())

        model.plant.stomata_open = False
        reaction = model.model.reactions.get_by_id("CO2_tx_leaf")
        reaction.bounds = (0, 0)

        self.assertFalse(model.plant.stomata_open)

        self.assertEqual(
            0,
            reaction.lower_bound,
        )
        self.assertEqual(
            0,
            reaction.upper_bound,
        )

        model.open_stomata()

        self.assertTrue(model.plant.stomata_open)
        reaction = model.model.reactions.get_by_id("CO2_tx_leaf")

        self.assertEqual(
            -1000,
            reaction.lower_bound,
        )
        self.assertEqual(
            1000,
            reaction.upper_bound,
        )

    def test_close_stomata(self):
        model = DynamicModel(enviroment=Environment())

        model.plant.stomata_open = True
        reaction = model.model.reactions.get_by_id("CO2_tx_leaf")
        reaction.bounds = (0, 1)

        self.assertTrue(model.plant.stomata_open)

        self.assertEqual(
            0,
            reaction.lower_bound,
        )
        self.assertEqual(
            1,
            reaction.upper_bound,
        )

        model.close_stomata()

        self.assertFalse(model.plant.stomata_open)
        reaction = model.model.reactions.get_by_id("CO2_tx_leaf")

        self.assertEqual(
            -1000,
            reaction.lower_bound,
        )
        self.assertEqual(
            0,
            reaction.upper_bound,
        )

    def test_objective_value_not_zero(self):
        dyn_model = DynamicModel(enviroment=Environment())

        dyn_model.set_bounds(NITRATE, (-1000, 1000))
        dyn_model.set_bounds(CO2, (-1000, 1000))
        dyn_model.set_bounds(STARCH_OUT, (-1000, 1000))

        # set in calc_growth_rate
        dyn_model.set_bounds(STARCH_IN, (-1000, 1000))
        dyn_model.set_bounds(WATER, (-1000, 1000))
        dyn_model.set_bounds(PHOTON, (-1000, 1000))

        ideal_objective_value = dyn_model.model.optimize().objective_value
        self.assertAlmostEqual(1000, ideal_objective_value, places=3)

    def test_update_constraints(self):
        env = Environment()
        dyn_model = DynamicModel(enviroment=env)
        growth_percent = GrowthPercent(
            leaf=0.5,
            stem=0,
            root=0.5,
            starch=0,
            flower=0,
            time_frame=10,
        )

        leaf_old = dyn_model.plant.leafs_biomass_gram
        root_old = dyn_model.plant.root_biomass_gram

        dyn_model.calc_growth_rate(growth_percent, environment=env)

        leaf_new = dyn_model.plant.leafs_biomass_gram
        root_new = dyn_model.plant.root_biomass_gram

        self.assertAlmostEqual(
            leaf_new - leaf_old, root_new - root_old, places=10
        )

        # Case 2
        dyn_model.plant.root_biomass = 1000000
        dyn_model.plant.stem_biomass = 1000000
        dyn_model.plant.leafs_biomass = 1000000
        dyn_model.plant.seed_biomass = 1000000

        dyn_model.plant.update_max_water_pool()
        dyn_model.plant.update_max_starch_pool()
        dyn_model.plant.update_max_nitrate_pool()
        dyn_model.open_stomata()

        dyn_model.plant.starch_pool.available_starch_pool = (
            dyn_model.plant.starch_pool.max_starch_pool
        )
        dyn_model.plant.water.water_pool = dyn_model.plant.water.max_water_pool
        dyn_model.plant.nitrate.nitrate_pool = (
            dyn_model.plant.nitrate.max_nitrate_pool
        )

        leaf_old = dyn_model.plant.leafs_biomass_gram
        stem_old = dyn_model.plant.stem_biomass_gram
        root_old = dyn_model.plant.root_biomass_gram
        seed_old = dyn_model.plant.seed_biomass_gram

        growth_percent = GrowthPercent(
            leaf=0.25,
            stem=0.25,
            root=0.25,
            starch=0.25,
            flower=0,
            time_frame=10,
        )
        dyn_model.calc_growth_rate(
            new_growth_percentages=growth_percent, environment=env
        )

        leaf_new = dyn_model.plant.leafs_biomass_gram
        stem_new = dyn_model.plant.stem_biomass_gram
        root_new = dyn_model.plant.root_biomass_gram
        seed_new = dyn_model.plant.seed_biomass_gram

        leaf_diff = leaf_new - leaf_old
        stem_diff = stem_new - stem_old
        root_diff = root_new - root_old
        seed_diff = seed_new - seed_old
        starch = dyn_model.plant.starch_pool.starch_production_in_gram

        msg = (
            f"Growth of leaf ({leaf_diff}), "
            f"stem ({stem_diff}), "
            f"root ({root_diff}) "
            f"and starch ({starch}) is unequal"
        )

        self.assertEqual(0, seed_diff)
        self.assertAlmostEqual(leaf_diff, stem_diff, msg=msg)
        self.assertAlmostEqual(stem_diff, root_diff, msg=msg)
        self.assertAlmostEqual(root_diff, starch, msg=msg)

    @skip(
        "Should be replaced by shorter methods."
        " This requires splitting 'calc_growth_rate' from dynamic_model."
    )
    def test_photosynthesis(self):
        env = Environment()
        dyn_model = DynamicModel(enviroment=env)
        dyn_model.seconds_passed = 3600 * 12  # 12:00

        dyn_model.plant.leafs.new_leaf(Leaf(mass=0, max_mass=5000))

        dyn_model.plant.root_biomass = 100
        dyn_model.plant.stem_biomass = 100
        dyn_model.plant.leafs_biomass = 100
        dyn_model.plant.seed_biomass = 100

        # Case 1
        dyn_model.plant.update_max_water_pool()
        dyn_model.plant.update_max_starch_pool()
        dyn_model.plant.update_max_nitrate_pool()
        dyn_model.open_stomata()

        dyn_model.plant.starch_pool.available_starch_pool = 0
        dyn_model.plant.water.water_pool = dyn_model.plant.water.max_water_pool
        dyn_model.plant.nitrate.nitrate_pool = (
            dyn_model.plant.nitrate.max_nitrate_pool
        )

        leaf_old = dyn_model.plant.leafs_biomass_gram
        stem_old = dyn_model.plant.stem_biomass_gram
        root_old = dyn_model.plant.root_biomass_gram
        seed_old = dyn_model.plant.seed_biomass_gram

        growth_percent = GrowthPercent(
            leaf=0.25,
            stem=0.25,
            root=0.25,
            starch=0.25,
            flower=0,
            time_frame=1,
        )
        dyn_model.calc_growth_rate(
            new_growth_percentages=growth_percent, environment=env
        )

        leaf_new = dyn_model.plant.leafs_biomass_gram
        stem_new = dyn_model.plant.stem_biomass_gram
        root_new = dyn_model.plant.root_biomass_gram
        seed_new = dyn_model.plant.seed_biomass_gram

        leaf_diff = leaf_new - leaf_old
        stem_diff = stem_new - stem_old
        root_diff = root_new - root_old
        seed_diff = seed_new - seed_old
        starch = dyn_model.plant.starch_pool.starch_production_in_gram

        msg = (
            f"Growth of leaf ({leaf_diff}), "
            f"stem ({stem_diff}), "
            f"root ({root_diff}) "
            f"and starch ({starch}) is unequal"
        )

        self.assertEqual(0, seed_diff)
        self.assertAlmostEqual(leaf_diff, stem_diff, msg=msg)
        self.assertAlmostEqual(stem_diff, root_diff, msg=msg)
        self.assertAlmostEqual(root_diff, starch, msg=msg)

        # Case 2
        # increase leaf mass => higher photon limit
        dyn_model.plant.leafs_biomass = 500

        growth_percent = GrowthPercent(
            leaf=0,
            stem=0,
            root=0,
            starch=1,
            flower=0,
            time_frame=3600,
        )
        dyn_model.plant.starch_pool.available_starch_pool = 0

        dyn_model.calc_growth_rate(
            new_growth_percentages=growth_percent, environment=env
        )

        growth_rate = dyn_model.growth_rates

        self.assertEqual(0, growth_rate.leaf_rate)
        self.assertEqual(0, growth_rate.stem_rate)
        self.assertEqual(0, growth_rate.root_rate)
        self.assertEqual(0, growth_rate.seed_rate)

        self.assertTrue(dyn_model._objective_value > 0)
        self.assertTrue(
            dyn_model.plant.starch_pool.starch_production_in_gram > 0
        )
        self.assertTrue(dyn_model.plant.co2 > 0)
        self.assertTrue(dyn_model.plant.photon > 0)
