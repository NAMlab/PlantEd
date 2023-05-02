from unittest import TestCase

from PlantEd.exceptions.pools import NegativePoolError
from PlantEd.server.plant.starch import (
    Starch,
    micromol_starch_per_gram_starch,
    gram_starch_per_micromol_starch,
    gram_starch_per_gram_fresh_weight,
)


class TestStarch(TestCase):
    def test_create(self):
        starch: Starch = Starch()
        self.assertIsInstance(starch, Starch)

        self.assertIsInstance(starch.starch_out, float)
        self.assertEqual(starch.starch_out, 0)

        self.assertIsInstance(starch.starch_in, float)
        self.assertEqual(starch.starch_in, 0)

        self.assertIsInstance(starch.allowed_starch_pool_consumption, float)
        self.assertEqual(starch.allowed_starch_pool_consumption, 100)

    def test_available_starch_pool(self):
        starch: Starch = Starch()
        init_value = 4.0 * micromol_starch_per_gram_starch

        # 24669.946947279088
        self.assertEqual(starch.available_starch_pool, init_value)

        # increase pool while init state already exceeds pool limit
        # => no change to pool

        starch.available_starch_pool = 30000
        self.assertEqual(starch.available_starch_pool, init_value)

        # reduce pool while exceeding pool limit
        starch.available_starch_pool = 2400
        self.assertEqual(starch.available_starch_pool, 2400)

        # go under max value
        starch.scale_pool_via_biomass(20)  # 123.34973473639545
        starch.available_starch_pool = 100

        self.assertEqual(starch.available_starch_pool, 100)

        # increase over max value
        starch.available_starch_pool = 150
        self.assertEqual(starch.available_starch_pool, starch.max_starch_pool)

        starch.available_starch_pool = 90
        self.assertEqual(starch.available_starch_pool, 90)
        starch.available_starch_pool = 60
        self.assertEqual(starch.available_starch_pool, 60)
        starch.available_starch_pool = 0
        self.assertEqual(starch.available_starch_pool, 0)

        with self.assertRaises(NegativePoolError):
            starch.available_starch_pool = -5

    def test_available_starch_pool_gram(self):
        starch: Starch = Starch()
        init_value = (
            4.0
            * micromol_starch_per_gram_starch
            * gram_starch_per_micromol_starch
        )

        # 24669.946947279088
        self.assertEqual(starch.available_starch_pool_gram, init_value)

        # increase pool while init state already exceeds pool limit
        # => no change to pool

        starch.available_starch_pool = 30000
        self.assertEqual(starch.available_starch_pool_gram, init_value)

        # reduce pool while exceeding pool limit
        starch.available_starch_pool = 2400
        self.assertEqual(starch.available_starch_pool_gram, 0.38913744)

        # go under max value
        starch.scale_pool_via_biomass(20)  # 123.34973473639545
        starch.available_starch_pool = 100

        self.assertEqual(
            starch.available_starch_pool_gram,
            100 * gram_starch_per_micromol_starch,
        )

        # increase over max value
        starch.available_starch_pool = 150
        self.assertEqual(
            starch.available_starch_pool_gram,
            starch.max_starch_pool * gram_starch_per_micromol_starch,
        )

        starch.available_starch_pool = 90
        self.assertEqual(
            starch.available_starch_pool_gram,
            90 * gram_starch_per_micromol_starch,
        )
        starch.available_starch_pool = 60
        self.assertEqual(
            starch.available_starch_pool_gram,
            60 * gram_starch_per_micromol_starch,
        )
        starch.available_starch_pool = 0
        self.assertEqual(starch.available_starch_pool_gram, 0)

    def test_starch_usage_in_gram(self):
        starch = Starch()

        self.assertEqual(starch.starch_usage_in_gram, 0)

        values = [5, 100, 50.67, -100, -5.97, 23, 86.4325]

        for value in values:
            starch.starch_in = value
            self.assertEqual(
                starch.starch_usage_in_gram,
                value * gram_starch_per_micromol_starch,
            )

    def test_starch_production_in_gram(self):
        starch = Starch()

        self.assertEqual(starch.starch_production_in_gram, 0)

        values = [3, 49, 27.997, -5, -1.786451, 99999, 48.4325]

        for value in values:
            starch.starch_out = value
            self.assertEqual(
                starch.starch_production_in_gram,
                value * gram_starch_per_micromol_starch,
            )

    def test_scale_pool_via_biomass(self):
        starch = Starch()

        self.assertEqual(starch.max_starch_pool, 0)

        values = [3, 49, 27.997, -5, -1.786451, 99999, 48.4325]

        for value in values:
            starch.scale_pool_via_biomass(value)
            expected_max_pool = (
                value
                * gram_starch_per_gram_fresh_weight
                * micromol_starch_per_gram_starch
            )
            self.assertEqual(starch.max_starch_pool, expected_max_pool)

    def test_calc_available_starch_in_mol_per_gram_and_time(self):
        starch = Starch()
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
