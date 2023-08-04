import numpy as np
from numpy import ndarray
import math
import pygame

from PlantEd.client.client import Client
from PlantEd.client.water import Water
from PlantEd.utils.gametime import GameTime
import random


# normal plant intake 83 (flux)
DRAIN_DEFAULT: float = 0.005  # *3600/240 to adjust to hourly
RAIN_RATE: int = 8
TRICKLE_AMOUNT: float = 0.001
MAX_DRAIN_CELL: int = 100
MINIMUM_CELL_AMOUNT_TO_DRAW: int = 20
MAX_DROPS_TO_DRAW: int = 20

class Water_Grid:
    """
    The soil is split into a grid of cells. Each cell holds water, can be drained and filled.
    Drainers are the plant and trickle
    Fillers are rain and the watering_can

    The grid shape defines the resolution of the grid. The root_grid must be of the same shape as water_grid.
    """
    def __init__(
        self, pos: tuple[int, int] = (0, 900),
            grid_size: tuple[int, int] = (6, 20),
            max_water_cell: int = 1000000
    ):
        self.pos = pos
        self.water_grid: ndarray = np.zeros(grid_size)
        self.available_water_grid: ndarray = np.zeros(grid_size)
        self.root_grid: ndarray
        self.raining: float = 0
        self.trickle_amount = TRICKLE_AMOUNT
        self.base_waters: list[Base_water] = []
        self.max_water_cell = max_water_cell
        # offset_grid shape: ((x,y), n_drops, width, height)
        self.offset_grid: ndarray = np.random.randint(0, 90, (2, MAX_DROPS_TO_DRAW, grid_size[0], grid_size[1]))
        self.grid_screen = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.gametime = GameTime.instance()

    def update(self, dt, water: Water, client: Client):
        """
        Update trickle and drain_grid
        Depending on raining, apply water to upper row
        """
        '''if self.raining > 0:
            self.water_grid[0, :] += (
                self.raining * self.gametime.GAMESPEED * dt
            )
            # self.water_grid[0, 0] < self.max_water_cell
        self.trickle(dt)

        # self.set_max_drain_rate()
        self.drain_grid(dt, water=water, client=client)'''
        for base_water in self.base_waters:
            base_water.update(dt)

    def set_root_grid(self, root_grid: ndarray):
        """
        Set the root grid to update current root structure
        """
        self.root_grid = root_grid

    def drain_grid(self, dt, water: Water, client: Client):
        """
        Drain the water_grid based on root structure and water location.
        Tries to drain across available cells equally. After 10 iterations it stops
        to save performance.

        transpiration and water_intake of the plant set the amount to drain
        MAX_DRAIN_CELL defines the maximum drainable amount of each cell

        First it drains the plant depending on water needed.
        Then it fills the internal water pool of the plant if possible.
        If there is not enough water in the plant, it disables the water intake of the plant.
        """
        # drain water from plant
        water_neded = water.water_intake
        transpiration = water.transpiration

        # transpiration *= 10
        # if not enough water in plant_pool
        if water.water_pool - (water_neded + transpiration) < 0:
            # kill water intake
            client.stop_water_intake()
        else:
            # take water from pool and set bounds to max
            water.water_pool -= water_neded + transpiration
            client.enable_water_intake()
        # calculate new plant pool intake
        available_water_grid = np.multiply(self.root_grid, self.water_grid)
        if water.water_pool < water.max_water_pool:
            # drain needed
            delta_water_pool = water.max_water_pool - water.water_pool
            tries = 10
            while delta_water_pool > 0:
                # ensure it is not looping forever
                tries -= 1
                if tries <= 0:
                    break
                for (x, y), value in np.ndenumerate(available_water_grid):
                    if available_water_grid[x, y] > 0:
                        # drainage per cell

                        delta = MAX_DRAIN_CELL * self.gametime.GAMESPEED * dt
                        # subtract from delta_water_pool preemtively
                        delta_water_pool -= delta
                        # check if was possible, then do so
                        if self.water_grid[x, y] - delta >= 0:
                            self.water_grid[x, y] -= delta
                        else:
                            # if there is not enough to drain, add it back to amount
                            delta_water_pool += delta - self.water_grid[x, y]
                            self.water_grid[x, y] = 0

            water.water_pool = water.max_water_pool - delta_water_pool
            if water.water_pool >= water.max_water_pool:
                water.water_pool = water.max_water_pool

        client.set_water_pool(water=water)

    def pour(self, rate: int, dt: float, pos: tuple[int, int]):
        """
        Fill one cell of the upper row of the water grid with water until max_water_cell.

        Args:
            rate (int): precipitation micromol per second
            dt (float): ticks between last call
            pos (tuple[int, int]): position of watering can
        """
        if not self.water_grid[0, int(pos[0] / 100)] > self.max_water_cell:
            self.water_grid[0, int(pos[0] / 100)] += rate * dt

    def add_base_water(self, base_water):
        """
        Add a row of base_water. Mainly for show, currently no function.
        """
        self.base_waters.append(base_water)

    def activate_rain(self, precipitation: float = RAIN_RATE):
        """
        Activate raining and set the raining amount per cell

        Args:
            precipitation (float): water fill amount per m² and second
        """
        self.raining = precipitation

    def deactivate_rain(self):
        """
        Deactivate rain by setting raining to 0
        """
        self.raining = 0

    def get_shape(self):
        """
        Return the shape of the water_grid
        """
        return self.water_grid.shape

    def trickle(self, dt):
        """
        Simulate the transpiration of water in the soil.
        Over time water travels from the upper rows to the base.
        Drain starts at the bottom row. Water from above get reduced and added
        below.
        The more water there is, the faster it trickles. Randomness makes it look less uniform.

        Depending on gamespeed and TRICKLE_AMOUNT
        """
        for i in reversed(range(1, self.water_grid.shape[0])):
            for j in range(0, self.water_grid.shape[1]):
                upper_cell = self.water_grid[i - 1, j]
                if upper_cell > 0:
                    adjusted_trickle = (
                        (
                            self.trickle_amount
                            + self.trickle_amount * upper_cell / 1000
                        )
                        * self.gametime.GAMESPEED
                        * random.random()
                        * dt
                    )
                    # check if zero in upper cell
                    delta_trickle = (
                        self.water_grid[i - 1, j] - adjusted_trickle
                    )
                    if delta_trickle <= 0:
                        self.water_grid[i - 1, j] = 0
                        adjusted_trickle = adjusted_trickle - delta_trickle
                    else:
                        self.water_grid[i - 1, j] -= adjusted_trickle
                    self.water_grid[i, j] += adjusted_trickle

    def draw(self, screen):
        """
            draws a grid of size width i : shape(0)-1, height j : shape(1)
            each cell contains k drops that vary in color
            the offset_grid provides random offsets for size: i,j and k drops in x and y dimensions
            """
        for base_water in self.base_waters:
            base_water.draw(screen)
        # self.grid_screen.fill((0,0,0,0))
        for i in range(0, self.water_grid.shape[0] - 1):
            for j in range(0, self.water_grid.shape[1]):
                cell = self.water_grid[i, j]

                if cell > MINIMUM_CELL_AMOUNT_TO_DRAW:
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(
                        surface=screen,
                        # color variations
                        color=(0, 10 + offset_y, 255 - offset_x),
                        center=(
                            self.pos[0] + j * 100 + offset_x,
                            self.pos[1] + i * 100 + offset_y,
                        ),
                        radius=int(cell / (self.max_water_cell / 5) + 5),
                    )

                    n_drops = min(MAX_DROPS_TO_DRAW, int(cell / (self.max_water_cell / 20)))
                    for k in range(0, n_drops):
                        offset_x = self.offset_grid[0, k, i, j]
                        offset_y = self.offset_grid[1, k, i, j]
                        pygame.draw.circle(
                            screen,
                            (10, 10 + offset_y, 255 - offset_x),
                            (
                                self.pos[0] + j * 100 + offset_x,
                                self.pos[1] + i * 100 + offset_y,
                            ),
                            5,
                        )


