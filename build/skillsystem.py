import pygame
from gameobjects.plant import Plant
import config
from utils.button import RadioButton
from data import assets

class Skill:
    def __init__(self, image_grey, image, pos=(0,0), callback=None, active=False, cost=0):
        self.image_normal = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.image_skilled = pygame.Surface((64,64),pygame.SRCALPHA)
        self.image_normal.blit(image_grey, (0, 0))
        self.image_skilled.blit(image,(0,0))
        self.image = self.image_normal
        self.pos = pos
        self.callback = callback
        self.active = active    #active in this case means skilled/bought
        self.cost = cost
        self.selected = False
        self.visible = False
        self.hover = False

    def handle_event(self, e):
        if self.active:
            return
        if not self.visible:
            return

        mouse_pos = pygame.mouse.get_pos()
        if e.type == pygame.MOUSEMOTION and not self.selected:
            if self.get_rect().collidepoint(mouse_pos):
                self.hover = True
            else:
                self.hover = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(mouse_pos):
                if self.selected:
                    self.selected = False
                    self.hover = True
                else:
                    self.selected = True
                    self.hover = False

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, self.pos)
            if self.selected:
                pygame.draw.rect(screen, config.WHITE, self.get_rect(), width=3)
            elif self.hover:
                pygame.draw.rect(screen, config.GREY_TRANSPARENT, self.get_rect(), width=3)

    def get_rect(self):
        rect = self.image.get_rect()
        return pygame.Rect(rect[0]+self.pos[0], rect[1]+self.pos[1], rect[2], rect[3])


class Skill_System:
    def __init__(self, pos, plant, leaf_skills=[], stem_skills=[], root_skills=[], starch_skills=[], cols=2):
        self.pos = pos
        self.rect = (pos[0],pos[1],200,220)
        self.plant = plant
        self.margin = 20
        self.cols = cols
        self.skills = [leaf_skills,
                       stem_skills,
                       root_skills,
                       starch_skills]
        self.active_skills = 0
        self.skills_label = config.FONT.render("Leaf Upgrades",False,config.BLACK)

        self.init_layout()
        self.set_target(0)

        #target_buttons[0].button_down = True

    def update(self, dt):
        if self.active_skills+1 != self.plant.target_organ:
            if self.plant.target_organ.type == self.plant.LEAF:
                self.set_target(0)
                self.skills_label = config.BIG_FONT.render("Leaf Upgrades", True, config.BLACK)
            if self.plant.target_organ.type == self.plant.STEM:
                self.set_target(1)
                self.skills_label = config.BIG_FONT.render("Stem Upgrades", True, config.BLACK)
            if self.plant.target_organ.type == self.plant.ROOTS:
                self.set_target(2)
                self.skills_label = config.BIG_FONT.render("Root Upgrades", True, config.BLACK)
            if self.plant.target_organ.type == self.plant.STARCH:
                self.set_target(3)
                self.skills_label = config.BIG_FONT.render("Starch Upgrades", True, config.BLACK)

    def handle_event(self,e):
        for skill in self.skills[self.active_skills]:
            skill.handle_event(e)

    def set_target(self, skills_id):
        for skill in self.skills[self.active_skills]:
            skill.visible = False
        self.active_skills = skills_id
        for skill in self.skills[self.active_skills]:
            skill.visible = True

    def draw(self, screen):
        s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s,config.WHITE,(self.rect[0],self.rect[1],self.rect[2],40),border_radius=3)
        s.blit(self.skills_label,(self.rect[0]+self.rect[2]/2-self.skills_label.get_width()/2,self.rect[1]))
        rect = (self.rect[0],self.rect[1]+45,self.rect[2],self.rect[3])
        pygame.draw.rect(s,config.WHITE_TRANSPARENT,rect,border_radius=3)
        #draw shoplike rect and buy button, also draw all skills, but first layout stuff
        for skill in self.skills[self.active_skills]:
            skill.draw(s)
        screen.blit(s, (0,0))

    def init_layout(self):
        for i in range(0,len(self.skills[0])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[0][i].pos = (x+self.pos[0],y+self.pos[1]+45)
        for i in range(0,len(self.skills[1])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[1][i].pos = (x+self.pos[0],y+self.pos[1]+45)
        for i in range(0,len(self.skills[2])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[2][i].pos = (x+self.pos[0],y+self.pos[1]+45)
        for i in range(0,len(self.skills[3])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[3][i].pos = (x+self.pos[0],y+self.pos[1]+45)