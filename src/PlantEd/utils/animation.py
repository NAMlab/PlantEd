import pygame
from pygame import Rect
import numpy as np
import config


class Animation:
    def __init__(self, images, duration, pos=[0, 0], running=True):
        self.pos = pos
        self.rect = Rect(pos[0], pos[1], 10, 10)
        self.images = images
        self.image = images[0]
        self.duration = duration
        self.timer = 0
        self.interval = int(
            duration / len(images)
        )  # delta time to switch images
        self.start_interval = self.interval
        self.index = 0
        self.running = running

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def update(self, dt):
        if self.running:
            self.timer += dt
            if self.timer >= self.interval:
                self.index += 1
                self.timer = 0
                if self.index >= len(self.images) - 1:
                    self.index = 0
                self.interval += self.start_interval
            self.image = self.images[self.index]

    def draw(self, screen):
        if self.running:
            screen.blit(self.image, self.pos)
