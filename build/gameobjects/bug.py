from utils.animation import Animation
import random
from data import assets
import math
import pygame
import numpy as np
import config

class Bug:
    def __init__(self, pos, bounding_rect, images, image=None, speed=1):
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images = images
        self.image = image if image else self.images[0]
        self.animation = Animation(self.images, 720)
        self.speed = speed
        self.rect = self.image.get_rect()
        self.dir = (0,0)
        self.pause_timer = 0
        self.set_random_direction()

    def update(self,dt):
        self.pause_timer -= 1
        if self.pause_timer <= 0:
            if random.random() > 0.99:
                self.pause_timer = 360
            self.move(dt)
            if self.animation:
                self.animation.update()

    def set_random_direction(self):
        self.dir = (random.random() - 0.5, random.random() - 0.5)
        self.rotate_images()

    def rotate_images(self):
        rad = self.angle_between((0,1), (self.dir[0],self.dir[1]))
        deg = int(rad / math.pi * 180)
        if self.dir[0] < 0:
            deg = 360 - deg
        rotated_images = []
        for image in self.images:
            rotated_image, self.rect = self.rot_center(image, -deg)
            rotated_images.append(rotated_image)
        self.animation.images = rotated_images

    def move(self, dt):
        self.check_boundaries()
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]-self.dir[1]*self.speed)

    def check_boundaries(self):
        if self.pos[0] < self.bounding_rect[0]:
            self.dir = (self.dir[0]*-1,self.dir[1])
        if self.pos[0] > self.bounding_rect[0]+self.bounding_rect[2]:
            self.dir = (self.dir[0]*-1,self.dir[1])
        if self.pos[1] < self.bounding_rect[1]:
            self.dir = (self.dir[0],self.dir[1]*-1)
        if self.pos[1] > self.bounding_rect[1] + self.bounding_rect[3]:
            self.dir = (self.dir[0],self.dir[1]*-1)
        self.rotate_images()

    def draw(self, screen):
        if self.animation:
            screen.blit(self.animation.image, (int(self.pos[0]-self.rect[2]/2),int(self.pos[1]-self.rect[3]/2)))
        elif self.image:
            screen.blit(self.image, self.pos)

    def unit_vector(self, vector):
        return vector / np.linalg.norm(vector)

    def angle_between(self, v1, v2):
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    def rot_center(self, image, angle):
        x = image.get_width() / 2
        y = image.get_height() / 2
        rotated_image = pygame.transform.rotate(image, angle)
        new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)
        return rotated_image, new_rect