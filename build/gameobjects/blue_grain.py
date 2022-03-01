import pygame
from data import assets
from utils.particle import ParticleSystem
from pygame import Rect
import config
from pygame.locals import *


class Blue_grain:
    def __init__(self, pos, amount=5):
        self.image = assets.img("blue_grain_bag.png")
        self.pos = pos
        self.amount = amount
        self.active = False
        self.particle_system = ParticleSystem(40, spawn_box=Rect(self.pos[0], self.pos[1], 50, 50),
                                                    boundary_box=Rect(0,0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT-220),
                                                    lifetime=20, size=8, color=config.BLUE,apply_gravity=True,speed=[0, 5],
                                                    spread=[6,0], active=False, once=True, size_over_lifetime=False)

    def activate(self, pos=None):
        self.pos = (int(pos[0] - self.image.get_width()/2), int(pos[1] - self.image.get_height()/2)) if pos else(0,0)
        self.active = True
        pygame.mouse.set_visible(False)

    def deactivate(self):
        self.active = False
        pygame.mouse.set_visible(True)

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            self.pos = (int(mouse_pos[0] - self.image.get_width()/2), int(mouse_pos[1] - self.image.get_height()/2))
        if e.type == MOUSEBUTTONDOWN:
            self.particle_system.spawn_box = Rect(self.pos[0], self.pos[1], 0, 0)
            self.particle_system.activate()
            self.deactivate()

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            screen.blit(self.image, self.pos)