from utils.animation import Animation
import random
from data import assets
import math

class Bug:
    def __init__(self, pos, bounding_rect, animation=None, image=None, speed=1):
        self.pos = pos
        self.rect = bounding_rect
        self.image = image
        self.animation = animation
        self.speed = speed
        self.dir = (0,0)
        self.set_direction()

    def update(self,dt):
        if self.animation:
            self.animation.update()
        #if not self.rect.collidepoint(self.pos):
        #    self.set_direction()
        self.move(dt)

    def set_direction(self):
        self.dir = (random.random() - 0.5, random.random() - 0.5)
        rad = assets.angle_between((0, 1), self.dir)
        deg = rad / math.pi * 180
        if self.dir[0] > 0:
            deg += 180
        rotated_images = []
        for image in self.animation.images:
            rotated_images.append(assets.rot_center(image, deg)[0])
        self.animation.images = rotated_images
        self.animation.image = rotated_images[0]

    def move(self, dt):
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]+self.dir[1]*self.speed)


    def draw(self, screen):
        if self.animation:
            screen.blit(self.animation.image, self.pos)

        elif self.image:
            screen.blit(self.image, self.pos)