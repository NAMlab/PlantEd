from __future__ import annotations
import json
import logging
from operator import itemgetter
import random
import numpy as np

from PlantEd.constants import TRICKLE_AMOUNT, MAX_WATER_PER_CELL, \
    WATER_MIKROMOL_PER_GRAM, WATER_MIKROMOL_PER_LITER

# normal plant intake 83 (flux)

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
    The soil is split into a grid of cells. Each cell holds water, can be drained and filled.
    Drainers are the plant and trickle
    Fillers are rain and the watering_can

    The grid shape defines the resolution of the grid. The root_grid must be of the same shape as water_grid.
    """

    def __init__(
            self,
            grid_size: tuple[int, int] = (20, 6),
            max_metabolite_cell: int = MAX_WATER_PER_CELL,
            preset_fill_amount: int = 0,
    ):
        self.grid_size: tuple[int, int] = grid_size
        self.grid: np.ndarray = np.full(grid_size, fill_value=preset_fill_amount)

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

    def rain_like_increase(self, time_in_s: float, rain: float):
        return
        """_summary_

        weather simulates mm of precipitation per hour per m²

        Args:
            time_in_s (int): The duration of the rain in seconds.
            rain (float): Rainfall per second in micromol.
        """
        # rain in mm/h --> mikromol/second
        # 1mm --> 1liter
        # 1h --> 3600s
        # rough estimate of the game surface to be 1m²
        if rain > 0:
            # in mirkomol per second
            visual_pleasing_factor = 10
            rain_per_cell = float(((rain / 3600) * WATER_MIKROMOL_PER_LITER) / self.grid.shape[1])
            self.grid[:, 0] += int((rain_per_cell/visual_pleasing_factor) * time_in_s)

    def available_absolute(self, root_grid: np.ndarray) -> int:

        available_metabolite = np.multiply(root_grid, self.grid)
        sum = available_metabolite.sum()

        if sum < 0:
            logger.error(
                "The calculated absolute available value based on the occurrence of the metabolite in the soil and root is negative. Check the grid itself and the root.")

        return sum

    def available_relative_mm(self, time_seconds: int, g_root: float, v_max: float, k_m: float, root_grid: np.ndarray):
        """
        This method calculates the usable metabolites in [mMol] / ([gram] * [s]. Either the calculated value is limited
        by the metabolites available in the soil or by the maximum uptake per second,
        which in turn is calculated by a time-dependent Michaelis-Menten equation.

        Args:
            time_seconds:
            g_root:
            v_max:
            k_m:
            root_grid:

        Returns:
            Relative availability of the Metabolite. The unit is [mMol] / ([gram] * [s]).
        """
        if any(x < 0 for x in [time_seconds, g_root, v_max, k_m]):
            logger.error(
                f"One of the parameters is contrary to expectations, negative. Parameters: {time_seconds} s, {g_root} g, {v_max} mMol/(g*s), k_m mMol, ")

        amount_absolute = self.available_absolute(root_grid=root_grid)
        max_uptake_per_second = amount_absolute / (time_seconds * g_root)  # based on availability

        theoretical_uptake_per_second = (v_max * amount_absolute) / (k_m + amount_absolute)  # based on MM

        logger.info(
            f"Calculated max uptake based on the soil as {max_uptake_per_second} and based on the Michaelis-Menten equation is {theoretical_uptake_per_second} ")

        return min(max_uptake_per_second, theoretical_uptake_per_second)

    def drain(self, amount: float, root_grid: np.ndarray):
        if amount <= 0:
            return

        available_water_grid = np.multiply(root_grid, self.grid)

        n_cells2drain_from = (available_water_grid > 0).sum()

        average_cell_drain = amount / n_cells2drain_from if n_cells2drain_from != 0 else 0

        # iterates over all cells ordered by key
        # => here from the cell with the lowest concentration to the highest concentration
        for (x, y), value in sorted(np.ndenumerate(available_water_grid), key=itemgetter(1), reverse=False):
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
            x (int): pos_x of cell
            y (int): pos_y of cell
        """

        self.grid[x, y] = min(self.grid[x, y] + rate, self.max_metabolite_cell)

    def trickle(self, dt):
        """
        Simulate the transpiration of water in the soil.
        Over time water travels from the upper rows to the base.
        Drain starts at the bottom row. Water from above get reduced and added
        below.
        The more water there is, the faster it trickles. Randomness makes it look less uniform.

        Depending on gamespeed and TRICKLE_AMOUNT
        """

        for x in range(0, self.grid.shape[0]):
            for y in reversed(range(0, self.grid.shape[1])):
                upper_cell_content = self.grid[x, y - 1]
                if upper_cell_content > 0:
                    take_from_upper_cell = (TRICKLE_AMOUNT * upper_cell_content * dt)
                    # check if zero in upper cell
                    delta_trickle = upper_cell_content - take_from_upper_cell
                    if delta_trickle <= 0:
                        self.grid[x, y - 1] = 0
                        take_from_upper_cell = take_from_upper_cell - abs(delta_trickle)
                    else:
                        self.grid[x, y - 1] -= take_from_upper_cell
                    self.grid[x, y] = min(MAX_WATER_PER_CELL, take_from_upper_cell + self.grid[x, y])
        self.grid[:,5] = 0

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

        met_grid.grid_size = tuple(dic["grid_size"])
        met_grid.grid = np.asarray(dic["grid"])
        met_grid.max_metabolite_cell = dic["max_metabolite_cell"]

        return met_grid

    @classmethod
    def from_json(cls, string: str) -> MetaboliteGrid:
        dic = json.loads(string)

        return MetaboliteGrid.from_dict(dic=dic)
