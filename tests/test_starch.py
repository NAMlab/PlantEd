import logging
from unittest import TestCase
from unittest.mock import patch

from PlantEd.constants import START_STARCH_POOL_IN_MICROMOL, GRAM_STARCH_PER_GRAM_FRESH_WEIGHT, \
    MICROMOL_STARCH_PER_GRAM_STARCH, GRAM_STARCH_PER_MICROMOL_STARCH, GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT
from PlantEd.exceptions.pools import NegativePoolError
from PlantEd.server.plant.starch import (
    Starch,
)

logging.basicConfig(level=logging.DEBUG)

class TestStarch(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def test_create(self):
        starch: Starch = Starch(plant_weight_gram= 6)
        self.assertIsInstance(starch, Starch)

        self.assertIsInstance(starch.starch_out, float)
        self.assertEqual(starch.starch_out, 0)

        self.assertIsInstance(starch.starch_in, float)
        self.assertEqual(starch.starch_in, 0)

        self.assertIsInstance(starch.allowed_starch_pool_consumption, float)
        self.assertEqual(starch.allowed_starch_pool_consumption, 1.0)

    @patch('PlantEd.server.plant.starch.START_STARCH_POOL_IN_MICROMOL', 2500)
    def test_available_starch_pool(self):
        starch: Starch = Starch(plant_weight_gram= 6)
        print(starch.available_starch_pool)

        init_value = 2500

        self.assertEqual(starch.available_starch_pool, init_value)

        # increase pool while init state already exceeds pool limit
        # => no change to pool

        starch.available_starch_pool = 30000
        self.assertEqual(starch.available_starch_pool, init_value)

        # reduce pool while exceeding pool limit
        starch.available_starch_pool = 2400
        self.assertEqual(2400, starch.available_starch_pool)

        # go under max value
        starch.scale_pool_via_biomass(20)  # 925.1230105229657
        starch.available_starch_pool = 100

        self.assertEqual(starch.available_starch_pool, 100)

        # increase over max value
        starch.available_starch_pool = starch.max_starch_pool * 2

        self.assertEqual(starch.available_starch_pool, starch.max_starch_pool)

        starch.available_starch_pool = 90
        self.assertEqual(starch.available_starch_pool, 90)
        starch.available_starch_pool = 60
        self.assertEqual(starch.available_starch_pool, 60)
        starch.available_starch_pool = 0
        self.assertEqual(starch.available_starch_pool, 0)

        with self.assertRaises(NegativePoolError):
            starch.available_starch_pool = -5

    @patch('PlantEd.server.plant.starch.START_STARCH_POOL_IN_MICROMOL', 2500)
    def test_available_starch_pool_gram(self):
        starch: Starch = Starch(plant_weight_gram= 6)

        init_value = 2500 * GRAM_STARCH_PER_MICROMOL_STARCH
        # 24669.946947279088
        self.assertEqual(init_value, starch.available_starch_pool_gram)

        # increase pool while init state already exceeds pool limit
        # => no change to pool

        starch.available_starch_pool = 30000
        self.assertEqual(starch.available_starch_pool_gram, init_value)

        # reduce pool while exceeding pool limit
        starch.available_starch_pool = 2400
        print()
        self.assertEqual(starch.available_starch_pool_gram, 0.38913744)

        # go under max value
        starch.scale_pool_via_biomass(20)  # 123.34973473639545
        starch.available_starch_pool = 100

        self.assertEqual(
            starch.available_starch_pool_gram,
            100 * GRAM_STARCH_PER_MICROMOL_STARCH,
        )

        # increase over max value
        starch.available_starch_pool = starch.max_starch_pool * 2
        self.assertEqual(
            starch.available_starch_pool_gram,
            starch.max_starch_pool * GRAM_STARCH_PER_MICROMOL_STARCH,
        )

        starch.available_starch_pool = 90
        self.assertEqual(
            starch.available_starch_pool_gram,
            90 * GRAM_STARCH_PER_MICROMOL_STARCH,
        )
        starch.available_starch_pool = 60
        self.assertEqual(
            starch.available_starch_pool_gram,
            60 * GRAM_STARCH_PER_MICROMOL_STARCH,
        )
        starch.available_starch_pool = 0
        self.assertEqual(starch.available_starch_pool_gram, 0)

    def test_starch_usage_in_gram(self):
        starch = Starch(plant_weight_gram= 6)

        self.assertEqual(starch.starch_usage_in_gram, 0)

        values = [5, 100, 50.67, -100, -5.97, 23, 86.4325]

        for value in values:
            starch.starch_in = value
            self.assertEqual(
                starch.starch_usage_in_gram,
                value * GRAM_STARCH_PER_MICROMOL_STARCH,
            )

    def test_starch_production_in_gram(self):
        starch = Starch(plant_weight_gram= 6)

        self.assertEqual(starch.starch_production_in_gram, 0)

        values = [3, 49, 27.997, -5, -1.786451, 99999, 48.4325]

        for value in values:
            starch.starch_out = value
            self.assertEqual(
                starch.starch_production_in_gram,
                value * GRAM_STARCH_PER_MICROMOL_STARCH,
            )

    def test_scale_pool_via_biomass(self):
        starch = Starch(plant_weight_gram= 0)

        self.assertEqual(starch.max_starch_pool, 0)

        values = [3, 49, 27.997, -5, -1.786451, 99999, 48.4325]

        for value in values:
            starch.scale_pool_via_biomass(value)
            expected_max_pool = (
                    value
                    * GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT
                    * GRAM_STARCH_PER_GRAM_FRESH_WEIGHT
                    * MICROMOL_STARCH_PER_GRAM_STARCH
            )
            self.assertEqual(starch.max_starch_pool, expected_max_pool)

    def test_calc_available_starch_in_mol_per_gram_and_time(self):
        starch = Starch(plant_weight_gram= 6)
        starch.scale_pool_via_biomass(5000)

        times = [
            -37.719,
            65.493,
            60.416,
            92,
            -36.736,
            20.851,
            34.85,
            -85.659,
            -59,
            21.13,
        ]
        organ_grams = [
            -79.961,
            26.558,
            31,
            8.261,
            -6.524,
            3.276,
            43.924,
            57.82,
            -70,
            -79.841,
        ]
        starch_pools = [
            10.849,
            64.18,
            1.68,
            7.935,
            82.355,
            21,
            24,
            48.376,
            91.219,
            86.358,
            0,
        ]

        for starch_pool in starch_pools:
            for organ_gram in organ_grams:
                for time in times:
                    starch.available_starch_pool = starch_pool

                    computed = (
                        starch.calc_available_starch_in_mol_per_gram_and_time(
                            gram_of_organ=organ_gram,
                            time_in_seconds=time,
                        )
                    )
                    expected = starch.available_starch_pool / (
                        organ_gram * time
                    )
                    expected = (
                        expected * starch.allowed_starch_pool_consumption
                    )

                    self.assertEqual(expected, computed)

        with self.assertRaises(ValueError):
            starch.calc_available_starch_in_mol_per_gram_and_time(
                gram_of_organ=5,
                time_in_seconds=0,
            )

        with self.assertRaises(ValueError):
            starch.calc_available_starch_in_mol_per_gram_and_time(
                gram_of_organ=0,
                time_in_seconds=76,
            )
