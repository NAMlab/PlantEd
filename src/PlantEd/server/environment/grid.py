from __future__ import annotations
import json
import logging
import math
from operator import itemgetter
import random

import numpy as np

from PlantEd.utils.LSystem import LSystem

# normal plant intake 83 (flux)
DRAIN_DEFAULT: float = 0.005  # *3600/240 to adjust to hourly
RAIN_RATE: int = 8
TRICKLE_AMOUNT: float = 0.001
MAX_DRAIN_CELL: int = 100
MINIMUM_CELL_AMOUNT_TO_DRAW: int = 20
MAX_DROPS_TO_DRAW: int = 20

logger = logging.getLogger(__name__)


# Coordinates for the Grid:
# -----x----->
# |
# |
# y
# |
# |
# ↓
#
# acess grid like this grid[x,y]


class MetaboliteGrid:
    """
    The soil is split into a grid of cells. Each cell holds water,
    can be drained and filled. Drainers are the plant and trickle.
    Fillers are rain and the watering_can

    The grid shape defines the resolution of the grid.
    The root_grid must be of the same shape as water_grid.
    """

    def __init__(
        self,
        grid_size: tuple[int, int] = (20, 6),
        max_metabolite_cell: int = 1000000,
        preset_fill_amount: float = 0.0,
    ):
        self.grid_size: tuple[int, int] = grid_size
        self.grid: np.ndarray = np.full(
            grid_size, fill_value=preset_fill_amount
        )

        self.max_metabolite_cell = max_metabolite_cell

    def __str__(self) -> str:
        string = str(self.grid)
        return string

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, MetaboliteGrid):
            return False

        if self.grid_size != __value.grid_size:
            return False

        if self.max_metabolite_cell != __value.max_metabolite_cell:
            return False

        if not np.array_equal(self.grid, __value.grid):
            return False
        return True

    def rain_linke_increase(self, time_in_s: int, rain: float):
        """_summary_

        weather simulates mm of precipitation per hour per m²

        Args:
            time_in_s (int): The duration of the rain in seconds.
            rain (float): Rainfall per second in micromol.
        """

        # Todo source
        # convert mm/m²/h -> millimol/s
        # water has 55.509 mmol / liter
        # 1mm = 1liter of water
        # size of cell?
        # the complete width of the screen has around one meter
        # for 20 cells, that would be 0.05m for each cell
        # all cells together will be 1m

        rain_per_cell = rain / self.grid.shape[1] * 55.509 / 3600

        if rain > 0:
            self.grid[:, 0] += rain_per_cell * time_in_s

        times = math.floor(time_in_s / 3600)
        for _ in range(times):
            self.trickle(dt=3600)

    def available_absolute(self, roots: LSystem) -> int:
        root_grid = roots.root_grid

        available_metabolite = np.multiply(root_grid, self.grid)
        sum = available_metabolite.sum()

        if sum < 0:
            logger.error(
                "The calculated absolute available value based on the "
                "occurrence of the metabolite in the soil and root is "
                "negative. Check the grid itself and the root."
            )

        logger.debug(
            f"The passed root has access to {sum} mMol of metabolites."
        )
        return sum

    def available_relative_mm(
        self,
        time_seconds: int,
        g_root: float,
        v_max: float,
        k_m: float,
        roots: LSystem,
    ):
        """
        This method calculates the usable metabolites in
        [mMol] / ([gram] * [s]. Either the calculated value is limited
        by the metabolites available in the soil or by the maximum uptake
        per second, which in turn is calculated by a time-dependent
        Michaelis-Menten equation.

        Args:
            time_seconds:
            g_root:
            v_max:
            k_m:
            roots:

        Returns:
            Relative availability of the Metabolite. The unit is
            [mMol] / ([gram] * [s]).
        """
        if any(x < 0 for x in [time_seconds, g_root, v_max, k_m]):
            logger.error(
                f"One of the parameters is contrary to expectations, negative."
                f" Parameters: {time_seconds} s, {g_root} g, "
                f"{v_max} mMol/(g*s), k_m mMol, "
            )

        amount_absolute = self.available_absolute(roots=roots)
        max_uptake_per_second = amount_absolute / (
            time_seconds * g_root
        )  # based on availability

        theoretical_uptake_per_second = (v_max * amount_absolute) / (
            k_m + amount_absolute
        )  # based on MM

        logger.info(
            f"Calculated max uptake based on the soil as"
            f" {max_uptake_per_second} and based on the Michaelis-Menten"
            f" equation is {theoretical_uptake_per_second} "
        )

        return min(max_uptake_per_second, theoretical_uptake_per_second)

    def drain(self, amount: float, roots: LSystem):
        if amount <= 0:
            return

        root_grid = roots.root_grid
        available_water_grid = np.multiply(root_grid, self.grid)

        n_cells2drain_from = (available_water_grid > 0).sum()

        average_cell_drain = (
            amount / n_cells2drain_from if n_cells2drain_from != 0 else 0
        )

        # iterates over all cells ordered by key
        # => here from the cell with the lowest concentration to the
        #    highest concentration

        for (x, y), value in sorted(
            np.ndenumerate(available_water_grid),
            key=itemgetter(1),
            reverse=False,
        ):
            if value == 0:
                continue
            if value < average_cell_drain:
                drained = self.grid[x, y]
                self.grid[x, y] = 0

                amount -= drained
                n_cells2drain_from -= 1

                average_cell_drain = amount / n_cells2drain_from

            else:
                self.grid[x, y] -= average_cell_drain

    def add2cell(self, rate: int, x: int, y: int):
        """
        Increase amount of once cell.

        Args:
            rate (int): water amount to be added in micromol
            pos (tuple[int, int]): position of the cell
        """

        self.grid[x, y] = min(self.grid[x, y] + rate, self.max_metabolite_cell)

    def trickle(self, dt):
        """
        Simulate the transpiration of water in the soil.
        Over time water travels from the upper rows to the base.
        Drain starts at the bottom row. Water from above get reduced and added
        below.
        The more water there is, the faster it trickles.
         Randomness makes it look less uniform.

        Depending on gamespeed and TRICKLE_AMOUNT
        """

        for x in range(0, self.grid.shape[0]):
            for y in reversed(range(0, self.grid.shape[1])):
                upper_cell = self.grid[x, y - 1]
                if upper_cell > 0:
                    adjusted_trickle = (
                        (TRICKLE_AMOUNT + TRICKLE_AMOUNT * upper_cell)
                        / 1000
                        * random.random()
                        * dt
                    )
                    # check if zero in upper cell
                    delta_trickle = self.grid[x, y - 1] - adjusted_trickle
                    if delta_trickle <= 0:
                        self.grid[x, y - 1] = 0
                        adjusted_trickle = adjusted_trickle - delta_trickle
                    else:
                        self.grid[x, y - 1] -= adjusted_trickle
                    self.grid[x, y] += adjusted_trickle

    def to_dict(self):
        dic = {}

        dic["grid_size"] = self.grid_size
        dic["grid"] = self.grid.tolist()
        dic["max_metabolite_cell"] = self.max_metabolite_cell

        return dic

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, dic: dict) -> MetaboliteGrid:
        met_grid = MetaboliteGrid()

        met_grid.grid_size = tuple(dic["grid_size"])  # type: ignore
        met_grid.grid = np.asarray(dic["grid"])
        met_grid.max_metabolite_cell = dic["max_metabolite_cell"]

        return met_grid

    @classmethod
    def from_json(cls, string: str) -> MetaboliteGrid:
        dic = json.loads(string)

        return MetaboliteGrid.from_dict(dic=dic)
