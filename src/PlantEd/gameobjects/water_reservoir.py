import numpy as np
import math
import pygame

from PlantEd.client import Water, Client
from PlantEd.utils.gametime import GameTime
import random


# normal plant intake 83 (flux)
# Grid 6*20 = 120 * 0.75 = 80 -> /60/60*240 to convert from hourly to each second -> 5.3 = 120 * 0.05, double to enable more growth
DRAIN_DEFAULT = 0.005  # *3600/240 to adjust to hourly

# rain should be much more than consumption
RAIN_RATE = 8
TRICKLE_AMOUNT = 0.001

MAX_DRAIN_CELL = 100


# falling down over time, into base water level -> lowest line of the grid
class Water_Grid:
    def __init__(
        self, pos=(0, 900), grid_size=(6, 20), max_water_cell=1000000
    ):
        self.pos = pos

        self.water_grid = np.zeros(grid_size)
        self.available_water_grid = np.zeros(grid_size)
        self.root_grid = None

        self.raining = 0
        self.trickle_amount = TRICKLE_AMOUNT
        self.reservoirs = []
        self.base_waters = []
        self.max_water_cell = max_water_cell
        self.offset_grid = np.random.randint(0, 90, (2, 25, 10, 20))
        self.grid_screen = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.gametime = GameTime.instance()

    def update(self, dt, water: Water, client: Client):
        if self.raining > 0:
            self.water_grid[0, :] += (
                self.raining * self.gametime.GAMESPEED * dt
            )
            # self.water_grid[0, 0] < self.max_water_cell
        self.trickle(dt)

        # self.set_max_drain_rate()
        self.drain_grid(dt, water=water, client=client)

        for reservoir in self.reservoirs:
            reservoir.update(dt)
        for base_water in self.base_waters:
            base_water.update(dt)

    def set_root_grid(self, root_grid):
        self.root_grid = root_grid

    def drain_grid(self, dt, water: Water, client: Client):
        # drain water from plant
        water_neded = water.water_intake
        transpiration = water.transpiration

        transpiration *= 10
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
                # ensure its not looping forever
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

    def pour(self, rate, dt, pos):
        if not self.water_grid[0, int(pos[0] / 100)] > self.max_water_cell:
            self.water_grid[0, int(pos[0] / 100)] += rate * dt

    def add_reservoir(self, reservoir):
        self.reservoirs.append(reservoir)

    def add_base_water(self, base_water):
        self.base_waters.append(base_water)

    def activate_rain(self, precipitation=RAIN_RATE):
        self.raining = precipitation

    def deactivate_rain(self):
        self.raining = 0

    def get_shape(self):
        return self.water_grid.shape

    def trickle(self, dt):
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

    def print_grid(self):
        print(self.water_grid)

    def draw(self, screen):
        for base_water in self.base_waters:
            base_water.draw(screen)
        # self.grid_screen.fill((0,0,0,0))
        for i in range(0, self.water_grid.shape[0] - 1):
            for j in range(0, self.water_grid.shape[1]):
                cell = self.water_grid[i, j]

                if cell > 20:
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(
                        screen,
                        (0, 10 + offset_y, 255 - offset_x),
                        (
                            self.pos[0] + j * 100 + offset_x,
                            self.pos[1] + i * 100 + offset_y,
                        ),
                        int(cell / (self.max_water_cell / 5) + 5),
                    )

                    n_drops = min(24, int(cell / (self.max_water_cell / 20)))
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
                # number = config.FONT.render("{:.2f}".format(cell),True,config.BLACK,config.WHITE)
                # screen.blit(number, (j * 100, 900 + i * 100))
        for reservoir in self.reservoirs:
            reservoir.draw(screen)


class Base_water:
    def __init__(
        self,
        n_dots,
        base_height,
        width,
        y,
        color,
        line_color=None,
        line_width=5,
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
        self.dots.append([0, self.y])
        for i in range(0, self.n_dots + 1):
            delta_x = self.width / self.n_dots
            self.dots.append([delta_x * i, self.y - self.base_height])
        self.dots.append([self.width, self.y])

    def update(self, dt):
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


class Water_Reservoir:
    def __init__(self, pos, n_verticies, length):
        self.pos = pos
        self.verticies = np.empty(n_verticies)
        self.base_length = length
        self.gametime = GameTime.instance()

    def update(self, dt):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        hours = (ticks % day) / hour
        deg = hours / 24 * 360
        angle_offset = 360 / len(self.verticies)

        for i in range(0, len(self.verticies)):
            self.verticies[
                i
            ] = self.base_length + self.base_length * 0.1 * math.sin(
                math.radians(10 * deg + angle_offset * i)
            )  # if math.sin(math.radians(deg+angle_offset*i)) > 0 else base_length
            self.verticies[i] = self.verticies[
                i
            ] + self.base_length * 0.02 * math.cos(
                3 * math.radians(10 * deg + angle_offset * i * 2)
            )

    def draw(self, screen):
        offset_x, offset_y = self.pos
        angle_offset = 360 / len(self.verticies)

        points = []
        for i in range(0, len(self.verticies)):
            x, y = (
                math.sin(math.radians(angle_offset * i)) * self.verticies[i]
                + offset_x,
                math.cos(math.radians(angle_offset * i)) * self.verticies[i]
                + offset_y,
            )
            points.append((x, y))
        pygame.draw.polygon(screen, (10, 40, 190), points)

        points = []
        for i in range(0, len(self.verticies)):
            x, y = (
                math.cos(math.radians(angle_offset * i))
                * self.verticies[i]
                * 0.5
                + offset_x,
                math.sin(math.radians(angle_offset * i))
                * self.verticies[i]
                * 0.5
                + offset_y,
            )
            points.append((x, y))
        pygame.draw.polygon(screen, (25, 30, 255), points)
