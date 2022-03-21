from utils.animation import Animation
import random
from data import assets

class Bug:
    def __init__(self, pos, bounding_rect, animation=None, image=None, speed=1):
        self.pos = pos
        self.rect = bounding_rect
        self.dir = (random.random(),random.random())
        self.image = image
        self.animation = animation
        self.speed = speed

    def update(self,dt):
        if self.animation:
            self.animation.update()
        if not self.rect.collidepoint(self.pos):
            self.dir = (random.random(),random.random())
        self.move(dt)

    def set_direction(self):
        self.dir = (random.random(), random.random())
        rad = assets.angle_between((0, 1), direction)
        deg = rad / math.pi * 180
        img, rect = rot_center(image, deg)
        for image in self.animation:
            rotated_image = image

    def move(self, dt):
        print(self.pos, self.dir)
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]+self.dir[1]*self.speed)


    def draw(self, screen):
        if self.animation:
            screen.blit(self.animation.image, self.pos)

        elif self.image:
            screen.blit(self.image, self.pos)