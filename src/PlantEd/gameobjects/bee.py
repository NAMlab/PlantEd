from utils.animation import Animation
import random
from data import assets
import math
import pygame
import numpy as np
import config


class Hive:
    def __init__(self, pos, amount, plant, camera, spawn_rate):
        self.pos = pos
        self.image = assets.img("bee/hive.png", (128, 128))
        self.amount = amount
        self.plant = plant
        self.camera = camera
        self.spawn_rate = spawn_rate

        self.bees = []

    def handle_event(self, e):
        for bee in self.bees:
            bee.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            # print(self.get_rect(),pygame.mouse.get_pos(),self.camera.offset_y)
            # if self.bounding_rect.collidepoint(pygame.mouse.get_pos()):
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                assets.sfx("bee/beehive_clicked.mp3").play()
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
            self.pos[1],
            self.image.get_width(),
            self.image.get_height(),
        )

    def spawn_bee(self, pos=None):
        if not pos:
            pos = (190 * random.randint(0, 10), random.randint(0, 800))
        self.bees.append(
            Bee(
                pos,
                pygame.Rect(
                    0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - 200
                ),
                [
                    assets.img("bee/{}.PNG".format(i), (64, 64))
                    for i in range(6)
                ],
                self.camera,
                self.plant.organs[3].pollinate,
                pos,
            )
        )

    def update(self, dt):
        for bee in self.bees:
            bee.update(dt)
        if random.random() > 0.99 and self.amount > len(self.bees):
            self.spawn_bee(
                (
                    self.pos[0] + self.image.get_width() / 2,
                    self.pos[1] + self.image.get_height() / 2,
                )
            )
        if random.random() > 0.995 and len(self.bees) > 0:
            free_bees = self.get_free_bees()
            if len(free_bees) > 0:
                i = int(random.random() * len(free_bees))
                flower_pos, target_flower_id = self.plant.organs[
                    3
                ].get_random_flower_pos()
                if flower_pos:
                    """flower_pos = (self.plant.organs[3].flowers[0]["x"] + self.plant.organs[3].flowers[0]["offset_x"] / 2,
                    self.plant.organs[3].flowers[0]["y"] + self.plant.organs[3].flowers[0]["offset_y"] / 2 - 20)
                    """
                    self.start_pollination(
                        flower_pos, target_flower_id, free_bees[i]
                    )
        for i in range(len(self.bees)):
            if self.get_rect().collidepoint(self.bees[i].pos):
                if self.bees[i].lifetime <= 0:
                    # if abs((self.bees[i].pos[0] - (self.pos[0]+self.image.get_width()/2)) + (self.bees[i].pos[0] - (self.pos[1]+self.image.get_height()/2))) < 25:
                    self.bees.pop(i)
                    break

    def draw(self, screen):
        screen.blit(self.image, self.pos)
        for bee in self.bees:
            bee.draw(screen)

    def start_pollination(self, flower_pos, target_flower_id, bee):
        bee.target_flower(flower_pos, target_flower_id, 6)

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
        callback,
        hive_pos,
        image=None,
        speed=4,
        lifetime=20,
    ):
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images = images
        self.camera = camera
        self.callback = callback
        self.hive_pos = hive_pos
        self.animation = Animation(self.images, 0.5)
        self.speed = speed
        self.lifetime = lifetime
        self.rect = self.images[0].get_rect()
        self.dir = (0, 0)
        self.target = None
        self.target_flower_id = None
        self.return_home = False
        self.pollinating = False
        self.timer = 0
        self.max_timer = 10
        self.pollinating_label = config.BIG_FONT.render(
            "Pollinating...", True, config.BLACK
        )
        self.set_random_direction()

    def update(self, dt):
        if self.lifetime <= 0 and not self.return_home:
            self.set_target_home()
        else:
            self.lifetime -= dt
        if self.pollinating:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0
                self.pollinating = False
                self.target = None
                self.set_random_direction()
                self.speed = 3
                self.callback(self.target_flower_id)
                self.target_flower_id = None
        """if random.random() > 0.999:
            self.set_random_direction()"""
        self.move(dt)
        if self.animation:
            self.animation.update(dt)

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
        self.dir = (random.random() - 0.5, random.random() - 0.5)

    def get_rect(self):
        return pygame.Rect(
            self.pos[0] - self.rect[2] / 2,
            self.pos[1] - self.rect[3] / 2 + self.camera.offset_y,
            self.rect[2],
            self.rect[3],
        )

    def start_pollinating(self):
        if not self.pollinating:
            self.speed = 0
            self.pollinating = True
            self.timer = self.max_timer

    def move(self, dt):
        self.check_boundaries()
        self.pos = (
            self.pos[0] + self.dir[0] * self.speed,
            self.pos[1] - self.dir[1] * self.speed,
        )

        if self.target is not None:
            if (
                abs(
                    (self.target[0] - self.pos[0])
                    + (self.target[1] - self.pos[1])
                )
                < 100
                and not self.pollinating
            ):
                self.speed = 2
                if (
                    abs(
                        (self.target[0] - self.pos[0])
                        + (self.target[1] - self.pos[1])
                    )
                    < 5
                ):
                    self.start_pollinating()
                    # self.callback()

    def target_flower(self, flower_pos, target_flower_id, speed):
        self.target_flower_id = target_flower_id
        self.speed = speed
        x_dist = flower_pos[0] - self.pos[0]
        y_dist = flower_pos[1] - self.pos[1]
        max_distance = max(x_dist, y_dist)
        self.dir = (
            x_dist / abs(max_distance),
            -1 * y_dist / abs(max_distance),
        )
        self.target = flower_pos

    def set_target_home(self):
        self.return_home = True
        x_dist = self.hive_pos[0] - self.pos[0]
        y_dist = self.hive_pos[1] - self.pos[1]
        max_distance = max(x_dist, y_dist)
        self.dir = (
            x_dist / abs(max_distance),
            -1 * y_dist / abs(max_distance),
        )

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
        if self.target is not None:
            pygame.draw.line(
                screen, config.WHITE, self.pos, self.target, width=3
            )

        if self.pollinating:
            pygame.draw.rect(
                screen,
                config.WHITE_TRANSPARENT,
                (
                    self.pos[0],
                    self.pos[1] - 50,
                    self.pollinating_label.get_width() + 10,
                    self.pollinating_label.get_height() + 10,
                ),
                border_radius=3,
            )
            width = (
                1 - self.timer / self.max_timer
            ) * self.pollinating_label.get_width() + 10
            pygame.draw.rect(
                screen,
                config.WHITE,
                (
                    self.pos[0],
                    self.pos[1] - 50,
                    width,
                    self.pollinating_label.get_height() + 10,
                ),
                border_radius=3,
            )
            screen.blit(
                self.pollinating_label, (self.pos[0] + 5, self.pos[1] - 45)
            )
