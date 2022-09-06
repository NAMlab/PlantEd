import numpy as np
import math
import pygame
from utils.gametime import GameTime
import random
import config

# a grid of integers, indicating water amount
# falling down over time, into base water level -> lowest line of the grid
class Water_Grid:
    def __init__(self, pos=(0,900), grid_size=(6,20), max_water=250):
        self.pos = pos
        self.grid = np.zeros(grid_size)
        self.raining = 0
        self.trickle_amount = 0.01
        self.reservoirs = []
        self.base_waters = []
        self.max_water = max_water
        self.offset_grid = np.random.randint(0,90,(2,25,10,20))
        self.grid_screen = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.gametime = GameTime.instance()

    def update(self, dt):
        if self.raining > 0 and self.grid[0,0] < self.max_water:
            self.grid[0,:] += self.raining
        self.trickle(dt)
        for reservoir in self.reservoirs:
            reservoir.update(dt)
        for base_water in self.base_waters:
            base_water.update(dt, self.grid[-1,0])

    def add_reservoir(self, reservoir):
        self.reservoirs.append(reservoir)

    def add_base_water(self, base_water):
        self.base_waters.append(base_water)

    def activate_rain(self):
        self.raining = 0.05

    def deactivate_rain(self):
        self.raining = 0

    def get_shape(self):
        return self.grid.shape

    def get_water_intake(self, root_mass, apexes):
        pass
        # list of apexes match with grid

    def trickle(self, dt):
        for i in reversed(range(1,self.grid.shape[0])):
            for j in range(0,self.grid.shape[1]):

                #print(i, i-1, j, "Current_Cell: ", self.grid[i, j], "Upper_CELL:", self.grid[i -1, j])

                upper_cell = self.grid[i-1,j]
                adjusted_trickle = self.trickle_amount * upper_cell * self.gametime.GAMESPEED / 100 * random.random()

                #check if zero in upper cell
                delta_trickle = self.grid[i - 1, j] - adjusted_trickle
                if delta_trickle < 0:
                    self.grid[i - 1, j] = 0
                    adjusted_trickle = adjusted_trickle - delta_trickle
                else:
                    self.grid[i - 1, j] -= adjusted_trickle

                if self.grid[i, j] < self.max_water:
                    self.grid[i, j] += adjusted_trickle
        # Todo maybe shitty to just delete it
        #self.grid[-1,:] = 0

    def print_grid(self):
        print(self.grid)

    def draw(self, screen):
        for base_water in self.base_waters:
            base_water.draw(screen)
        #self.grid_screen.fill((0,0,0,0))
        for i in range(0,self.grid.shape[0]-1):
            for j in range(0,self.grid.shape[1]):
                cell = self.grid[i,j]
                #number = config.FONT.render("{:2f}".format(cell),True,config.BLACK,config.WHITE)
                #screen.blit(number,(j*100,900+i*100))
                if cell > 0:
                    #Todo make better loop, to draw at 0
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(screen, (0,10+offset_y,255-offset_x), (self.pos[0]+j * 100 + offset_x, self.pos[1]+i * 100 + offset_y), int(cell/20+5))

                    n_drops = int(cell/5)
                    for k in range(0,n_drops):
                        offset_x = self.offset_grid[0,k, i, j]
                        offset_y = self.offset_grid[1,k, i, j]
                        pygame.draw.circle(screen,(10,10+offset_y,255-offset_x),(self.pos[0]+j*100+offset_x,self.pos[1]+i*100+offset_y),int(cell/20+5))

        for reservoir in self.reservoirs:
            reservoir.draw(screen)

class Base_water:
    def __init__(self, n_dots, base_height, width, y, color, line_color=None, line_width=5):
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
            self.dots.append([delta_x * i, self.y-self.base_height])
        self.dots.append([self.width, self.y])

    def update(self,dt,lower_amount):
        if self.n_dots > 0:
            ticks = self.gametime.get_time()
            day = 1000 * 60 * 6
            hour = day / 24
            hours = (ticks % day) / hour
            deg = hours / 24 * 360
            angle_offset = 360 / len(self.dots)

            for i in range(1, len(self.dots) - 1):
                self.dots[i][1] = self.y - (self.base_height + lower_amount + self.base_height * 0.1 * math.sin(math.radians(
                    10 * deg + angle_offset * i)))

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color, self.dots)
        if self.line_color:
            pygame.draw.lines(screen,self.line_color,False,self.dots[1:-1],self.line_width)


class Water_Reservoir:
    def __init__(self, pos, n_verticies, length):
        self.pos = pos
        self.verticies = np.empty(n_verticies)
        self.base_length = length
        self.gametime = GameTime.instance()

    def update(self, dt):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 6
        hour = day / 24
        hours = (ticks % day) / hour
        deg = hours / 24 * 360
        angle_offset = 360 / len(self.verticies)

        for i in range(0, len(self.verticies)):
            self.verticies[i] = self.base_length + self.base_length * 0.1 * math.sin(math.radians(
                10* deg + angle_offset * i))  # if math.sin(math.radians(deg+angle_offset*i)) > 0 else base_length
            self.verticies[i] = self.verticies[i] + self.base_length * 0.02 * math.cos(3*math.radians(
                10 * deg + angle_offset * i*2))

    def draw(self, screen):
        offset_x, offset_y = self.pos
        angle_offset = 360 / len(self.verticies)

        points = []
        for i in range(0, len(self.verticies)):
            x, y = math.sin(math.radians(angle_offset * i)) * self.verticies[i] + offset_x, math.cos(
                math.radians(angle_offset * i)) * self.verticies[i] + offset_y
            points.append((x, y))
        pygame.draw.polygon(screen, (10, 40, 190), points)

        points = []
        for i in range(0, len(self.verticies)):
            x, y = math.cos(math.radians(angle_offset * i)) * self.verticies[i] * 0.5 + offset_x, math.sin(
                math.radians(angle_offset * i)) * self.verticies[i] * 0.5 + offset_y
            points.append((x, y))
        pygame.draw.polygon(screen, (25, 30, 255), points)