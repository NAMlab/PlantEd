from utils.animation import Animation
import random
from data import assets
import math
import pygame
import numpy as np
import config

class Bee():
    def __init__(self, pos, bounding_rect, images, camera, callback, image=None, speed=3):
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.images = images
        self.camera = camera
        self.callback = callback
        self.animation = Animation(self.images, 0.5)
        self.speed = speed
        self.rect = self.images[0].get_rect()
        self.dir = (0,0)
        self.target = None
        self.pollinating = False
        self.timer = 0
        self.max_timer = 10
        self.pollinating_label = config.BIG_FONT.render("Pollinating...", True, config.BLACK)
        self.set_random_direction()

    def update(self,dt):
        if self.pollinating:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0
                self.pollinating = False
                self.target = None
                self.set_random_direction()
                self.speed = 3
        if random.random() > 0.999:
            self.set_random_direction()
        self.move(dt)
        if self.animation:
            self.animation.update(dt)


    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            #print(self.get_rect(),pygame.mouse.get_pos(),self.camera.offset_y)
            #if self.bounding_rect.collidepoint(pygame.mouse.get_pos()):
            if self.get_rect().collidepoint(pygame.mouse.get_pos()):
                self.set_random_direction()
                self.speed = 5
                assets.sfx("bug_click_sound/bug_squeek_{}.mp3".format(random.randint(0,2))).play()


    def set_random_direction(self):
        self.dir = (random.random() - 0.5, random.random() - 0.5)

    def get_rect(self):
        return pygame.Rect(self.pos[0]-self.rect[2]/2,self.pos[1]-self.rect[3]/2+self.camera.offset_y,self.rect[2],self.rect[3])

    def start_pollinating(self):
        if not self.pollinating:
            self.speed = 0
            self.pollinating = True
            self.timer = self.max_timer

    def move(self, dt):
        self.check_boundaries()
        self.pos = (self.pos[0]+self.dir[0]*self.speed,self.pos[1]-self.dir[1]*self.speed)
        if self.target is not None:
            if abs((self.target[0]-self.pos[0]) + (self.target[1]-self.pos[1])) < 100 and not self.pollinating:
                self.speed = 2
                if abs((self.target[0] - self.pos[0]) + (self.target[1] - self.pos[1])) < 5:
                    self.start_pollinating()
                    self.callback()

    def target_flower(self, flower_pos):
        x_dist = flower_pos[0]-self.pos[0]
        y_dist = flower_pos[1]-self.pos[1]
        max_distance = max(x_dist, y_dist)
        self.dir = (x_dist/abs(max_distance),-1* y_dist/abs(max_distance))
        self.target = flower_pos

    def check_boundaries(self):
        if self.pos[0] < self.bounding_rect[0]:
            self.dir = (self.dir[0]*-1,self.dir[1])
        if self.pos[0] > self.bounding_rect[0]+self.bounding_rect[2]:
            self.dir = (self.dir[0]*-1,self.dir[1])
        if self.pos[1] < self.bounding_rect[1]:
            self.dir = (self.dir[0],self.dir[1]*-1)
        if self.pos[1] > self.bounding_rect[1] + self.bounding_rect[3]:
            self.dir = (self.dir[0],self.dir[1]*-1)

    def draw(self, screen):
        #pygame.draw.rect(screen,config.WHITE,self.get_rect(),2)
        screen.blit(self.animation.image, (int(self.pos[0]-self.rect[2]/2),int(self.pos[1]-self.rect[3]/2)))
        if self.target is not None:
            pygame.draw.line(screen, config.WHITE, self.pos, self.target, width=3)

        if self.pollinating:
            pygame.draw.rect(screen, config.WHITE_TRANSPARENT, (self.pos[0],self.pos[1]-50,self.pollinating_label.get_width()+10,self.pollinating_label.get_height()+10),border_radius=3)
            width = (1-self.timer/self.max_timer)*self.pollinating_label.get_width()+10
            pygame.draw.rect(screen, config.WHITE, (self.pos[0],self.pos[1]-50,width,self.pollinating_label.get_height()+10),border_radius=3)
            screen.blit(self.pollinating_label, (self.pos[0]+5,self.pos[1]-45))