from unittest import TestCase
from unittest.mock import patch, PropertyMock

from PlantEd.constants import MAXIMUM_LEAF_BIOMASS_GRAM
from PlantEd.server.plant.leaf import Leaf, Leafs


class TestLeaf(TestCase):
    def test_create(self):
        leaf = Leaf()
        self.assertIsInstance(leaf, Leaf)
        self.assertEqual(0, leaf.mass)
        self.assertEqual(MAXIMUM_LEAF_BIOMASS_GRAM, leaf.max_mass)

        leaf = Leaf(mass=7, max_mass=18)
        self.assertIsInstance(leaf, Leaf)
        self.assertEqual(7, leaf.mass)
        self.assertEqual(18, leaf.max_mass)

        with self.assertRaises(ValueError):
            leaf = Leaf(max_mass=3, mass=10)

    def test_equal(self):
        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
            mock.return_value = 1
            leaf = Leaf(mass=6, max_mass=13)

        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
            mock.return_value = 1
            leaf_2 = Leaf(mass=7, max_mass=13)

        self.assertNotEqual(leaf, leaf_2)
        self.assertNotEqual(leaf_2, leaf)

        leaf_2.mass = 6
        self.assertEqual(leaf_2, leaf)
        self.assertEqual(leaf, leaf_2)

    def test_space_left(self):
        leaf = Leaf(mass=0, max_mass=10)
        self.assertEqual(10, leaf.space_left)

        leaf = Leaf(mass=8, max_mass=14)
        self.assertEqual(6, leaf.space_left)

    def test_to_dict(self):
        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
            mock.return_value = 6
            leaf = Leaf(mass=0, max_mass=10)

        dic = leaf.to_dict()
        expected = {"mass": 0, "max_mass": 10, "id": 6}
        self.assertEqual(expected, dic)

        leaf.mass = 7
        leaf.max_mass = 13
        dic = leaf.to_dict()
        expected = {"mass": 7, "max_mass": 13, "id": 6}
        self.assertEqual(expected, dic)

    def test_from_dict(self):
        dic = {"mass": 7, "max_mass": 13, "id": 5}
        leaf = Leaf.from_dict(dic)

        self.assertIsInstance(leaf, Leaf)
        self.assertEqual(7, leaf.mass)
        self.assertEqual(13, leaf.max_mass)
        self.assertEqual(5, leaf.id)

        dic = {"mass": 1, "max_mass": 26, "id": 8}
        leaf = Leaf.from_dict(dic)

        self.assertIsInstance(leaf, Leaf)
        self.assertEqual(1, leaf.mass)
        self.assertEqual(26, leaf.max_mass)
        self.assertEqual(8, leaf.id)

    def test_to_json(self):
        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
            mock.return_value = 9
            leaf = Leaf(mass=4, max_mass=78)
        json = leaf.to_json()
        expected = '{"id": 9, "mass": 4, "max_mass": 78}'

        self.assertEqual(expected, json)

    def test_from_json(self):
        json = '{"id": 8,"mass": 1, "max_mass": 20}'

        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
            mock.return_value = 1
            leaf = Leaf.from_json(json)

            leaf_2 = Leaf()  # id should be 9 now

        self.assertIsInstance(leaf, Leaf)
        self.assertEqual(1, leaf.mass)
        self.assertEqual(20, leaf.max_mass)
        self.assertEqual(8, leaf.id)
        self.assertEqual(9, leaf_2.id)


