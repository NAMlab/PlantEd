import pygame
from data import assets
from utils.particle import ParticleSystem
from pygame import Rect
import config
from pygame.locals import *


class Blue_grain:
    def __init__(self, pos, model, amount=25000):
        self.image = assets.img("blue_grain_bag.png",(128,128))
        self.pos = pos
        self.model = model
        self.amount = amount
        self.active = False
        self.particle_system = ParticleSystem(80, spawn_box=Rect(self.pos[0], self.pos[1], 50, 50),
                                                    boundary_box=Rect(0,0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT-220),
                                                    lifetime=25, size=10, color=config.BROWN,apply_gravity=True,speed=[20, 70],
                                                    spread=[60,10], active=False, once=True, color_spectrum=10, size_over_lifetime=False)

    def activate(self, pos=None):
        pos = pos if pos else pygame.mouse.get_pos()
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
            x,y = pygame.mouse.get_pos()
            self.pos = (x+120,y+120)
        if e.type == MOUSEBUTTONDOWN:
            self.particle_system.spawn_box = Rect(self.pos[0], self.pos[1], 20, 20)
            self.particle_system.activate()
            self.model.increase_nitrate(self.amount)
            self.deactivate()

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            screen.blit(self.image, self.pos)