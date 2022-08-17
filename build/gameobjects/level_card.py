#from game import SceneMananger, CustomScene, DevScene, DefaultGameScene
import pygame
import config
from pygame.locals import *


class Card:
    def __init__(self, pos, image, name, callback=None, callback_var=None, increase=0.3, score=0, keywords="", frames=15, margin=10):
        self.pos = pos
        # images should be 24 iterations to increase an image
        self.image = image
        self.callback = callback
        self.callback_var = callback_var
        self.increase = increase
        self.score = score
        self.keywords = keywords
        self.margin = margin

        self.name_label = config.BIGGER_FONT.render("{}".format(name),True,config.WHITE)
        self.score_label = config.BIGGER_FONT.render("Score: {}".format(score),True,config.WHITE)
        self.keyword_labels = config.BIG_FONT.render("{}".format(keywords), True, config.WHITE)

        self.images = self.generate_images(frames)
        self.image_index = 0

        self.focus_timer = 0 # frames
        self.focus_duration = 15
        self.focus = False

    def update(self, dt):
        if self.focus:
            if self.focus_timer > 1:
                self.focus_timer = self.focus_timer - 1
                self.image_index = int(
                    (self.focus_duration - self.focus_timer) / self.focus_duration * (len(self.images) - 1))
        elif self.focus_timer > 0 and self.focus_timer < self.focus_duration:
            self.focus_timer += 1
            self.image_index = int(
                (self.focus_duration - self.focus_timer) / self.focus_duration * (len(self.images) - 1))
        else:
            self.focus_timer = 0
            self.image_index = 0





    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            if self.get_rect().collidepoint(pos):
                if not self.focus:
                    self.focus = True
                    self.focus_timer = self.focus_duration
            else:
                self.focus = False
                self.image_index = 0
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.focus:
                if self.callback:
                    self.callback(self.callback_var())

    def draw(self, screen):
        size = self.images[self.image_index].get_size()
        offset_x = size[0]/2
        offset_y = size[1]/2
        screen.blit(self.images[self.image_index], (self.pos[0]-offset_x,self.pos[1]-offset_y))

    def get_rect(self):
        rect = self.images[self.image_index].get_rect()
        x_offset = rect[2]/2
        y_offset = rect[3]/2
        return pygame.Rect(self.pos[0]-x_offset,self.pos[1]-y_offset,rect[2],rect[3])

    def generate_images(self, frames):
        images = []
        w,h = self.image.get_size()
        w+=8
        h+=8

        h_card = h + self.score_label.get_height() + self.keyword_labels.get_height() + self.margin*3
        w_decrement = int((w * self.increase) / frames)
        h_decrement = int((h_card * self.increase) / frames)

        surface = pygame.Surface((w, h_card), pygame.SRCALPHA)
        pygame.draw.rect(surface,config.BLACK,(0,0,w,h_card),border_radius=5)
        pygame.draw.rect(surface,config.WHITE,(0,0,w,h_card),width=2,border_radius=5)
        surface.blit(self.image, (4, 4))
        pygame.draw.rect(surface,config.BLACK,(self.margin-2,self.margin-2,self.name_label.get_width()+4,
                                                          self.name_label.get_height()+4),border_radius=2)
        surface.blit(self.name_label, (self.margin, self.margin))
        surface.blit(self.score_label, (self.margin, h + self.margin))
        surface.blit(self.keyword_labels, (self.margin, h + self.margin*2 + self.score_label.get_height()))

        for i in range(0,frames):
            tmp_s = surface.copy()
            tmp_s = pygame.transform.scale(tmp_s, (w -w_decrement * i, h_card -h_decrement * i))
            images.insert(0,tmp_s)
        return images

