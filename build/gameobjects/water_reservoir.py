import numpy as np
import math
import pygame
from utils.gametime import GameTime
import random

# a grid of integers, indicating water amount
# falling down over time, into base water level -> lowest line of the grid
class Water_Grid:
    def __init__(self, pos=(0,900), grid_size=(6,20), max_water=250):
        self.pos = pos
        self.grid = np.zeros(grid_size)
        self.raining = 0
        self.trickle_amount = 0.01
        self.reservoirs = []
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

    def add_reservoir(self, reservoir):
        self.reservoirs.append(reservoir)

    def activate_rain(self):
        self.raining = 0.05

    def deactivate_rain(self):
        self.raining = 0

    def trickle(self, dt):
        for i in reversed(range(self.grid.shape[0]-1)):
            for j in range(0,self.grid.shape[1]):
                cell = self.grid[i,j]
                if cell > 2:
                    adjusted_trickle = self.trickle_amount*cell*self.gametime.GAMESPEED
                    temp = self.grid[i,j] - (self.trickle_amount + random.random()/10)
                    if temp < 0:
                        self.grid[i,j] = 0
                        temp = self.trickle_amount - temp
                    else:
                        self.grid[i,j] -= self.trickle_amount
                    if self.grid[i+1,j] < self.max_water:
                        self.grid[i+1,j] += self.trickle_amount


    def print_grid(self):
        print(self.grid)

    def draw(self, screen):
        #self.grid_screen.fill((0,0,0,0))
        for i in range(0,self.grid.shape[0]):
            for j in range(0,self.grid.shape[1]):
                cell = self.grid[i,j]
                if cell > 3:
                    #Todo make better loop, to draw at 0
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(screen, (0,10+offset_y,255-offset_x), (self.pos[0]+j * 100 + offset_x, self.pos[1]+i * 100 + offset_y), int(cell/50+5))

                    n_drops = int(cell/10)
                    for k in range(0,n_drops):
                        offset_x = self.offset_grid[0,k, i, j]
                        offset_y = self.offset_grid[1,k, i, j]
                        pygame.draw.circle(screen,(10,10+offset_y,255-offset_x),(self.pos[0]+j*100+offset_x,self.pos[1]+i*100+offset_y),int(cell/50+5))

        for reservoir in self.reservoirs:
            reservoir.draw(screen)
        #screen.blit(self.grid_screen,(0,0))


class Base_water:
    def __init(self, pos, width):
        self.pos = pos
        self.width = width


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