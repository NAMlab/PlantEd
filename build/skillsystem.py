import pygame
from gameobjects.plant import Plant
import config
from utils.button import RadioButton
from data import assets
from utils.button import Button

class Skill:
    def __init__(self, image_grey, image, pos=(0,0), callback=None, active=False, cost=1, offset=(0,0), post_hover_message=None, message=None):
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
        self.skills = []
        self.post_hover_message = post_hover_message
        self.message = message

    def activate(self):
        self.active = True
        self.image = self.image_skilled

    def handle_event(self, e):
        if self.active: #active = skilled already
            return
        if not self.visible:
            return
        if e.type == pygame.MOUSEMOTION and not self.selected:
            pos = (e.pos[0]-self.offset[0], e.pos[1]-self.offset[1])
            if self.get_rect().collidepoint(pos):
                self.hover = True
                if self.post_hover_message is not None:
                    self.post_hover_message(self.message)
            else:
                if self.post_hover_message is not None and self.hover:
                    self.post_hover_message()
                self.hover = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            pos = (e.pos[0] - self.offset[0], e.pos[1] - self.offset[1])
            if self.get_rect().collidepoint(pos):
                if self.selected:
                    self.selected = False
                    self.hover = True
                else:
                    for skill in self.skills:
                        skill.selected = False
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
    def __init__(self, pos, plant, leaf_skills=[], stem_skills=[], root_skills=[], starch_skills=[], cols=2, post_hover_message=None):
        #performance improve test
        self.s = s = pygame.Surface((200, 290), pygame.SRCALPHA)
        self.current_cost_label = config.BIG_FONT.render("0", False, (0, 0, 0))
        self.pos = pos
        self.post_hover_message = post_hover_message
        self.rect = (pos[0],pos[1],200,245)
        self.plant = plant
        self.margin = 20
        self.cols = cols
        self.skills = [leaf_skills,
                       stem_skills,
                       root_skills,
                       starch_skills]
        for skills in self.skills:
            for skill in skills:
                skill.skills = skills
        self.active_skills = 0
        self.current_cost = 0
        self.skills_label = config.FONT.render("Leaf Upgrades",False,config.BLACK)

        self.buy_button = Button(self.rect[2]-self.margin-64,
                                 self.rect[3]-30,64,64,[self.buy],config.FONT,"Buy", offset=self.pos)
        self.green_thumbs_icon = assets.img("green_thumb.PNG", (26, 26))
        self.init_layout()
        self.set_target(0)

        #target_buttons[0].button_down = True

    def update(self, dt):
        if self.active_skills+1 != self.plant.target_organ.type:
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

    def get_skills(self, organ_type):
        for i in range(0,len(self.plant.organs)):
            if self.plant.organs[i].type == organ_type:
                return self.skills[i]
        if organ_type == self.plant.STARCH:
            return self.skills[3]

    def update_current_cost(self):
        self.current_cost = 0
        for skill in self.skills[self.active_skills]:
            if skill.selected:
                self.current_cost += skill.cost
                self.current_cost_label = config.BIG_FONT.render("{}".format(self.current_cost), False, (0, 0, 0))

    def handle_event(self,e):
        self.buy_button.handle_event(e)
        for skill in self.skills[self.active_skills]:
            skill.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.update_current_cost()

    def set_target(self, skills_id):
        for skill in self.skills[self.active_skills]:
            skill.visible = False
            skill.selected = False
        self.active_skills = skills_id
        for skill in self.skills[self.active_skills]:
            skill.visible = True
        self.update_current_cost()

    def buy(self):
        for skill in self.skills[self.active_skills]:
            if skill.selected:
                if self.plant.upgrade_points - skill.cost >= 0:
                    self.plant.upgrade_points -= skill.cost
                    if skill.callback is not None:
                        skill.callback()
                    skill.selected = False
                    skill.activate()
                    self.plant.target_organ.skills.append(skill)
                    self.update_current_cost()
                    #cost = config.FONT.render("{}".format(self.current_cost), False, (255, 255, 255))
                    #self.animations.append(LabelAnimation(cost, item.cost, 120, self.cost_label_pos))
        self.update_current_cost()

    def draw(self, screen):
        pygame.draw.rect(self.s,config.WHITE,(0,0,self.rect[2],40),border_radius=3)
        self.s.blit(self.skills_label,(self.rect[2]/2-self.skills_label.get_width()/2,0))
        rect = (0,45,self.rect[2],self.rect[3])
        pygame.draw.rect(self.s,config.WHITE_TRANSPARENT,rect,border_radius=3)
        #draw shoplike rect and buy button, also draw all skills, but first layout stuff
        for skill in self.skills[self.active_skills]:
            skill.draw(self.s)
        self.buy_button.draw(self.s)
        self.s.blit(self.green_thumbs_icon, (70, self.rect[3]-self.margin))
        self.s.blit(self.current_cost_label, (50, self.rect[3]-self.margin))
        screen.blit(self.s, (self.pos[0],self.pos[1]))

    def init_layout(self):
        for i in range(0,len(self.skills[0])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin/2) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[0][i].pos = (x,y+45)
            self.skills[0][i].offset = self.pos
        for i in range(0,len(self.skills[1])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin/2) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[1][i].pos = (x,y+45)
            self.skills[1][i].offset = self.pos
        for i in range(0,len(self.skills[2])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin/2) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[2][i].pos = (x,y+45)
            self.skills[2][i].offset = self.pos
        for i in range(0,len(self.skills[3])):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin/2) * int(i/2)) # 10 for first, every row + 32 + margin
            self.skills[3][i].pos = (x,y+45)
            self.skills[3][i].offset = self.pos