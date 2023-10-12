import logging
from unittest import TestCase
from unittest.mock import patch, MagicMock, call

from PlantEd.client.water import Water
from PlantEd.server.plant.leaf import Leafs, Leaf
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.plant import Plant
from PlantEd.server.plant.starch import Starch
from PlantEd.utils.LSystem import DictToRoot

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)


class TestPlant(TestCase):
    def test_create(self):
        plant = Plant(ground_grid_resolution=(20, 6))
        self.assertIsInstance(plant, Plant)

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

        self.assertEqual(plant, new_plant)

    def test_to_dict(self):
        plant = Plant(ground_grid_resolution=(20, 6))
        plant.leafs_biomass = 3.4
        plant.stem_biomass = 2
        plant.root_biomass = 1
        plant.seed_biomass = 1.5

        self.assertEqual(plant, Plant.from_dict(plant.to_dict()))

    def test_from_dict(self):
        water_dict = {
            "water_pool": 1.0,
            "water_intake": 2,
            "water_intake_pool": 5,
            "transpiration": 60,
            "max_water_pool": 300,
        }

        nitrate_dict = {
            "nitrate_pool": 60,
            "nitrate_intake": 3,
            "max_nitrate_pool": 120,
        }

        starch_dict = {
            "max_starch_pool": 50,
            "starch_out": 6.0,
            "starch_in": 3.0,
            "allowed_starch_pool_consumption": 0.5,
            "available_starch_pool": 200,
        }

        leaf_dict = {
            "addable_leaf_biomass": 3.0,
            "biomass": 2.1,
            "leafs": [
                {"id": 1, "mass": 0.1, "max_mass": 0.1},
                {"id": 2, "mass": 2.3, "max_mass": 5.3},
            ],
        }

        root_dict = {
            "root_grid": {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
                18: 0.0,
                19: 0.0,
                20: 0.0,
                21: 0.0,
                22: 0.0,
                23: 0.0,
                24: 0.0,
                25: 0.0,
                26: 0.0,
                27: 0.0,
                28: 0.0,
                29: 0.0,
                30: 0.0,
                31: 0.0,
                32: 0.0,
                33: 0.0,
                34: 0.0,
                35: 0.0,
                36: 0.0,
                37: 0.0,
                38: 0.0,
                39: 0.0,
                40: 0.0,
                41: 0.0,
                42: 0.0,
                43: 0.0,
                44: 0.0,
                45: 0.0,
                46: 0.0,
                47: 0.0,
                48: 0.0,
                49: 0.0,
                50: 0.0,
                51: 0.0,
                52: 0.0,
                53: 0.0,
                54: 0.0,
                55: 0.0,
                56: 0.0,
                57: 0.0,
                58: 0.0,
                59: 0.0,
                60: 0.0,
                61: 0.0,
                62: 0.0,
                63: 0.0,
                64: 0.0,
                65: 0.0,
                66: 0.0,
                67: 0.0,
                68: 0.0,
                69: 0.0,
                70: 0.0,
                71: 0.0,
                72: 0.0,
                73: 0.0,
                74: 0.0,
                75: 0.0,
                76: 0.0,
                77: 0.0,
                78: 0.0,
                79: 0.0,
                80: 0.0,
                81: 0.0,
                82: 0.0,
                83: 0.0,
                84: 0.0,
                85: 0.0,
                86: 0.0,
                87: 0.0,
                88: 0.0,
                89: 0.0,
                90: 0.0,
                91: 0.0,
                92: 0.0,
                93: 0.0,
                94: 0.0,
                95: 0.0,
                96: 0.0,
                97: 0.0,
                98: 0.0,
                99: 0.0,
                100: 0.0,
                101: 0.0,
                102: 0.0,
                103: 0.0,
                104: 0.0,
                105: 0.0,
                106: 0.0,
                107: 0.0,
                108: 0.0,
                109: 0.0,
                110: 0.0,
                111: 0.0,
                112: 0.0,
                113: 0.0,
                114: 0.0,
                115: 0.0,
                116: 0.0,
                117: 0.0,
                118: 0.0,
                119: 0.0,
                120: 0.0,
            },
            "water_grid_pos": (0, 900),
            "positions": [],
            "directions": [],
            "root_classes": [
                [
                    {
                        "max_length": 150,
                        "duration": 4,
                        "tries": 5,
                        "max_branches": 5,
                    },
                    {
                        "max_length": 100,
                        "duration": 2,
                        "tries": 4,
                        "max_branches": 5,
                    },
                    {
                        "max_length": 30,
                        "duration": 1,
                        "tries": 1,
                        "max_branches": 0,
                    },
                ],
                [
                    {
                        "max_length": 600,
                        "duration": 5,
                        "tries": 5,
                        "max_branches": 5,
                    },
                    {
                        "max_length": 250,
                        "duration": 3,
                        "tries": 4,
                        "max_branches": 3,
                    },
                    {
                        "max_length": 50,
                        "duration": 2,
                        "tries": 1,
                        "max_branches": 0,
                    },
                ],
                [
                    {
                        "max_length": 800,
                        "duration": 6,
                        "tries": 6,
                        "max_branches": 3,
                    },
                    {
                        "max_length": 450,
                        "duration": 4,
                        "tries": 5,
                        "max_branches": 2,
                    },
                    {
                        "max_length": 90,
                        "duration": 2,
                        "tries": 1,
                        "max_branches": 0,
                    },
                ],
            ],
            "first_letters": [],
        }

        dic: dict = {
            "stem_biomass": 0.6,
            "root_biomass": 0.7,
            "seed_biomass": 1,
            "co2": 8,
            "photon": 100,
            "stomata_open": True,
            "water": water_dict,
            "nitrate": nitrate_dict,
            "starch": starch_dict,
            "leafs": leaf_dict,
            "root": root_dict,
        }

        plant: Plant = Plant.from_dict(dic=dic)

        self.assertEqual(0.6, plant.stem_biomass)
        self.assertEqual(0.7, plant.root_biomass)
        self.assertEqual(1, plant.seed_biomass)
        self.assertEqual(8, plant.co2)
        self.assertEqual(100, plant.photon)
        self.assertTrue(plant.stomata_open)

        water = Water.from_dict(water_dict)
        nitrate = Nitrate.from_dict(nitrate_dict)
        starch = Starch.from_dict(starch_dict)
        leafs = Leafs.from_dict(leaf_dict)
        root = DictToRoot.load_root_system(root_dict)

        self.assertEqual(water, plant.water)
        self.assertEqual(nitrate, plant.nitrate)
        self.assertEqual(starch, plant.starch_pool)
        self.assertEqual(leafs, plant.leafs)
        self.assertEqual(root, plant.root)

    def test_from_json(self):
        string: str = '{"stem_biomass": 3, "root_biomass": 1, "seed_biomass": 0.005, "co2": 30, "photon": 100, "stomata_open": true, "water": {"water_pool": 15, "water_intake": 3, "water_intake_pool": 79, "transpiration": 24, "max_water_pool": 37}, "nitrate": {"nitrate_pool": 87, "nitrate_intake": 67, "max_nitrate_pool": 38}, "starch": {"max_starch_pool": 25, "starch_out": 16, "starch_in": 8, "allowed_starch_pool_consumption": 0.75, "available_starch_pool": 24}, "leafs": {"addable_leaf_biomass": 2, "biomass": 1.1, "leafs": [{"id": 1, "mass": 0.1, "max_mass": 0.1},{"id": 2, "mass": 1, "max_mass": 3}]}, "root": {"root_grid": {"1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0, "6": 0.0, "7": 0.0, "8": 0.0, "9": 0.0, "10": 0.0, "11": 0.0, "12": 0.0, "13": 0.0, "14": 0.0, "15": 0.0, "16": 0.0, "17": 0.0, "18": 0.0, "19": 0.0, "20": 0.0, "21": 0.0, "22": 0.0, "23": 0.0, "24": 0.0, "25": 0.0, "26": 0.0, "27": 0.0, "28": 0.0, "29": 0.0, "30": 0.0, "31": 0.0, "32": 0.0, "33": 0.0, "34": 0.0, "35": 0.0, "36": 0.0, "37": 0.0, "38": 0.0, "39": 0.0, "40": 0.0, "41": 0.0, "42": 0.0, "43": 0.0, "44": 0.0, "45": 0.0, "46": 0.0, "47": 0.0, "48": 0.0, "49": 0.0, "50": 0.0, "51": 0.0, "52": 0.0, "53": 0.0, "54": 0.0, "55": 0.0, "56": 0.0, "57": 0.0, "58": 0.0, "59": 0.0, "60": 0.0, "61": 0.0, "62": 0.0, "63": 0.0, "64": 0.0, "65": 0.0, "66": 0.0, "67": 0.0, "68": 0.0, "69": 0.0, "70": 0.0, "71": 0.0, "72": 0.0, "73": 0.0, "74": 0.0, "75": 0.0, "76": 0.0, "77": 0.0, "78": 0.0, "79": 0.0, "80": 0.0, "81": 0.0, "82": 0.0, "83": 0.0, "84": 0.0, "85": 0.0, "86": 0.0, "87": 0.0, "88": 0.0, "89": 0.0, "90": 0.0, "91": 0.0, "92": 0.0, "93": 0.0, "94": 0.0, "95": 0.0, "96": 0.0, "97": 0.0, "98": 0.0, "99": 0.0, "100": 0.0, "101": 0.0, "102": 0.0, "103": 0.0, "104": 0.0, "105": 0.0, "106": 0.0, "107": 0.0, "108": 0.0, "109": 0.0, "110": 0.0, "111": 0.0, "112": 0.0, "113": 0.0, "114": 0.0, "115": 0.0, "116": 0.0, "117": 0.0, "118": 0.0, "119": 0.0, "120": 0.0}, "water_grid_pos": [0, 900], "positions": [], "directions": [], "root_classes": [[{"max_length": 150, "duration": 4, "tries": 5, "max_branches": 5}, {"max_length": 100, "duration": 2, "tries": 4, "max_branches": 5}, {"max_length": 30, "duration": 1, "tries": 1, "max_branches": 0}], [{"max_length": 600, "duration": 5, "tries": 5, "max_branches": 5}, {"max_length": 250, "duration": 3, "tries": 4, "max_branches": 3}, {"max_length": 50, "duration": 2, "tries": 1, "max_branches": 0}], [{"max_length": 800, "duration": 6, "tries": 6, "max_branches": 3}, {"max_length": 450, "duration": 4, "tries": 5, "max_branches": 2}, {"max_length": 90, "duration": 2, "tries": 1, "max_branches": 0}]], "first_letters": []}}'  # noqa: E501

        plant = Plant.from_json(string=string)

        self.assertEqual(3, plant.stem_biomass)
        self.assertEqual(1, plant.root_biomass)
        self.assertEqual(0.005, plant.seed_biomass)
        self.assertEqual(30, plant.co2)
        self.assertEqual(100, plant.photon)
        self.assertTrue(plant.stomata_open)

        self.assertEqual(15, plant.water.water_pool)
        self.assertEqual(3, plant.water.water_intake)
        self.assertEqual(79, plant.water.water_intake_pool)
        self.assertEqual(24, plant.water.transpiration)
        self.assertEqual(37, plant.water.max_water_pool)

        self.assertEqual(87, plant.nitrate.nitrate_pool)
        self.assertEqual(67, plant.nitrate.nitrate_intake)
        self.assertEqual(38, plant.nitrate.max_nitrate_pool)

        self.assertEqual(25, plant.starch_pool.max_starch_pool)
        self.assertEqual(16, plant.starch_pool.starch_out)
        self.assertEqual(8, plant.starch_pool.starch_in)
        self.assertEqual(
            0.75, plant.starch_pool.allowed_starch_pool_consumption
        )
        self.assertEqual(24, plant.starch_pool.available_starch_pool)

        self.assertEqual(2, plant.leafs.addable_leaf_biomass)
        self.assertEqual(1.1, plant.leafs.biomass)
        self.assertEqual(
            {
                Leaf.from_dict({"id": 1, "mass": 0.1, "max_mass": 0.1}),
                Leaf.from_dict({"id": 2, "mass": 1, "max_mass": 3}),
            },
            plant.leafs.leafs,
        )

    def test_starch_out(self):
        plant = Plant()

        with patch.object(plant.starch_pool, "starch_out", 8):
            self.assertEqual(8, plant.starch_out)

        with patch.object(plant.starch_pool, "starch_out", 1):
            self.assertEqual(1, plant.starch_out)

    def test_starch_in(self):
        plant = Plant()

        with patch.object(plant.starch_pool, "starch_in", 23):
            self.assertEqual(23, plant.starch_in)

        with patch.object(plant.starch_pool, "starch_in", 7):
            self.assertEqual(7, plant.starch_in)

    def test_leafs_biomass(self):
        plant = Plant()

        with patch("PlantEd.server.plant.leaf.Leafs.biomass", 23):
            self.assertEqual(23, plant.leafs.biomass)
            self.assertEqual(23, plant.leafs_biomass_gram)

        with patch("PlantEd.server.plant.leaf.Leafs.biomass", 3):
            self.assertEqual(3, plant.leafs.biomass)
            self.assertEqual(3, plant.leafs_biomass_gram)

        with patch("PlantEd.server.plant.leaf.Leafs.biomass", 500):
            self.assertEqual(500, plant.leafs.biomass)
            self.assertEqual(500, plant.leafs_biomass_gram)

    @patch("PlantEd.server.plant.plant.START_STEM_BIOMASS_GRAM", 3)
    def test_stem_biomass(self):
        plant = Plant()

        self.assertEqual(3, plant.stem_biomass)
        self.assertEqual(3, plant.stem_biomass_gram)

        with patch.object(plant, "stem_biomass", 9):
            self.assertEqual(9, plant.stem_biomass)
            self.assertEqual(9, plant.stem_biomass_gram)

        with patch.object(plant, "stem_biomass", 17):
            self.assertEqual(17, plant.stem_biomass)
            self.assertEqual(17, plant.stem_biomass_gram)

    @patch("PlantEd.server.plant.plant.START_ROOT_BIOMASS_GRAM", 1)
    @patch("PlantEd.utils.LSystem.LSystem.calc_positions")
    @patch("PlantEd.utils.LSystem.LSystem.update")
    def test_root_biomass(self, update: MagicMock, calc_positions: MagicMock):
        plant = Plant()

        self.assertEqual(1, plant.root_biomass)
        self.assertEqual(1, plant.root_biomass_gram)

        update_called = update.call_count
        calc_positions_called = calc_positions.call_count

        plant.root_biomass = 5
        self.assertEqual(5, plant.root_biomass)
        self.assertEqual(5, plant.root_biomass_gram)
        update_called = update_called + 1
        self.assertEqual(update_called, update.call_count)
        self.assertEqual(call(5), update.call_args)
        calc_positions_called = calc_positions_called + 1
        self.assertEqual(calc_positions_called, calc_positions.call_count)
        self.assertEqual((), calc_positions.call_args)

        plant.root_biomass = 10
        self.assertEqual(10, plant.root_biomass)
        self.assertEqual(10, plant.root_biomass_gram)
        update_called = update_called + 1
        self.assertEqual(update_called, update.call_count)
        self.assertEqual(call(10), update.call_args)
        calc_positions_called = calc_positions_called + 1
        self.assertEqual(calc_positions_called, calc_positions.call_count)
        self.assertEqual((), calc_positions.call_args)

        plant.root_biomass = 6
        self.assertEqual(10, plant.root_biomass)
        self.assertEqual(10, plant.root_biomass_gram)
        self.assertEqual(update_called, update.call_count)
        self.assertEqual(calc_positions_called, calc_positions.call_count)

    def test_seed_biomass(self):
        plant = Plant()
        self.assertEqual(plant.seed_biomass, plant.seed_biomass_gram)

        plant.seed_biomass = 50
        self.assertEqual(plant.seed_biomass, plant.seed_biomass_gram)

    def test_biomass_total(self):
        plant = Plant()

        plant.leafs.new_leaf(Leaf(max_mass=100))
        plant.leafs_biomass = 5
        plant.stem_biomass = 4
        plant.root_biomass = 3
        plant.seed_biomass = 2

        self.assertEqual(14, plant.biomass_total)
        self.assertEqual(14, plant.biomass_total_gram)

        plant.leafs_biomass = 10
        plant.stem_biomass = 5
        plant.root_biomass = 100
        plant.seed_biomass = 50

        self.assertEqual(165, plant.biomass_total)
        self.assertEqual(165, plant.biomass_total_gram)

    @patch("PlantEd.client.water.Water.update_max_water_pool")
    def test_update_max_water_pool(self, update_max_water_pool: MagicMock):
        plant = Plant()

        self.assertEqual(1, update_max_water_pool.call_count)

        plant.update_max_water_pool()
        self.assertEqual(2, update_max_water_pool.call_count)
        self.assertEqual(
            call(plant_biomass=plant.biomass_total_gram),
            update_max_water_pool.call_args,
        )

        with patch("PlantEd.server.plant.plant.Plant.biomass_total_gram", 23):
            plant.update_max_water_pool()
            self.assertEqual(3, update_max_water_pool.call_count)
            self.assertEqual(
                call(plant_biomass=plant.biomass_total_gram),
                update_max_water_pool.call_args,
            )

        with patch("PlantEd.server.plant.plant.Plant.biomass_total_gram", 4):
            plant.update_max_water_pool()
            self.assertEqual(4, update_max_water_pool.call_count)
            self.assertEqual(
                call(plant_biomass=plant.biomass_total_gram),
                update_max_water_pool.call_args,
            )

    @patch("PlantEd.server.plant.starch.Starch.scale_pool_via_biomass")
    def test_update_max_starch_pool(self, scale_pool_via_biomass: MagicMock):
        plant = Plant()

        self.assertEqual(1, scale_pool_via_biomass.call_count)

        plant.update_max_starch_pool()
        self.assertEqual(2, scale_pool_via_biomass.call_count)
        self.assertEqual(
            call(biomass_in_gram=plant.biomass_total_gram),
            scale_pool_via_biomass.call_args,
        )

        with patch("PlantEd.server.plant.plant.Plant.biomass_total_gram", 7):
            plant.update_max_starch_pool()
            self.assertEqual(3, scale_pool_via_biomass.call_count)
            self.assertEqual(
                call(biomass_in_gram=plant.biomass_total_gram),
                scale_pool_via_biomass.call_args,
            )

        with patch(
            "PlantEd.server.plant.plant.Plant.biomass_total_gram", 1000
        ):
            plant.update_max_starch_pool()
            self.assertEqual(4, scale_pool_via_biomass.call_count)
            self.assertEqual(
                call(biomass_in_gram=plant.biomass_total_gram),
                scale_pool_via_biomass.call_args,
            )

    @patch("PlantEd.client.water.Water.update_transpiration")
    def test_update_transpiration(self, update_transpiration: MagicMock):
        plant = Plant()
        plant.update_transpiration()
        expected_call = call(
            stomata_open=plant.stomata_open,
            co2_uptake_in_micromol_per_second_and_gram=plant.co2_uptake_in_micromol_per_second_and_gram,  # noqa: E501
            transpiration_factor=plant.water.transpiration_factor,
        )

        self.assertEqual(1, update_transpiration.call_count)
        self.assertEqual(expected_call, update_transpiration.call_args)

        plant.stomata_open = True
        plant.co2_uptake_in_micromol_per_second_and_gram = 100
        plant.water.transpiration_factor = 50

        plant.update_transpiration()

        expected_call = call(
            stomata_open=plant.stomata_open,
            co2_uptake_in_micromol_per_second_and_gram=plant.co2_uptake_in_micromol_per_second_and_gram,  # noqa: E501
            transpiration_factor=plant.water.transpiration_factor,
        )

        self.assertEqual(2, update_transpiration.call_count)
        self.assertEqual(expected_call, update_transpiration.call_args)

    @patch(
        "PlantEd.server.plant.nitrate.Nitrate.update_nitrate_pool_based_on_plant_weight"  # noqa: E501
    )
    def test_update_max_nitrate_pool(
        self, update_nitrate_pool_based_on_plant_weight: MagicMock
    ):
        plant = Plant()
        self.assertEqual(
            1, update_nitrate_pool_based_on_plant_weight.call_count
        )

        plant.update_max_nitrate_pool()
        self.assertEqual(
            2, update_nitrate_pool_based_on_plant_weight.call_count
        )
        self.assertEqual(
            call(plant_weight_gram=plant.biomass_total_gram),
            update_nitrate_pool_based_on_plant_weight.call_args,
        )
