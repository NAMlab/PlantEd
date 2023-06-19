from unittest import TestCase

from PlantEd.client.water import Water, MAX_WATER_POOL_PER_GRAMM
from PlantEd.exceptions.pools import NegativeBiomassError


class TestWater(TestCase):
    def test_get_water_drain(self):
        water = Water()

        self.assertEqual(
            water.get_water_drain(), 0.05550843506179199 * 4000000
        )

        water.water_intake = 57
        water.update_max_water_pool(plant_biomass=64)

        intakes = [
            -23.45,
            -66,
            9.60,
            3,
            -97.30,
            -28.74,
            6,
            86.35,
            -1,
            47.82,
            0,
        ]
        biomasses = [
            47.46,
            79,
            31.44,
            30.53,
            52,
            6.76,
            37,
            47.67,
            50.61,
            60.41,
        ]

        for intake in intakes:
            for biomass in biomasses:
                water.water_intake = intake
                water.update_max_water_pool(plant_biomass=biomass)

                expected = intake + MAX_WATER_POOL_PER_GRAMM * biomass
                calculated = water.get_water_drain()

                self.assertEqual(expected, calculated)

    def test_fill_percentage(self):
        water = Water()
        maximum = water.max_water_pool

        self.assertEqual(water.fill_percentage, 0)
        pools = [
            93.27,
            39.77,
            59.21,
            23.59,
            86.61,
            10.02,
            3.92,
            6.83,
            27.86,
            5.03,
        ]

        for pool in pools:
            water.water_pool = pool

            expected = pool / maximum
            calculated = water.fill_percentage

            self.assertEqual(expected, calculated)

    def test_to_dict(self):
        water = Water()

        expected = {
            "water_pool": 0,
            "water_intake": 0,
            "water_intake_pool": 0,
            "transpiration": 0,
            "max_water_pool": 222033.74024716797,
            "max_water_pool_consumption": 1,
        }

        calculated = water.to_dict()

        self.assertEqual(expected, calculated)

        water.water_pool = 3
        water.water_intake = 7
        water.water_intake_pool = 57
        water.transpiration = 95
        water.update_max_water_pool(50)

        expected = {
            "water_pool": 3,
            "water_intake": 7,
            "water_intake_pool": 57,
            "transpiration": 95,
            "max_water_pool": 50 * MAX_WATER_POOL_PER_GRAMM,
            "max_water_pool_consumption": 1,
        }

        calculated = water.to_dict()

        self.assertEqual(expected, calculated)

    def test_from_dic(self):
        dic = {
            "water_pool": 67,
            "water_intake": 17,
            "water_intake_pool": 287,
            "transpiration": 697,
            "max_water_pool": 472,
            "max_water_pool_consumption": 1,
        }
        water = Water.from_dict(dic=dic)

        self.assertEqual(67, water.water_pool)
        self.assertEqual(17, water.water_intake)
        self.assertEqual(287, water.water_intake_pool)
        self.assertEqual(697, water.transpiration)
        self.assertEqual(472, water.max_water_pool)
        self.assertEqual(1, water.max_water_pool_consumption)

        dic = {
            "water_pool": 297,
            "water_intake": 157,
            "water_intake_pool": 1,
            "transpiration": 0,
            "max_water_pool": 3987,
            "max_water_pool_consumption": 1,
        }
        water = Water.from_dict(dic=dic)

        self.assertEqual(297, water.water_pool)
        self.assertEqual(157, water.water_intake)
        self.assertEqual(1, water.water_intake_pool)
        self.assertEqual(0, water.transpiration)
        self.assertEqual(3987, water.max_water_pool)
        self.assertEqual(1, water.max_water_pool_consumption)

    def test_to_json(self):
        water = Water()

        expected = '{"water_pool": 0, "water_intake": 0, "water_intake_pool": 0, "transpiration": 0, "max_water_pool": 222033.74024716797, "max_water_pool_consumption": 1}'

        calculated = water.to_json()

        self.assertEqual(expected, calculated)

        water.water_pool = 3
        water.water_intake = 7
        water.water_intake_pool = 57
        water.transpiration = 95
        water.update_max_water_pool(50)

        expected = '{"water_pool": 3, "water_intake": 7, "water_intake_pool": 57, "transpiration": 95, "max_water_pool": 2775421.7530896, "max_water_pool_consumption": 1}'

        calculated = water.to_json()

        self.assertEqual(expected, calculated)

    def test_from_json(self):
        string = '{"water_pool": 5, "water_intake": 47, "water_intake_pool": 238, "transpiration": 47, "max_water_pool": 348, "max_water_pool_consumption": 1}'
        water = Water.from_json(string= string)

        self.assertEqual(5, water.water_pool)
        self.assertEqual(47, water.water_intake)
        self.assertEqual(238, water.water_intake_pool)
        self.assertEqual(47, water.transpiration)
        self.assertEqual(348, water.max_water_pool)
        self.assertEqual(1, water.max_water_pool_consumption)

        string = '{"water_pool": 37, "water_intake": 147, "water_intake_pool": 7, "transpiration": 64, "max_water_pool": 297, "max_water_pool_consumption": 1}'
        water = Water.from_json(string= string)

        self.assertEqual(37, water.water_pool)
        self.assertEqual(147, water.water_intake)
        self.assertEqual(7, water.water_intake_pool)
        self.assertEqual(64, water.transpiration)
        self.assertEqual(297, water.max_water_pool)
        self.assertEqual(1, water.max_water_pool_consumption)


    def test_update_max_water_pool(self):
        water = Water()

        with self.assertRaises(NegativeBiomassError):
            water.update_max_water_pool(-6)

        biomasses = [
            85.07,
            44.82,
            49.13,
            71.72,
            56.60,
            34.98,
            7.74,
            53.93,
            51.53,
            91.43,
        ]

        for biomass in biomasses:
            expected = MAX_WATER_POOL_PER_GRAMM * biomass

            water.update_max_water_pool(plant_biomass=biomass)
            calculated = water.max_water_pool

            self.assertEqual(expected, calculated)
