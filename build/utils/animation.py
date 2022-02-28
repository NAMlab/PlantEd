import pygame
from pygame import Rect
import numpy as np

class OneShotAnimation(pygame.sprite.Sprite):
    def __init__(self, images, duration, pos, speed=1):
        super(OneShotAnimation, self).__init__()
        self.pos = pos
        self.rect = Rect(pos[0], pos[1], 10, 10)
        self.images = images
        self.image = images[0]
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.interval = int(duration / len(images))
        self.start_interval = self.interval
        self.index = 0
        self.speed = speed

    def update(self):
        time_elapsed = pygame.time.get_ticks() - self.start_time
        if time_elapsed >= self.interval:
            if self.index >= len(self.images) - 1:
                return False
            self.index += 1
            self.interval += self.start_interval
        self.image = self.images[self.index]
        return True

class Animation(pygame.sprite.Sprite):
    def __init__(self, images, duration, pos=[0,0], speed=1):
        super(Animation, self).__init__()
        self.pos = pos
        self.rect = Rect(pos[0], pos[1], 10, 10)
        self.images = images
        self.image = images[0]
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.interval = int(duration / len(images))
        self.start_interval = self.interval
        self.index = 0
        self.speed = speed

    def update(self):
        time_elapsed = pygame.time.get_ticks() - self.start_time
        if time_elapsed >= self.interval:
            self.index += 1
            if self.index >= len(self.images) - 1:
                self.index = 0
            self.interval += self.start_interval
        self.image = self.images[self.index]
        return True

class MoveAnimation(pygame.sprite.Sprite):
    def __init__(self, images, duration, lines, speed=1):
        super(MoveAnimation, self).__init__()
        self.lines = lines
        self.positions = []
        self.get_positions()
        self.pos = self.positions[0]
        self.pos_index = 0
        self.rect = None
        self.update_rect()
        self.images = images
        self.image = images[0]
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.interval = int(duration / len(self.positions))
        self.start_interval = self.interval
        self.index = 0
        self.speed = speed

    def get_positions(self):
        for line in self.lines:
            nx = line[0][0]-line[1][0]
            ny = line[0][1]-line[1][1]
            n = nx if nx != 0 else ny
            n = int(abs(n) / 10)
            points = np.linspace(line[0], line[1], n)
            for point in points:
                self.positions.append(point)

    def update_rect(self):
        self.rect = Rect(self.positions[self.pos_index][0], self.positions[self.pos_index][1], 10, 10)

    def update(self):
        time_elapsed = pygame.time.get_ticks() - self.start_time
        if time_elapsed >= self.interval:
            self.index += 1
            if self.index >= len(self.images) - 1:
                self.pos_index += 1
                self.index = 0
                if self.pos_index >= len(self.positions):
                    self.pos_index = 0
            self.interval += self.start_interval
        self.image = self.images[self.index]
        self.update_rect()
        return True