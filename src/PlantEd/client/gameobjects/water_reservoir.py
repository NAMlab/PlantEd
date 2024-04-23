import numpy as np
from numpy import ndarray
import math
import pygame

from PlantEd.client.utils.gametime import GameTime
from PlantEd.constants import MAX_WATER_PER_CELL

# normal plant intake 83 (flux)
MINIMUM_CELL_AMOUNT_TO_DRAW: int = 20
MAX_DROPS_TO_DRAW: int = 20


class Water_Grid:
    """
    The soil is split into a grid of cells. Each cell holds water, can be drained and filled.
    Drainers are the plant and trickle
    Fillers are rain and the watering_can

    Dimensions: x horizontal, y vertical

    The grid shape defines the resolution of the grid. The root_grid must be of the same shape as water_grid.
    """

    def __init__(
        self,
        pos: tuple[int, int],
        screen_size: [int, int],
        grid_size: tuple[int, int] = (20, 6),
        max_water_cell: int = MAX_WATER_PER_CELL,
    ):
        self.pos = pos
        self.screen_size = screen_size
        self.water_grid: ndarray = np.zeros(grid_size)
        self.poured_cells: ndarray = np.zeros(20)
        self.available_water_grid: ndarray = np.zeros(grid_size)
        self.root_grid: ndarray
        self.pouring = False
        self.raining: bool = False
        self.base_waters: list[Base_water] = []
        self.max_water_cell = max_water_cell

        self.offset_grid: ndarray = np.random.randint(
            0,
            self.screen_size[1] / 11,
            (2, MAX_DROPS_TO_DRAW, grid_size[0], grid_size[1]),
        )
        self.grid_screen = pygame.Surface(self.screen_size, pygame.SRCALPHA)

    def update(self, dt):
        for base_water in self.base_waters:
            base_water.update(dt)

    def pour(self, rate: int, dt: float, pos: tuple[int, int]):
        self.pouring = True
        """
        Fill one cell of the upper row of the water grid with water until max_water_cell.

        Args:
            rate (int): precipitation micromol per second
            dt (float): ticks between last call
            pos (tuple[int, int]): position of watering can
        """
        if (
            not self.water_grid[int(pos[0] / (self.screen_size[1] / 10)), 0]
            > self.max_water_cell
        ):
            self.water_grid[int(pos[0] / (self.screen_size[1] / 10)), 0] += rate * dt
            self.poured_cells[int(pos[0] / (self.screen_size[1] / 10))] += rate * dt

    def pop_poured_cells(self):
        poured_sum = self.poured_cells.sum()
        if poured_sum > 0 and not self.pouring:
            poured_cells = self.poured_cells.copy()
            # normalize
            for i in range(len(poured_cells)):
                if poured_cells[i] > 0:
                    poured_cells[i] = poured_cells[i] / poured_sum
            poured_cells = {"cells": poured_cells.tolist()}
            self.poured_cells.fill(0)
            return poured_cells
        else:
            return None

    def add_base_water(self, base_water):
        """
        Add a row of base_water. Mainly for show, currently no function.
        """
        self.base_waters.append(base_water)

    def activate_rain(self):
        """
        Activate raining and set the raining amount per cell

        Args:
            precipitation (float): water fill amount per m² and second
        """
        self.raining = True

    def deactivate_rain(self):
        """
        Deactivate rain by setting raining to 0
        """
        self.raining = False

    def get_shape(self):
        """
        Return the shape of the water_grid
        """
        return self.water_grid.shape

    def draw(self, screen):
        """
        draws a grid of size width i : shape(0)-1, height j : shape(1)
        each cell contains k drops that vary in color
        the offset_grid provides random offsets for size: i,j and k drops in x and y dimensions
        """
        for base_water in self.base_waters:
            base_water.draw(screen)
        # self.grid_screen.fill((0,0,0,0))

        # x
        for i in range(0, self.water_grid.shape[0] - 1):
            # y
            for j in range(0, self.water_grid.shape[1]):
                cell = self.water_grid[i, j]

                if cell >= MINIMUM_CELL_AMOUNT_TO_DRAW:
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(
                        surface=screen,
                        # color variations
                        color=(0, 10 + offset_y, 255 - offset_x),
                        center=(
                            self.pos[0] + i * self.screen_size[1] / 10 + offset_x,
                            self.pos[1] + j * self.screen_size[1] / 10 + offset_y,
                        ),
                        radius=min(10, int(cell / (self.max_water_cell / 5) + 5)),
                    )

                    n_drops = min(
                        MAX_DROPS_TO_DRAW, int(cell / (self.max_water_cell / 20))
                    )
                    for k in range(0, n_drops):
                        offset_x = self.offset_grid[0, k, i, j]
                        offset_y = self.offset_grid[1, k, i, j]
                        pygame.draw.circle(
                            screen,
                            (10, 10 + offset_y, 255 - offset_x),
                            (
                                self.pos[0] + i * self.screen_size[1] / 10 + offset_x,
                                self.pos[1] + j * self.screen_size[1] / 10 + offset_y,
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
