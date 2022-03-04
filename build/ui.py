import pygame

'''
UI: set up all UI elements, update them, link them to functions
@param  scale:size UI dynamically
        Components may differ from level to level --> should be set by file
            Dict active groups for: Organs plsu Sliders, Starch deposit, Organ Detail
'''


class UI:
    def __init__(self, scale):
        self.sliders = []
        self.sprites = pygame.sprite.Group()
        self.button_sprites = pygame.sprite.Group()
        self.particle_systems = []

    def update(self, dt):
        pass

    def draw(self, screen):
        pass