class Base_water:
    """
    Base_water has no functionality. It visualizes a waving bottom layer of water.
    """
    def __init__(
        self,
        n_dots: int,
        base_height: int,
        width: int,
        y: int,
        color: tuple[int, int, int],
        line_color: tuple[int, int, int] = None,
        line_width: int = 5,
    ):
        self.gametime = GameTime.instance()
        self.width = width
        self.y = y
        self.n_dots = n_dots
        self.line_width = line_width
        self.line_color = line_color
        self.color = color
        self.base_height = base_height
        self.dots = []
        self.init_dots()

    def init_dots(self):
        """
        Initialise a chain of dots to draw the water surface
        """
        self.dots.append([0, self.y])
        for i in range(0, self.n_dots + 1):
            delta_x = self.width / self.n_dots
            self.dots.append([delta_x * i, self.y - self.base_height])
        self.dots.append([self.width, self.y])

    def update(self, dt):
        """
        Adjust the hight of each dot to move according to a sine wave, depending on the current time.
        """
        if self.n_dots > 0:
            ticks = self.gametime.get_time()
            day = 1000 * 60 * 60 * 24
            hour = day / 24
            hours = (ticks % day) / hour
            deg = hours / 24 * 360
            angle_offset = 360 / len(self.dots)

            for i in range(1, len(self.dots) - 1):
                self.dots[i][1] = self.y - (
                    self.base_height
                    + self.base_height
                    * 0.1
                    * math.sin(math.radians(10 * deg + angle_offset * i))
                )

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color, self.dots)
        if self.line_color:
            pygame.draw.lines(
                screen,
                self.line_color,
                False,
                self.dots[1:-1],
                self.line_width,
            )