class TestLeafs(TestCase):
    def test_create(self):
        leafs = Leafs()

        self.assertIsInstance(leafs, Leafs)

    def test_equality(self):
        leafs = Leafs()
        leafs_2 = Leafs()

        self.assertEqual(leafs, leafs_2)

        leaf = Leaf(mass=5, max_mass=10)
        leafs.new_leaf(leaf)

        self.assertNotEqual(leafs, leafs_2)

        leafs_2.new_leaf(leaf)
        self.assertEqual(leafs, leafs_2)

        leafs_3 = Leafs()
        leaf_2 = Leaf(mass=4, max_mass=9)
        self.assertNotEqual(leafs, leafs_3)

        leafs_3.new_leaf(leaf_2)
        self.assertNotEqual(leafs, leafs_3)

        leafs_3.new_leaf(Leaf.from_dict(leaf.to_dict()))
        leafs.new_leaf(Leaf.from_dict(leaf_2.to_dict()))

        self.assertEqual(leafs, leafs_3)

    def test_leafs(self):
        leafs = Leafs()

        self.assertIsInstance(leafs.leafs, set)
        self.assertEqual(set(), leafs.leafs)

        leaf = Leaf(mass=3, max_mass=18)
        leafs.new_leaf(leaf)
        self.assertEqual({leaf}, leafs.leafs)

    def test_new_leaf(self):
        leafs = Leafs()

        self.assertEqual(0, len(leafs.leafs))

        leaf = Leaf(mass=3, max_mass=17)
        leafs.new_leaf(leaf)
        expected = set()
        expected.add(leaf)

        self.assertEqual(1, len(leafs.leafs))
        self.assertEqual(expected, leafs.leafs)

        leaf_2 = Leaf(mass=0, max_mass=50)
        leafs.new_leaf(leaf_2)
        expected.add(leaf_2)

        self.assertEqual(expected, leafs.leafs)

    def test_addable_leaf_biomass(self):
        leafs = Leafs()

        self.assertEqual(0, leafs.addable_leaf_biomass)

        leafs.new_leaf(Leaf(mass=2, max_mass=12))
        self.assertEqual(10, leafs.addable_leaf_biomass)

        leafs.new_leaf(Leaf(mass=0, max_mass=0))
        self.assertEqual(10, leafs.addable_leaf_biomass)

        leafs.new_leaf(Leaf(mass=0, max_mass=5.7))
        self.assertEqual(15.7, leafs.addable_leaf_biomass)

        leafs.biomass = leafs.biomass + 10
        self.assertAlmostEqual(5.7, leafs.addable_leaf_biomass)

    def test_specific_leaf_area_in_square_meter(self):
        leafs = Leafs()

        self.assertEqual(0, leafs.specific_leaf_area_in_square_meter)
        leafs.new_leaf(Leaf(mass=5, max_mass=10))
        self.assertEqual(0.125, leafs.specific_leaf_area_in_square_meter)

        leafs.biomass = 10
        self.assertEqual(0.25, leafs.specific_leaf_area_in_square_meter)

    def test_biomass(self):
        leafs = Leafs()
        self.assertEqual(0, leafs.biomass)
        leaf = Leaf(mass=0, max_mass=3)

        leafs.new_leaf(leaf)
        self.assertEqual(0, leafs.biomass)

        leafs.biomass = 2
        self.assertEqual(2, leafs.biomass)

        leaf_2 = Leaf(mass=3, max_mass=10)
        leafs.new_leaf(leaf_2)
        self.assertEqual(5, leafs.biomass)

        leafs.biomass = 6

        self.assertEqual(6, leafs.biomass)
        self.assertEqual(2.5, leaf.mass)
        self.assertEqual(3.5, leaf_2.mass)

        leafs.biomass = 7
        self.assertEqual(7, leafs.biomass)
        self.assertEqual(3, leaf.mass)
        self.assertEqual(4, leaf_2.mass)

        leafs.biomass = 10
        self.assertEqual(10, leafs.biomass)
        self.assertEqual(3, leaf.mass)
        self.assertEqual(7, leaf_2.mass)

        leaf_3 = Leaf(mass=4, max_mass=14)
        leafs.new_leaf(leaf_3)
        self.assertEqual(14, leafs.biomass)
        self.assertEqual(3, leaf.mass)
        self.assertEqual(7, leaf_2.mass)
        self.assertEqual(4, leaf_3.mass)

        leafs.biomass = 20
        self.assertEqual(20, leafs.biomass)
        self.assertEqual(3, leaf.mass)
        self.assertEqual(10, leaf_2.mass)
        self.assertEqual(7, leaf_3.mass)

        leafs.biomass = 25
        self.assertEqual(25, leafs.biomass)
        self.assertEqual(3, leaf.mass)
        self.assertEqual(10, leaf_2.mass)
        self.assertEqual(12, leaf_3.mass)

    @patch.object(Leaf, "_Leaf__max_id", new_callable=PropertyMock)
    def test_to_dict(self, mock):
        mock.return_value = 1
        leafs = Leafs()
        leafs.new_leaf(Leaf(mass=0, max_mass=0))
        leafs.new_leaf(Leaf(mass=0, max_mass=20))
        leafs.new_leaf(Leaf(mass=3, max_mass=10))

        dic = {
            "addable_leaf_biomass": 27,
            "biomass": 3,
            "leafs": [
                {"id": 1, "mass": 0, "max_mass": 0},
                {"id": 2, "mass": 0, "max_mass": 20},
                {"id": 3, "mass": 3, "max_mass": 10},
            ],
        }

        self.assertEqual(dic, leafs.to_dict())

    def test_from_dict(self):
        dic = {
            "addable_leaf_biomass": 37,
            "biomass": 11,
            "leafs": [
                {"id": 2, "mass": 5, "max_mass": 14},
                {"id": 4, "mass": 0, "max_mass": 7},
                {"id": 8, "mass": 6, "max_mass": 27},
            ],
        }
        leafs = Leafs.from_dict(dic)

        all_leafs = set()
        all_leafs.add(Leaf.from_dict({"id": 2, "mass": 5, "max_mass": 14}))
        all_leafs.add(Leaf.from_dict({"id": 4, "mass": 0, "max_mass": 7}))
        all_leafs.add(Leaf.from_dict({"id": 8, "mass": 6, "max_mass": 27}))

        self.assertEqual(11, leafs.biomass)
        self.assertEqual(37, leafs.addable_leaf_biomass)
        self.assertEqual(all_leafs, leafs.leafs)
