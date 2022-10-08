import pygame
from data import assets
from utils.particle import ParticleSystem
from pygame import Rect
import config
from pygame.locals import *
from fba import dynamic_model


class Spraycan:
    def __init__(self, pos, model, amount, cost=1): # take from config
        self.pos = pos
        self.model = model
        self.image = assets.img("spraycan.PNG")
        self.default_amount = amount
        self.amount = amount
        self.max_amount = amount
        self.cost = cost
        self.active = False
        self.can_particle_system = ParticleSystem(100, spawn_box=Rect(self.pos[0], self.pos[1], 0, 0), lifetime=13,
                                                  color=config.PURPLE,apply_gravity=True,speed=[-10,3],
                                                  spread=[3, 3], active=False, size=14, size_over_lifetime=True, once=True)

    def activate(self, amount=None):
        self.amount = self.default_amount if amount is None else amount
        self.pos = pygame.mouse.get_pos()
        self.active = True
        pygame.mouse.set_visible(False)
        self.can_particle_system.spawn_box = Rect(self.pos[0], self.pos[1], 0, 0)

    def deactivate(self):
        self.image = assets.img("spraycan.PNG")
        self.amount = 0
        self.active = False
        pygame.mixer.Sound.stop(assets.sfx('water_can.mp3'))
        pygame.mouse.set_visible(True)

    def update(self,dt):
        self.can_particle_system.update(dt)
        if self.active:
            if self.amount <= 0:
                self.amount = 0
                self.deactivate()

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEBUTTONDOWN:
            self.image = assets.img("spraycan_active.PNG")
            self.can_particle_system.activate()
            pygame.mixer.Sound.play(assets.sfx('spraycan.mp3', 0.3))
        if e.type == MOUSEBUTTONUP:
            self.amount -= 1
            self.image = assets.img("spraycan.PNG")
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x,y)
            self.can_particle_system.spawn_box = Rect(x, y, 0, 0)

    def draw(self, screen):
        self.can_particle_system.draw(screen)
        if self.active:
            w = self.image.get_width()
            line_width = w/self.max_amount
            for i in range(0,self.amount):
                pygame.draw.line(screen,(0,0,0),(self.pos[0]+i*line_width,self.pos[1]),(self.pos[0]+(i+1)*line_width,self.pos[1]),width=5)
                pygame.draw.line(screen,config.WHITE,(self.pos[0]+i*line_width+1,self.pos[1]),(self.pos[0]+(i+1)*line_width+1,self.pos[1]),width=3)
            screen.blit(self.image, self.pos)
