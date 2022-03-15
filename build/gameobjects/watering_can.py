import pygame
from data import assets
from utils.particle import ParticleSystem
from pygame import Rect
import config
from pygame.locals import *
from fba import dynamic_model


class Watering_can:
    def __init__(self, pos, model, amount=0, rate=0.15, cost=1): # take from config
        self.pos = pos
        self.model = model
        self.image = assets.img("watering_can_outlined.png")
        self.amount = amount
        self.default_amount = 10 #add to config
        self.rate = rate
        self.default_rate = 0.15 #add to config
        self.cost = cost
        self.active = False
        self.pouring = False
        self.can_particle_system = ParticleSystem(40, spawn_box=Rect(self.pos[0], self.pos[1], 0, 0), lifetime=8,
                                                  color=config.BLUE,apply_gravity=True,speed=[0, 5],
                                                  spread=[3, 0], active=False)

    def activate(self, amount=None):
        self.amount = self.default_amount if amount is None else amount
        self.pos = pygame.mouse.get_pos()
        self.active = True
        pygame.mouse.set_visible(False)
        self.can_particle_system.spawn_box = Rect(self.pos[0], self.pos[1] + 100, 0, 0)
        self.can_particle_system.activate()

    def deactivate(self):
        self.image = assets.img("watering_can_outlined.png")
        self.can_particle_system.deactivate()
        self.amount = 0
        self.active = False
        self.pouring = False
        pygame.mixer.Sound.stop(assets.sfx('water_can.mp3'))
        pygame.mouse.set_visible(True)

    def update(self,dt):
        if self.active and self.pouring:
            self.can_particle_system.update(dt)
            self.model.water_pool += self.rate
            if self.amount < 0:
                self.amount = 0
                self.deactivate()
            else:
                self.amount -= self.rate

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEBUTTONDOWN:
            self.image = assets.img("watering_can_outlined_tilted.png")
            self.pouring = True
            self.can_particle_system.activate()
            pygame.mixer.Sound.play(assets.sfx('water_can.mp3', 0.05), -1)
        if e.type == MOUSEBUTTONUP:
            self.image = assets.img("watering_can_outlined.png")
            self.can_particle_system.deactivate()
            pygame.mixer.Sound.stop(assets.sfx('water_can.mp3', 0.05))
            self.pouring = False
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x,y)
            self.can_particle_system.spawn_box = Rect(x, y + 100, 0, 0)

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, self.pos)
            self.can_particle_system.draw(screen)