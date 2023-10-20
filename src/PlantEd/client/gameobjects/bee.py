import math
from typing import List
import random
import pygame

from PlantEd import config
from PlantEd.client.utils.animation import Animation
from PlantEd.data import assets


class Hive:
    def __init__(self, pos, amount, plant, camera, spawn_rate, play_hive_clicked, play_bee_clicked):
        self.pos = pos
        self.image = assets.img("bee/hive.png", (128, 128))
        self.amount = amount
        self.plant = plant
        self.camera = camera
        self.spawn_rate = spawn_rate
        self.play_hive_clicked = play_hive_clicked
        self.play_bee_clicked = play_bee_clicked

        self.bees: List[Bee] = []

    def handle_event(self, e):
        for bee in self.bees:
            bee.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            # if self.bounding_rect.collidepoint(pygame.mouse.get_pos()):
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                self.play_hive_clicked()
                if self.amount > len(self.bees):
                    self.spawn_bee(
                        (
                            self.pos[0] + self.image.get_width() / 2,
                            self.pos[1] + self.image.get_height() / 2,
                        )
                    )

    def get_rect(self):
        return pygame.Rect(
            self.pos[0],
            self.pos[1] + self.camera.offset_y,
            self.image.get_width(),
            self.image.get_height(),
        )

    def spray_bees(self, rect):
        for bee in self.bees:
            bee.kill(rect)

    def spawn_bee(self, pos=None):
        if not pos:
            pos = (190 * random.randint(0, 10), random.randint(0, 800))
        self.bees.append(
            Bee(
                pos=pos,
                bounding_rect=pygame.Rect(
                    0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - 200
                ),
                images=[
                    assets.img("bee/{}.PNG".format(i), (64, 64))
                    for i in range(6)
                ],
                camera=self.camera,
                hive_pos=self.pos,
                play_bee_clicked=self.play_bee_clicked
            )
        )

    def update(self, dt):
        for bee in self.bees:
            bee.update(dt)
            if bee.dead:
                if bee.death_timer > 0:
                    bee.death_timer -= dt
                else:
                    bee.death_timer = 0

        if random.random() > 0.99 and self.amount > len(self.bees):
            self.spawn_bee(
                (
                    self.pos[0] + self.image.get_width() / 2,
                    self.pos[1] + self.image.get_height() / 2,
                )
            )
        for i in range(len(self.bees)):
            if self.bees[i].dead and self.bees[i].death_timer == 0:
                self.bees.pop(i)
                break
            if self.get_rect().collidepoint(self.bees[i].pos):
                if self.bees[i].lifetime <= 0:
                    self.bees.pop(i)
                    break

    def draw(self, screen):
        screen.blit(self.image, self.pos)
        for bee in self.bees:
            bee.draw(screen)

    def get_free_bees(self):
        free_bees = []
        for bee in self.bees:
            if not bee.target:
                free_bees.append(bee)
        return free_bees


class Bee:
    def __init__(
        self,
        pos,
        bounding_rect,
        images,
        camera,
        hive_pos,
        image=None,
        speed=4,
        lifetime=20,
        play_bee_clicked=None
    ):
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images = images
        self.camera = camera
        self.hive_pos = hive_pos
        self.animation = Animation(self.images, 0.1)
        self.speed = speed
        self.lifetime = lifetime
        self.play_bee_clicked=play_bee_clicked
        self.rect = self.images[0].get_rect()
        self.dir = (0, 0)
        self.target = None
        self.return_home = False
        self.timer = 0
        self.max_timer = 10
        self.set_random_direction()
        self.dead = False
        self.death_timer = 0

    def update(self, dt):
        if self.dead:
            if self.death_timer > 0:
                self.death_timer -= dt
            else:
                self.death_timer = 0
        if (
            self.lifetime <= 0
            and not self.return_home and not self.dead
        ):
            self.set_target_home()
        else:
            self.lifetime -= dt
        self.move(dt)
        if not self.dead:
            if self.animation:
                self.animation.update(dt)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                if not self.target or self.dead:
                    self.set_random_direction()
                    self.speed = 4
                    self.play_bee_clicked()

    def set_random_direction(self):
        self.dir = (random.random() - 0.5, random.random() - 0.5)

    def get_rect(self):
        return pygame.Rect(
            self.pos[0] - self.rect[2] / 2,
            self.pos[1] - self.rect[3] / 2 + self.camera.offset_y,
            self.rect[2],
            self.rect[3],
        )

    def kill(self, rect):
        if rect.collidepoint(self.pos):
            self.target = None
            self.dir = (0,-1)
            self.death_timer = 2
            self.dead = True

    def move(self, dt):
        self.check_boundaries()
        self.pos = (
            self.pos[0] + self.dir[0] * self.speed,
            self.pos[1] - self.dir[1] * self.speed,
        )

        if self.target is not None:
            dist = self.get_dist_abs(self.target)
            if dist < 100:
                self.speed = 2
                if dist < 40:
                    self.speed = 1
                    if dist < 10 and not self.return_home:
                        self.speed = 0

    def get_dist_abs(self, target):
        return math.sqrt(
            (
                (target[0] - self.pos[0]) * (target[0] - self.pos[0])
                + (target[1] - self.pos[1]) * (target[1] - self.pos[1])
            )
        )

    def get_tagret_dir(self, target):
        x_dist = target[0] - self.pos[0]
        y_dist = target[1] - self.pos[1]
        max_distance = max(abs(x_dist), abs(y_dist))
        self.dir = (
            x_dist / max_distance,
            -1 * y_dist / max_distance,
        )

    def set_target_home(self):
        self.return_home = True
        self.get_tagret_dir(self.hive_pos)

    def check_boundaries(self):
        if self.pos[0] < self.bounding_rect[0]:
            self.dir = (self.dir[0] * -1, self.dir[1])
        if self.pos[0] > self.bounding_rect[0] + self.bounding_rect[2]:
            self.dir = (self.dir[0] * -1, self.dir[1])
        if self.pos[1] < self.bounding_rect[1]:
            self.dir = (self.dir[0], self.dir[1] * -1)
        if self.pos[1] > self.bounding_rect[1] + self.bounding_rect[3]:
            self.dir = (self.dir[0], self.dir[1] * -1)

    def draw(self, screen):
        # pygame.draw.rect(screen,config.WHITE,self.get_rect(),2)
        screen.blit(
            self.animation.image,
            (
                int(self.pos[0] - self.rect[2] / 2),
                int(self.pos[1] - self.rect[3] / 2),
            ),
        )
