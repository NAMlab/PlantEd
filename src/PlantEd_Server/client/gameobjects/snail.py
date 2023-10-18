import math
import pygame
import random

from PlantEd_Server.client.utils.animation import Animation
from PlantEd_Server.data import assets
from PlantEd_Server import config

LEFT = 0
RIGHT = 1


class SnailSpawner:
    def __init__(
            self,
            images_left,
            images_right,
            camera,
            callback,
            bounds=pygame.Rect(0, 0, 0, 0),
            max_amount=0,
            speed=3,
            snails=[],
            snail_clicked=None
    ):
        self.bounds = bounds
        self.max_amount = max_amount
        self.snails = snails
        self.camera = camera
        self.speed = speed
        self.snail_clicked = snail_clicked
        self.callback = callback
        self.images_left = images_left
        self.images_right = images_right

    def spawn_snail(self):
        self.snails.append(
            Snail(
                pos=(random.randint(0, 1) * self.bounds[2] + self.bounds[0],
                     random.random() * self.bounds[3] + self.bounds[1]),
                bounding_rect=self.bounds,
                images_left=self.images_left,
                images_right=self.images_right,
                camera=self.camera,
                callback=self.callback,
                eat_rate=0.0001,
                speed=self.speed,
                snail_clicked=self.snail_clicked
            )
        )

    def spray_snails(self, rect):
        for snail in self.snails:
            snail.kill(rect)

    def remove_dead_snails(self):
        tmp_snails = self.snails.copy()
        self.snails = []
        for snail in tmp_snails:
            if snail.dead:
                self.snails.remove(snail)

    def update(self, dt):
        for snail in self.snails:
            snail.update(dt)
            if snail.dead:
                self.snails.remove(snail)
        # self.remove_dead_snails()
        if random.random() > 0.9 and len(self.snails) < self.max_amount:
            self.spawn_snail()

    def handle_event(self, e):
        for snail in self.snails:
            snail.handle_event(e)

    def draw(self, screen):
        for snail in self.snails:
            snail.draw(screen)


class Snail:
    def __init__(
            self,
            pos,
            bounding_rect,
            images_left,
            images_right,
            camera,
            callback,
            eat_rate=0.00001,
            speed=1,
            snail_clicked=None
    ):
        self.state = LEFT
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images_left = images_left
        self.images_right = images_right
        self.camera = camera
        self.animation_left = Animation(self.images_left, 0.5)
        self.animation_right = Animation(self.images_right, 0.5)
        skull_images = Animation.generate_rising_animation(image=assets.img("skull.png", (64, 64)), move_up=-1)
        self.animation_death = Animation(images=skull_images, duration=1, running=False, once=True)
        self.speed = speed
        self.snail_clicked = snail_clicked
        self.base_speed = speed
        self.callback = callback
        self.rect = self.images_left[0].get_rect()
        self.dir = (0, 0)
        self.set_random_direction()
        self.target = None
        self.eat_rate = eat_rate
        self.nom_label = config.FONT.render("NOM NOM", True, (0, 0, 0))
        self.death_timer = 0
        self.dead = False

    def update(self, dt):
        if self.dead:
            return
        if self.death_timer > 0:
            self.death_timer -= dt
        if self.death_timer < 0:
            self.dead = True
            self.death_timer = 0
        if self.target:
            dist = math.sqrt((self.target[0] - self.pos[0]) * (self.target[0] - self.pos[0]))
            if dist < 10:
                self.callback(self.eat_rate, dt)
        elif random.random() > 0.999:
            self.set_random_direction()
        if self.target is None:
            if random.random() > 0.9999:
                self.target_plant((config.SCREEN_WIDTH / 2, 0))

        self.move(dt)
        self.animation_death.update(dt)
        if self.animation_left:
            self.animation_left.update(dt)
        if self.animation_right:
            self.animation_right.update(dt)

    def handle_event(self, e):
        if self.dead:
            return
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                self.scare_away()
                self.speed = 5
                self.snail_clicked()

    def set_random_direction(self):
        self.dir = ((random.randint(0, 1) - 0.5) * 2, 0)
        self.state = LEFT if self.dir[0] < 0 else RIGHT
        self.speed = self.base_speed

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
        self.speed = 3

    def kill(self, rect):
        if rect.collidepoint(self.pos):
            self.animation_death.start(self.pos)
            self.target = None
            self.speed = 0
            self.death_timer = 1

    def target_plant(self, pos):
        self.target = pos
        if self.target[0] - self.pos[0] < 0:
            self.dir = (-1, 0)
            self.state = LEFT
        else:
            self.dir = (1, 0)
            self.state = RIGHT

    def check_boundaries(self):
        if self.pos[0] < self.bounding_rect[0]:
            self.dir = (abs(self.dir[0]), self.dir[1])
            self.state = RIGHT
            self.speed = self.base_speed
        if self.pos[0] > self.bounding_rect[0] + self.bounding_rect[2]:
            self.dir = (abs(self.dir[0]) * -1, self.dir[1])
            self.state = LEFT

    def draw(self, screen):
        if self.dead:
            return
        self.animation_death.draw(screen)
        if self.target:
            dist = math.sqrt((self.target[0] - self.pos[0]) * (self.target[0] - self.pos[0]))
            if dist < 10:
                pygame.draw.rect(screen, config.WHITE, (
                    self.pos[0] + 20, self.pos[1] - 40, self.nom_label.get_width() + 20,
                    self.nom_label.get_height() + 10),
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
