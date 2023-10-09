import logging
import random
from unittest import TestCase
import numpy as np

from numpy.testing import assert_almost_equal

from PlantEd.server.environment.grid import MetaboliteGrid
from PlantEd.utils.LSystem import LSystem

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)


class TestMetaboliteGrid(TestCase):
    def setUp(self) -> None:
        random.seed(10)

    def test_create(self):
        met = MetaboliteGrid()
        self.assertIsInstance(met, MetaboliteGrid)
        self.assertEqual(met.grid_size, (20, 6))
        self.assertEqual(met.max_metabolite_cell, 1000000)

    def test_rain_linke_increase(self):
        met = MetaboliteGrid()

        met.rain_linke_increase(
            time_in_s=100,
            rain=10,
        )
        np.set_printoptions(threshold=50000)

        expected = np.matrix(
            [
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    2.56986111,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
            ]
        )

        assert_almost_equal(met.grid, expected, decimal=4, verbose=True)

        met.rain_linke_increase(
            time_in_s=3600 * 10,
            rain=0,
        )

        expected = np.matrix(
            [
                [
                    2.50617606e00,
                    5.33568005e-02,
                    6.59864399e-03,
                    1.42518797e-02,
                    5.20670378e-04,
                    6.89729131e-03,
                ],
                [
                    2.53167703e00,
                    4.91954183e-02,
                    1.20698674e-03,
                    8.61199472e-03,
                    8.51653788e-03,
                    0.00000000e00,
                ],
                [
                    2.50226480e00,
                    5.80590653e-02,
                    4.65547621e-03,
                    6.16876834e-03,
                    5.23245445e-03,
                    2.73556767e-03,
                ],
                [
                    2.52322902e00,
                    5.48762957e-02,
                    3.36979735e-03,
                    2.05851343e-03,
                    1.12911507e-02,
                    0.00000000e00,
                ],
                [
                    2.53237332e00,
                    3.21934376e-02,
                    5.62603868e-03,
                    2.18241550e-03,
                    6.47801739e-03,
                    6.29427282e-03,
                ],
                [
                    2.52006955e00,
                    3.85874796e-02,
                    5.98389883e-03,
                    3.05174994e-03,
                    1.20762071e-02,
                    3.21434999e-03,
                ],
                [
                    2.51865426e00,
                    4.65145366e-02,
                    4.85515068e-03,
                    1.10288373e-02,
                    3.46177167e-03,
                    4.68287310e-03,
                ],
                [
                    2.52588798e00,
                    4.23945239e-02,
                    3.75684889e-03,
                    6.06450115e-03,
                    2.18714426e-03,
                    2.30441801e-03,
                ],
                [
                    2.53341436e00,
                    2.99958443e-02,
                    7.26415145e-03,
                    1.79615879e-03,
                    8.80488288e-03,
                    6.95884861e-04,
                ],
                [
                    2.54223003e00,
                    2.81247660e-02,
                    4.51206584e-03,
                    4.74210449e-03,
                    4.29118803e-03,
                    1.40862009e-03,
                ],
                [
                    2.52364438e00,
                    4.50775529e-02,
                    3.97575931e-03,
                    3.42941037e-03,
                    7.18606304e-03,
                    3.22473200e-03,
                ],
                [
                    2.51024797e00,
                    5.47388593e-02,
                    4.12428119e-03,
                    2.86989994e-03,
                    6.37566207e-03,
                    7.85252060e-04,
                ],
                [
                    2.49961508e00,
                    6.67126036e-02,
                    1.27351740e-03,
                    8.81153458e-03,
                    1.66085831e-04,
                    9.96165628e-03,
                ],
                [
                    2.52713576e00,
                    3.17086395e-02,
                    3.44837543e-03,
                    1.05243484e-02,
                    1.07745052e-03,
                    1.38462341e-02,
                ],
                [
                    2.51642022e00,
                    4.66887296e-02,
                    8.58610323e-03,
                    7.26177547e-03,
                    2.05362355e-03,
                    1.38664704e-03,
                ],
                [
                    2.52957511e00,
                    4.58544188e-02,
                    1.75271196e-03,
                    1.68014334e-02,
                    7.98861115e-03,
                    0.00000000e00,
                ],
                [
                    2.51966274e00,
                    5.06389329e-02,
                    2.09560646e-03,
                    1.44268469e-02,
                    3.42524658e-04,
                    3.09938448e-03,
                ],
                [
                    2.52022430e00,
                    4.01069915e-02,
                    6.88472383e-03,
                    1.03083939e-03,
                    1.20369064e-02,
                    2.49420570e-03,
                ],
                [
                    2.51306964e00,
                    5.51186002e-02,
                    4.65883652e-03,
                    4.60224556e-03,
                    8.45059348e-03,
                    0.00000000e00,
                ],
                [
                    2.51927610e00,
                    4.38369531e-02,
                    2.46375495e-03,
                    3.27733508e-03,
                    4.63834852e-03,
                    6.62710855e-03,
                ],
            ]
        )

        assert_almost_equal(met.grid, expected, decimal=1)

    def test_available_absolute(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate=500,
            x=4,
            y=3,
        )

        grid.add2cell(
            rate=500,
            x=1,
            y=2,
        )

        root = LSystem(root_grid=np.ones((20, 6)), water_grid_pos=(0, 900))

        self.assertEqual(grid.available_absolute(roots=root), 1000)

        root.root_grid[1, 2] = 0
        self.assertEqual(grid.available_absolute(roots=root), 500)

    def test_drain(self):
        grid = MetaboliteGrid()

        grid.add2cell(
            rate=500,
            x=4,
            y=3,
        )

        grid.add2cell(
            rate=500,
            x=1,
            y=2,
        )

        root = LSystem(root_grid=np.ones((20, 6)), water_grid_pos=(0, 900))

        self.assertEqual(grid.available_absolute(roots=root), 1000)

        grid.drain(amount=500, roots=root)
        self.assertEqual(grid.available_absolute(roots=root), 500)
        self.assertEqual(grid.grid[4, 3], 250)
        self.assertEqual(grid.grid[1, 2], 250)

        grid.add2cell(
            rate=1000,
            x=10,
            y=0,
        )

        self.assertEqual(grid.available_absolute(roots=root), 1500)
        grid.drain(amount=300, roots=root)
        self.assertEqual(grid.available_absolute(roots=root), 1200)
        self.assertEqual(grid.grid[4, 3], 150)
        self.assertEqual(grid.grid[1, 2], 150)
        self.assertEqual(grid.grid[10, 0], 900)

        grid.drain(amount=900, roots=root)
        self.assertEqual(grid.available_absolute(roots=root), 300)
        self.assertEqual(grid.grid[4, 3], 0)
        self.assertEqual(grid.grid[1, 2], 0)
        self.assertEqual(grid.grid[10, 0], 300)

    def test_to_dict(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate=500,
            x=7,
            y=0,
        )

        grid.add2cell(
            rate=500,
            x=10,
            y=4,
        )

        dic = grid.to_dict()
        expected = {
            "grid_size": (20, 6),
            "grid": [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [500.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 500.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ],
            "max_metabolite_cell": 1000000,
        }

        self.assertEqual(dic, expected)

        grid.add2cell(rate=47, x=4, y=1)

        dic = grid.to_dict()
        expected = {
            "grid_size": (20, 6),
            "grid": [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 47.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [500.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 500.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ],
            "max_metabolite_cell": 1000000,
        }

        self.assertEqual(dic, expected)

    def test_to_json(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate=500,
            x=7,
            y=0,
        )

        grid.add2cell(
            rate=500,
            x=10,
            y=4,
        )

        json = grid.to_json()
        expected = '{"grid_size": [20, 6], "grid": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], "max_metabolite_cell": 1000000}'  # noqa: E501
        self.assertEqual(json, expected)

        grid.add2cell(rate=47, x=4, y=1)
        json = grid.to_json()
        expected = '{"grid_size": [20, 6], "grid": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 47.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], "max_metabolite_cell": 1000000}'  # noqa: E501

        self.assertEqual(json, expected)

    def test_from_dict(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate=500,
            x=7,
            y=0,
        )

        grid.add2cell(
            rate=500,
            x=10,
            y=4,
        )

        dic = grid.to_dict()

        restored_grid = MetaboliteGrid.from_dict(dic)

        self.assertTrue(restored_grid == grid)

    def test_from_json(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate=500,
            x=7,
            y=0,
        )

        grid.add2cell(
            rate=500,
            x=10,
            y=4,
        )

        json = grid.to_json()
        restored_grid = MetaboliteGrid.from_json(json)

        self.assertTrue(grid == restored_grid)

    def test_available_relative_mm(self):
        met = MetaboliteGrid()
        root = LSystem(root_grid=np.ones((20, 6)), water_grid_pos=(0, 900))
        met.add2cell(20, 1, 1)
        met.add2cell(7, 5, 5)
        v_max = 0.038
        k_m = 4000

        mm_limit = 0.0002547802334243854

        self.assertEqual(
            mm_limit,
            met.available_relative_mm(
                roots=root,
                g_root=1,
                time_seconds=20,
                v_max=v_max,
                k_m=k_m,
            ),
        )
        self.assertEqual(
            mm_limit,
            met.available_relative_mm(
                roots=root,
                g_root=1,
                time_seconds=30,
                v_max=v_max,
                k_m=k_m,
            ),
        )

        self.assertEqual(
            27 / 500000,
            met.available_relative_mm(
                roots=root,
                g_root=1,
                time_seconds=500000,
                v_max=v_max,
                k_m=k_m,
            ),
        )

        self.assertEqual(
            27 / (500000 * 57),
            met.available_relative_mm(
                roots=root,
                g_root=57,
                time_seconds=500000,
                v_max=v_max,
                k_m=k_m,
            ),
        )
