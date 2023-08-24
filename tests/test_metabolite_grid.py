import logging
import random
import sys
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
                    9.99942803e02,
                    5.71973997e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99957068e02,
                    4.29317944e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99942133e02,
                    5.78669392e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99979370e02,
                    2.06304330e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99918587e02,
                    8.14134573e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99917559e02,
                    8.24412461e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99934587e02,
                    6.54126006e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99983961e02,
                    1.60389786e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99947881e02,
                    5.21190029e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99967190e02,
                    3.28100584e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99974975e02,
                    2.50246673e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99904623e02,
                    9.53769726e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99900245e02,
                    9.97553550e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99995540e02,
                    4.46009388e-03,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99913898e02,
                    8.61021198e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99939621e02,
                    6.03793802e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99961801e02,
                    3.81987592e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99971610e02,
                    2.83901836e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99932436e02,
                    6.75639812e-02,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                    0.00000000e00,
                ],
                [
                    9.99954271e02,
                    4.57287982e-02,
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
                    9.77635356e02,
                    2.21063790e01,
                    2.49458531e-01,
                    1.25148241e-02,
                    3.34851010e-03,
                    6.78925629e-03,
                ],
                [
                    9.81058108e02,
                    1.88385181e01,
                    1.14492120e-01,
                    5.81297593e-03,
                    1.09172869e-02,
                    0.00000000e00,
                ],
                [
                    9.79738511e02,
                    2.00501972e01,
                    2.01530924e-01,
                    7.44289737e-03,
                    3.11222935e-03,
                    4.40364110e-03,
                ],
                [
                    9.81491244e02,
                    1.83808130e01,
                    1.34528595e-01,
                    4.43124120e-03,
                    9.93671518e-03,
                    2.21746671e-03,
                ],
                [
                    9.88917786e02,
                    1.09911200e01,
                    9.02648942e-02,
                    6.00487917e-04,
                    8.72593062e-03,
                    7.28570691e-03,
                ],
                [
                    9.86638556e02,
                    1.32220212e01,
                    1.32731317e-01,
                    3.37984502e-03,
                    1.45836506e-02,
                    1.57370274e-03,
                ],
                [
                    9.82102070e02,
                    1.77168818e01,
                    1.75920325e-01,
                    5.34031653e-03,
                    4.18596829e-03,
                    3.82049275e-03,
                ],
                [
                    9.80945138e02,
                    1.89190808e01,
                    1.36000655e-01,
                    8.22708317e-03,
                    1.96558395e-03,
                    5.12675249e-03,
                ],
                [
                    9.86895755e02,
                    1.29559465e01,
                    1.45706380e-01,
                    3.11152385e-03,
                    1.19487466e-02,
                    7.09623760e-04,
                ],
                [
                    9.88392409e02,
                    1.15109020e01,
                    1.00751953e-01,
                    2.63471623e-03,
                    3.13318643e-03,
                    1.20394936e-03,
                ],
                [
                    9.82086991e02,
                    1.77719137e01,
                    1.42068718e-01,
                    4.38594016e-03,
                    7.50589168e-03,
                    3.48682492e-03,
                ],
                [
                    9.80659272e02,
                    1.92199989e01,
                    1.17667146e-01,
                    2.18738749e-03,
                    7.76100045e-03,
                    2.47482110e-03,
                ],
                [
                    9.77232288e02,
                    2.25998551e01,
                    1.62629021e-01,
                    8.70540419e-03,
                    2.06660312e-03,
                    1.42653022e-02,
                ],
                [
                    9.83405601e02,
                    1.64520415e01,
                    1.31633122e-01,
                    1.17058037e-02,
                    9.44724222e-04,
                    1.73462964e-02,
                ],
                [
                    9.83275427e02,
                    1.65272322e01,
                    1.99721507e-01,
                    7.23857653e-03,
                    9.93739756e-04,
                    3.04751849e-03,
                ],
                [
                    9.85721713e02,
                    1.42133355e01,
                    6.27383906e-02,
                    1.06649414e-02,
                    8.46018712e-03,
                    1.27528470e-03,
                ],
                [
                    9.80715577e02,
                    1.91851713e01,
                    9.77566250e-02,
                    9.48177651e-03,
                    3.25940706e-03,
                    7.28545195e-03,
                ],
                [
                    9.81288611e02,
                    1.85512469e01,
                    1.53703236e-01,
                    3.73193825e-03,
                    1.50009004e-02,
                    2.30874700e-03,
                ],
                [
                    9.81399196e02,
                    1.84511463e01,
                    1.51270788e-01,
                    1.10653656e-03,
                    9.85619832e-03,
                    6.89362621e-05,
                ],
                [
                    9.81655462e02,
                    1.82002820e01,
                    1.37173003e-01,
                    2.99358607e-03,
                    6.45956388e-03,
                    7.11907909e-03,
                ],
            ]
        )

        assert_almost_equal(met.grid, expected, decimal=1)

    def test_available_absolute(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate= 500,
            x = 4,
            y = 3,
        )

        grid.add2cell(
            rate= 500,
            x = 1,
            y = 2,
        )

        root = LSystem(
            root_grid=np.ones((20,6)),
            water_grid_pos= (0,900)
            )

        self.assertEqual(grid.available_absolute(roots= root), 1000)

        root.root_grid[1,2] = 0
        self.assertEqual(grid.available_absolute(roots= root), 500)

    def test_drain(self):
        grid = MetaboliteGrid()

        grid.add2cell(
            rate= 500,
            x = 4,
            y = 3,
        )

        grid.add2cell(
            rate= 500,
            x = 1,
            y = 2,
        )

        root = LSystem(
            root_grid=np.ones((20,6)),
            water_grid_pos= (0,900)
            )

        self.assertEqual(grid.available_absolute(roots= root), 1000)

        grid.drain(amount= 500, roots= root)
        self.assertEqual(grid.available_absolute(roots= root), 500)
        self.assertEqual(grid.grid[4,3], 250)
        self.assertEqual(grid.grid[1,2], 250)

        grid.add2cell(
            rate= 1000,
            x = 10,
            y = 0,
        )

        self.assertEqual(grid.available_absolute(roots= root), 1500)
        grid.drain(amount= 300, roots= root)
        self.assertEqual(grid.available_absolute(roots= root), 1200)
        self.assertEqual(grid.grid[4,3], 150)
        self.assertEqual(grid.grid[1,2], 150)
        self.assertEqual(grid.grid[10,0], 900)

        grid.drain(amount=900, roots= root)
        self.assertEqual(grid.available_absolute(roots= root), 300)
        self.assertEqual(grid.grid[4,3], 0)
        self.assertEqual(grid.grid[1,2], 0)
        self.assertEqual(grid.grid[10,0], 300)

    def test_to_dict(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate= 500,
            x = 7,
            y = 0,
        )

        grid.add2cell(
            rate= 500,
            x = 10,
            y = 4,
        )

        dic = grid.to_dict()
        expected = {'grid_size': (20, 6), 'grid': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], 'max_metabolite_cell': 1000000}

        self.assertEqual(dic, expected)

        grid.add2cell(rate= 47, x= 4, y = 1)

        dic = grid.to_dict()
        expected = {'grid_size': (20, 6), 'grid': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 47.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], 'max_metabolite_cell': 1000000}
        
        self.assertEqual(dic, expected)


    def test_to_json(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate= 500,
            x = 7,
            y = 0,
        )

        grid.add2cell(
            rate= 500,
            x = 10,
            y = 4,
        )

        json = grid.to_json()
        expected = "{\"grid_size\": [20, 6], \"grid\": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], \"max_metabolite_cell\": 1000000}"
        self.assertEqual(json, expected)

        grid.add2cell(rate= 47, x= 4, y = 1)
        json = grid.to_json()
        expected = "{\"grid_size\": [20, 6], \"grid\": [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 47.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [500.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 500.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], \"max_metabolite_cell\": 1000000}"
        
        self.assertEqual(json, expected)

    def test_from_dict(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate= 500,
            x = 7,
            y = 0,
        )

        grid.add2cell(
            rate= 500,
            x = 10,
            y = 4,
        )

        dic = grid.to_dict()

        restored_grid = MetaboliteGrid.from_dict(dic)


        self.assertTrue(restored_grid == grid)

    def test_from_json(self):
        grid = MetaboliteGrid()
        grid.add2cell(
            rate= 500,
            x = 7,
            y = 0,
        )

        grid.add2cell(
            rate= 500,
            x = 10,
            y = 4,
        )

        json = grid.to_json()
        restored_grid = MetaboliteGrid.from_json(json)
        
        self.assertTrue(grid == restored_grid)

    def test_available_relative_mm(self):
        met = MetaboliteGrid()
        root = LSystem(root_grid=np.ones((20, 6)), water_grid_pos=(0, 900))
        met.add2cell(20, 1,1)
        met.add2cell(7, 5, 5)
        v_max = 0.038
        k_m = 4000

        mm_limit = 0.0002547802334243854

        self.assertEqual(mm_limit, met.available_relative_mm(
            roots=root,
            g_root= 1,
            time_seconds= 20,
            v_max= v_max,
            k_m=k_m,
        )
        )
        self.assertEqual(mm_limit,met.available_relative_mm(
            roots=root,
            g_root= 1,
            time_seconds= 30,
            v_max= v_max,
            k_m=k_m,
        )

        )

        self.assertEqual(27/500000, met.available_relative_mm(
                roots=root,
                g_root=1,
                time_seconds=500000,
                v_max=v_max,
                k_m=k_m,
            ))

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


