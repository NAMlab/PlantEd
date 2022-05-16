import config
import pygame
from utils.particle import ParticleSystem
from pygame import Rect

class Root_Item:
    def __init__(self, callback, plant, cost=1): # take from config
        self.plant = plant
        self.dir = [0,0]
        self.cost = cost
        self.callback = callback
        self.active = False
        self.validation_rect = Rect(0,config.SCREEN_HEIGHT-200,config.SCREEN_WIDTH,200)
        self.particle_system = ParticleSystem(100, spawn_box=Rect(self.plant.x, self.plant.y+45, 0, 0), lifetime=8,
                                                  color=config.WHITE,apply_gravity=False,speed=[0,0],
                                                  spread=[20, 20], active=False, once=True)

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if self.active:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.validation_rect.collidepoint(mouse_pos):
                    self.callback(pygame.mouse.get_pos())
                    self.deactivate()
                    self.particle_system.activate()

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            mouse_pos = pygame.mouse.get_pos()
            if self.validation_rect.collidepoint(mouse_pos):
                pygame.draw.line(screen, config.WHITE, (self.plant.x,self.plant.y+45),mouse_pos,3)
                pygame.draw.circle(screen, config.WHITE, mouse_pos, 3)
            else:
                pygame.draw.line(screen, config.GRAY, (self.plant.x,self.plant.y+45),mouse_pos,3)
                pygame.draw.circle(screen, config.GRAY, mouse_pos, 3)
