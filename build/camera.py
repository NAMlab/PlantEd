import pygame

class Camera:
    def __init__(self):
        self.offset_y = 100

    def render(self, screen_high, screen):
        screen.blit(screen_high,(0,self.offset_y))

