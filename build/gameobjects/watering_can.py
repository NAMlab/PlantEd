import pygame
from data import assets
from utils.particle import ParticleSystem
from pygame import Rect
import config
from utils.gametime import GameTime
from pygame.locals import *
from fba import dynamic_model


class Watering_can:
    def __init__(self, pos, model=None, water_grid=None, amount=None, rate=3000000, cost=1, active=False, callback=None): # take from config
        self.gametime = GameTime.instance()
        self.pos = (pos[0]-20,pos[1]-120)
        self.model = model
        self.water_grid = water_grid
        self.image = assets.img("watering_can.png",(214,147))
        self.default_amount = rate*3 #default gamespeed 3s
        self.amount = amount if amount else self.default_amount
        self.rate = rate
        self.cost = cost
        self.active = active
        self.pouring = False
        self.callback = callback
        self.rect = Rect(self.pos[0],self.pos[1],20,20)
        self.can_particle_system = ParticleSystem(290, spawn_box=self.rect, lifetime=12,
                                                  color=config.BLUE,apply_gravity=10,speed=[-40, 0],
                                                  spread=[20, 20], active=False)

    def activate(self, amount=None):
        self.pos = pygame.mouse.get_pos()
        self.active = True
        self.amount = self.default_amount if not amount else amount
        pygame.mouse.set_visible(False)
        self.can_particle_system.spawn_box = self.rect
        self.can_particle_system.activate()

    def deactivate(self):
        self.image = assets.img("watering_can.png",(214,147))
        self.can_particle_system.deactivate()
        self.amount = 0
        self.active = False
        self.pouring = False
        pygame.mixer.Sound.stop(assets.sfx('water_can.mp3'))
        pygame.mouse.set_visible(True)

    def update(self,dt):
        if self.active and self.pouring:
            self.can_particle_system.update(dt)
            if self.water_grid:
                #self.model.water_pool += self.rate
                self.water_grid.pour(self.rate,dt,self.pos)
            if self.callback:
                self.callback(self.rate)
            if self.amount < 0:
                self.amount = 0
                self.deactivate()
            else:
                self.amount -= self.rate * dt

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEBUTTONDOWN:
            self.image = assets.img("watering_can_tilted.png",(182,148))
            self.pouring = True
            self.can_particle_system.activate()
            pygame.mixer.Sound.play(assets.sfx('water_can.mp3', 0.05), -1)
        if e.type == MOUSEBUTTONUP:
            self.image = assets.img("watering_can.png",(214,147))
            self.can_particle_system.deactivate()
            pygame.mixer.Sound.stop(assets.sfx('water_can.mp3', 0.05))
            self.pouring = False
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x,y)
            self.rect = Rect(self.pos[0], self.pos[1]+100, 20, 20)
            self.can_particle_system.spawn_box = self.rect

    def draw(self, screen):
        if self.active:
            screen.blit(self.image, self.pos)
            self.can_particle_system.draw(screen)