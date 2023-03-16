from utils.animation import Animation
import random
from data import assets
import pygame

LEFT = 0
RIGHT = 1


class Snail:
    def __init__(
        self,
        pos,
        bounding_rect,
        images_left,
        images_right,
        camera,
        image=None,
        speed=3,
    ):
        self.state = LEFT
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images_left = images_left
        self.images_right = images_right
        self.camera = camera
        self.animation_left = Animation(self.images_left, 1)
        self.animation_right = Animation(self.images_right, 1)
        self.speed = speed
        self.rect = self.images_left[0].get_rect()
        self.dir = (0, 0)
        self.set_random_direction()

    def update(self, dt):
        if random.random() > 0.999:
            self.set_random_direction()
        self.move(dt)
        if self.animation_left:
            self.animation_left.update(dt)
        if self.animation_right:
            self.animation_right.update(dt)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            # print(self.get_rect(),pygame.mouse.get_pos(),self.camera.offset_y)
            # if self.bounding_rect.collidepoint(pygame.mouse.get_pos()):
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                self.set_random_direction()
                self.speed = 5
                assets.sfx(
                    "bug_click_sound/bug_squeek_{}.mp3".format(
                        random.randint(0, 2)
                    )
                ).play()

    def set_random_direction(self):
        self.dir = (random.random() - 0.5, 0)
        self.state = LEFT if self.dir[0] < 0 else RIGHT

    def get_rect(self):
        return pygame.Rect(
            self.pos[0] - self.rect[2] / 2,
            self.pos[1] - self.rect[3] / 2 + self.camera.offset_y,
            self.rect[2],
            self.rect[3],
        )

    def move(self, dt):
        self.check_boundaries()
        self.pos = (
            self.pos[0] + self.dir[0] * self.speed,
            self.pos[1] - self.dir[1] * self.speed,
        )

    def check_boundaries(self):
        if self.pos[0] < self.bounding_rect[0]:
            self.dir = (self.dir[0] * -1, self.dir[1])
            self.state = RIGHT
        if self.pos[0] > self.bounding_rect[0] + self.bounding_rect[2]:
            self.dir = (self.dir[0] * -1, self.dir[1])
            self.state = LEFT
        if self.pos[1] < self.bounding_rect[1]:
            self.dir = (self.dir[0], self.dir[1] * -1)
        if self.pos[1] > self.bounding_rect[1] + self.bounding_rect[3]:
            self.dir = (self.dir[0], self.dir[1] * -1)

    def draw(self, screen):
        # pygame.draw.rect(screen,config.WHITE,self.get_rect(),2)
        if self.state == LEFT:
            screen.blit(
                self.animation_left.image,
                (
                    int(self.pos[0] - self.rect[2] / 2),
                    int(self.pos[1] - self.rect[3] / 2),
                ),
            )
        else:
            screen.blit(
                self.animation_right.image,
                (
                    int(self.pos[0] - self.rect[2] / 2),
                    int(self.pos[1] - self.rect[3] / 2),
                ),
            )
