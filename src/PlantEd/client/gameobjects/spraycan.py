import pygame
from pygame import Rect
from pygame.locals import *

from PlantEd import config
from PlantEd.data import assets
from PlantEd.client.utils.particle import ParticleSystem


class Spraycan:
    def __init__(self,
                 pos,
                 amount,
                 callbacks=[],
                 play_sound=None
                 ):  # take from config
        self.pos = pos
        self.image_active = assets.img("spraycan_active.PNG", (128, 128))
        self.image_inactive = assets.img("spraycan.PNG", (128, 128))
        self.image = self.image_inactive
        self.default_amount = amount
        self.amount = amount
        self.hitbox = pygame.Rect(self.pos[0]-125,self.pos[1]-25,150,150)
        self.max_amount = amount
        self.callbacks = callbacks
        self.play_sound = play_sound
        self.active = False
        self.can_particle_system = ParticleSystem(
            50,
            spawn_box=Rect(self.pos[0], self.pos[1], 0, 0),
            lifetime=13,
            color=config.PURPLE,
            apply_gravity=True,
            speed=[-35, 15],
            spread=[10, 10],
            active=False,
            size=10,
            size_over_lifetime=True,
            once=True,
        )

    def activate(self, amount=None):
        self.amount = self.default_amount if amount is None else amount
        self.pos = pygame.mouse.get_pos()
        self.active = True
        pygame.mouse.set_visible(False)
        self.can_particle_system.spawn_box = Rect(
            self.pos[0], self.pos[1], 0, 0
        )

    def deactivate(self):
        self.image = self.image_inactive
        self.amount = 0
        self.active = False
        pygame.mouse.set_visible(True)

    def update(self, dt):
        self.can_particle_system.update(dt)
        if self.active:
            if self.amount <= 0:
                self.amount = 0
                self.deactivate()

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEBUTTONDOWN:
            self.image = self.image_active
            self.can_particle_system.activate()
            self.play_sound()
            for callback in self.callbacks:
                callback(self.hitbox)
        if e.type == MOUSEBUTTONUP:
            self.amount -= 1
            self.image = self.image_inactive
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x, y)
            self.can_particle_system.spawn_box = Rect(x, y, 0, 0)
            self.hitbox = pygame.Rect(self.pos[0] - 125, self.pos[1]-25, 150, 150)

    def draw(self, screen):
        self.can_particle_system.draw(screen)
        if self.active:
            # pygame.draw.rect(screen, config.GREEN, self.hitbox, width=5)
            w = self.image.get_width()
            line_width = w / self.max_amount
            for i in range(0, self.amount):
                pygame.draw.rect(
                    screen,
                    config.BLACK,
                    (self.pos[0], self.pos[1] - 15, (i + 1) * line_width, 10),
                    border_radius=3,
                )
                pygame.draw.rect(
                    screen,
                    config.WHITE,
                    (
                        self.pos[0] + 2,
                        self.pos[1] - 13,
                        (i + 1) * line_width - 4,
                        6,
                    ),
                    border_radius=3,
                )
            screen.blit(self.image, self.pos)
