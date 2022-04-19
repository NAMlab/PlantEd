import pygame
from gameobjects.plant import Plant
import config
from utils.button import RadioButton
from data import assets

class Skill:
    def __init__(self, image_grey, image, pos=(0,0), callback=None, active=False, cost=0):
        self.image_normal = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.image_hover = pygame.Surface((64,64),pygame.SRCALPHA)
        self.image_selected = pygame.Surface((64, 64), pygame.SRCALPHA)
        # only image with color, should be
        self.image_skilled = pygame.Surface((64,64),pygame.SRCALPHA)

        self.image_normal.blit(image_grey, (0, 0))
        self.image_hover.blit(image_grey, (0, 0))
        self.image_selected.blit(image_grey, (0, 0))
        self.image_skilled.blit(image,(0,0))


        pygame.draw.rect(self.image_hover, config.WHITE, self.image_hover.get_rect(), 3)
        pygame.draw.rect(self.image_selected, config.WHITE_TRANSPARENT, self.image_selected.get_rect(), 3)

        self.image = self.image_normal

        self.pos = pos
        self.callback = callback
        self.active = active    #active in this case means skilled/bought
        self.cost = cost
        self.selected = False
        self.visible = False

    def handle_event(self, e):
        if self.active:
            return
        if not self.visible:
            return
        mouse_pos = pygame.mouse.get_pos()
        if e.type == pygame.MOUSEMOTION:
            if self.get_rect().collidepoint(mouse_pos):
                self.image = self.image_hover
            else:
                self.image = self.image_normal
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.get_rect().collidepoint(mouse_pos):
                if self.selected:
                    self.selected = False
                    self.image = self.image_hover
                else:
                    self.selected = True
                    self.image = self.image_selected

    def draw(self, screen):
        if self.visible:
            screen.blit(self.image, self.pos)

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
        self.button_sprites = pygame.sprite.Group()
        self.leaf_skills = leaf_skills
        self.stem_skills = stem_skills
        self.root_skills = root_skills
        self.starch_skills = starch_skills

        # target organ = int, for convenience
        self.target_organ = Plant.LEAF

        # init organ selection radio buttons
        target_buttons = [RadioButton(pos[0]+10, pos[1]+55, 32, 32, [self.target_leaf],image=assets.img("leaf_small.png",(32,32))),
                         RadioButton(pos[0]+60, pos[1]+55, 32, 32, [self.target_stem], image=assets.img("stem_small.png",(32,32))),
                         RadioButton(pos[0]+110, pos[1]+55, 32, 32, [self.target_root], image=assets.img("roots_small.png",(32,32))),
                         RadioButton(pos[0]+160, pos[1]+55, 32, 32, [self.target_starch], image=assets.img("starch.png",(32,32)))]
        for button in target_buttons:
            button.setRadioButtons(target_buttons)
            self.button_sprites.add(button)


        self.init_layout()

        target_buttons[0].button_down = True

    def init_layout(self):
        for i in range(0,len(self.leaf_skills)):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.leaf_skills[i].pos = (x+self.pos[0],y+self.pos[1]+45+40)
        for i in range(0,len(self.stem_skills)):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.stem_skills[i].pos = (x+self.pos[0],y+self.pos[1]+45+40)
        for i in range(0,len(self.root_skills)):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.root_skills[i].pos = (x+self.pos[0],y+self.pos[1]+45+40)
        for i in range(0,len(self.starch_skills)):
            x = self.margin + ((64 + self.margin*2) * (i%self.cols)) # 10 for left, 20 + img_width for right
            y = self.margin + ((64 + self.margin) * int(i/2)) # 10 for first, every row + 32 + margin
            self.starch_skills[i].pos = (x+self.pos[0],y+self.pos[1]+45+40)

    def handle_event(self,e):
        for button in self.button_sprites:
            # all button_sprites handle their events
            button.handle_event(e)
        for skill in self.leaf_skills:
            skill.handle_event(e)
        for skill in self.stem_skills:
            skill.handle_event(e)
        for skill in self.root_skills:
            skill.handle_event(e)
        for skill in self.starch_skills:
            skill.handle_event(e)

    def deactivate_all(self):
        for skill in self.leaf_skills:
            skill.visible=False
        for skill in self.stem_skills:
            skill.visible=False
        for skill in self.root_skills:
            skill.visible=False
        for skill in self.starch_skills:
            skill.visible=False

    def target_leaf(self):
        self.deactivate_all()
        self.target_organ = Plant.LEAF
        for skill in self.leaf_skills:
            skill.visible=True
    def target_stem(self):
        self.deactivate_all()
        self.target_organ = Plant.STEM
        for skill in self.stem_skills:
            skill.visible=True
    def target_root(self):
        self.deactivate_all()
        self.target_organ = Plant.ROOTS
        for skill in self.root_skills:
            skill.visible=True
    def target_starch(self):
        self.deactivate_all()
        self.target_organ = Plant.STARCH
        for skill in self.starch_skills:
            skill.visible=True

    def draw(self, screen):
        skills_label = config.FONT.render("Skills",False,config.BLACK)
        pygame.draw.rect(screen,config.WHITE,(self.rect[0],self.rect[1],self.rect[2],40),border_radius=3)
        screen.blit(skills_label,(self.rect[0]+self.rect[2]/2-skills_label.get_width()/2,self.rect[1]))

        rect = (self.rect[0],self.rect[1]+45,self.rect[2],self.rect[3])
        pygame.draw.rect(screen,config.WHITE_TRANSPARENT,rect,border_radius=3)

        self.button_sprites.draw(screen)
        #draw shoplike rect and buy button, also draw all skills, but first layout stuff
        if self.target_organ == Plant.LEAF:
            for skill in self.leaf_skills:
                skill.draw(screen)
        if self.target_organ == Plant.STEM:
            for skill in self.stem_skills:
                skill.draw(screen)
        if self.target_organ == Plant.ROOTS:
            for skill in self.root_skills:
                skill.draw(screen)
        if self.target_organ == Plant.STARCH:
            for skill in self.starch_skills:
                skill.draw(screen)