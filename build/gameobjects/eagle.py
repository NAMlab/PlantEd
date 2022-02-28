import pygame
import random
from utils.button import Button
from utils.particle import ParticleSystem
from pygame import Rect
# spawns a button or interactable. If the player reacts fast, nothing happens. Else spawn hazard
class QuickTimeEvent:
    def __init__(self, pos, react_time, eagle, image, entities, quick_sound=None, font=None, text=None):
        self.eagle = eagle
        self.active = True
        self.pos = eagle.get_button_pos()
        self.react_time = react_time * 60 # ugly for 60fps, in seconds
        #spawn button, callback for deactivate
        self.button = Button( self.pos[0], self.pos[1], image.get_width(), image.get_height(), [self.deactivate], image=image, font=font, text=text)
        if quick_sound:
            pygame.mixer.Sound.play(quick_sound)
        self.entities = entities

    def handle_event(self, e):
        if self.active:
            self.button.handle_event(e)

    def update(self):
        if self.active:
            if self.react_time <= 0 and not self.eagle.active:
                self.eagle.activate()
                self.active = False
            else:
                self.react_time -= 1

    def deactivate(self):
        self.entities.remove(self.eagle)
        self.active = False


    def draw(self, screen):
        if not self.active:
            return
        screen.blit(self.button.image, (self.button.rect[0],self.button.rect[1]))


# eagles are generated and destroyed, they are no supposed to live long
class Eagle:
    def __init__(self, screen_width, screen_height, target_leaf, animation=None, speed=1, action_sound=None, callback=None):
        self.active = False
        self.speed = speed
        self.animation = animation
        self.width = animation.image.get_width()
        self.x = screen_width
        self.y = target_leaf["y"]-self.width/2
        self.callback = callback
        self.target_leaf = target_leaf
        self.direction = (-1,0)
        self.action_sound = action_sound
        self.eaten = False

    def update(self):
        if self.active:
            self.animation.update()
            self.fly()

    def draw(self, screen):
        if self.active:
            screen.blit(self.animation.image,(self.x,self.y))

    def activate(self):
        self.active = True
        if self.action_sound:
            pygame.mixer.Sound.play(self.action_sound)

    def get_button_pos(self):
        return (self.x-128,self.y)

    def fly(self):
        self.x += self.direction[0]*self.speed
        if self.x < 0-self.width:
            self.active = False
        if Rect(self.x, self.y, self.width, self.width).collidepoint(self.target_leaf["x"],self.target_leaf["y"]) and not self.eaten:
            self.callback(self.target_leaf)
            self.eaten = True