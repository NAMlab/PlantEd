import math

from PlantEd.utils.animation import Animation
import random
from PlantEd.data import assets
import pygame
from PlantEd import config

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
            eat_plant,
            image=None,
            speed=3
    ):
        self.state = LEFT
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images_left = images_left
        self.images_right = images_right
        self.camera = camera
        self.animation_left = Animation(self.images_left, 0.5)
        self.animation_right = Animation(self.images_right, 0.5)
        self.speed = speed
        self.eat_plant = eat_plant
        self.rect = self.images_left[0].get_rect()
        self.dir = (0, 0)
        self.set_random_direction()
        self.target = None
        self.eat_rate = 0.000001  # gramm per second
        self.nom_label = config.FONT.render("NOM NOM", True, (0, 0, 0))
        self.death_timer = 0
        self.die = False

    def update(self, dt):
        if self.die:
            if random.random() > 0.9999:
                self.die = False
                self.pos = (-100,900)
                self.dir = (1,0)
            return
        if self.death_timer > 0:
            self.death_timer -= dt
        if self.death_timer < 0:
            self.die = True
            self.death_timer = 0
        if self.target:
            dist = math.sqrt((self.target[0] - self.pos[0]) * (self.target[0] - self.pos[0]))
            if dist < 10:
                self.eat_plant(self.eat_rate, dt)
        elif random.random() > 0.999:
            self.set_random_direction()
        if self.target is None:
            if random.random() > 0.999:
                self.target_plant((config.SCREEN_WIDTH/2, 0))

        self.move(dt)
        if self.animation_left:
            self.animation_left.update(dt)
        if self.animation_right:
            self.animation_right.update(dt)

    def handle_event(self, e):
        if self.die:
            return
        if e.type == pygame.MOUSEBUTTONDOWN:
            # print(self.get_rect(),pygame.mouse.get_pos(),self.camera.offset_y)
            # if self.bounding_rect.collidepoint(pygame.mouse.get_pos()):
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                self.scare_away()
                self.speed = 5
                assets.sfx(
                    "bug_click_sound/bug_squeek_{}.mp3".format(
                        random.randint(0, 2)
                    )
                ).play()

    def set_random_direction(self):
        self.dir = ((random.randint(0, 1) - 0.5)*2, 0)
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
        if self.target:
            dist = math.sqrt((self.target[0] - self.pos[0]) * (self.target[0] - self.pos[0]))
            if dist < 10:
                return
        self.pos = (
            self.pos[0] + self.dir[0] * self.speed,
            self.pos[1] - self.dir[1] * self.speed,
        )

    def scare_away(self):
        self.target = None
        self.set_random_direction()
        self.speed = 5

    def kill(self, rect):
        print(rect, self.pos)
        if rect.collidepoint(self.pos):
            self.target = None
            self.set_random_direction()
            self.speed = 1
            self.death_timer = 1

    def target_plant(self, pos):
        self.target = pos
        if self.target[0] - self.pos[0] < 0:
            self.dir = (-1, 0)
            self.state = LEFT
        else:
            self.dir = (1, 0)
            self.state = RIGHT

        print(self.dir, self.pos)

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
        if self.die:
            return
        if self.target:
            dist = math.sqrt((self.target[0] - self.pos[0]) * (self.target[0] - self.pos[0]))
            if dist < 10:
                pygame.draw.rect(screen, config.WHITE, (
                self.pos[0] + 20, self.pos[1] - 40, self.nom_label.get_width() + 20, self.nom_label.get_height() + 10),
                                 border_radius=3)
                screen.blit(self.nom_label, (self.pos[0] + 30, self.pos[1] - 35))
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
