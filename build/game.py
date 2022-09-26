import ctypes
import pygame
from pygame.locals import *
import numpy as np
from itertools import repeat
import analysis.scoring
from data import assets
import math
from analysis.logger import Log
from gameobjects.plant import Plant
from utils.button import Button, RadioButton, Slider, SliderGroup, ToggleButton, Textbox
from utils.particle import ParticleSystem, PointParticleSystem
from utils.animation import OneShotAnimation, Animation
import os, sys
from utils.tool_tip import ToolTipManager
from weather import Environment
from fba.dynamic_model import DynamicModel, BIOMASS, STARCH_OUT
from gameobjects.eagle import Eagle, QuickTimeEvent
import config
from utils.gametime import GameTime
from datetime import datetime
from utils.spline import Beziere
from gameobjects.watering_can import Watering_can
from gameobjects.blue_grain import Blue_grain
from gameobjects.shop import Shop, Shop_Item
from gameobjects.bug import Bug
from ui import UI
from camera import Camera
import random
from skillsystem import Skill_System, Skill
from utils.LSystem import LSystem, Letter
from analysis import scoring
from gameobjects.water_reservoir import Water_Reservoir, Water_Grid, Base_water
from gameobjects.level_card import Card

currentdir = os.path.abspath('..')
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
pygame.init()
ctypes.windll.user32.SetProcessDPIAware()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)
#pygame.display.toggle_fullscreen()
#print(pygame.display.list_modes(depth=0, flags=pygame.FULLSCREEN, display=0))
#screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
#screen_high = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT*2), pygame.DOUBLEBUF)
tmp_screen = pygame.display.set_mode(true_res, pygame.SRCALPHA)
temp_surface = pygame.Surface((1920, 2160), pygame.SRCALPHA)
#screen_high = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT*2), pygame.SRCALPHA)
GROWTH = 24
RECALC = 25
WIN = pygame.USEREVENT+1

# stupid, change dynamically
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
plant_pos = (SCREEN_WIDTH - SCREEN_WIDTH/4, SCREEN_HEIGHT - SCREEN_HEIGHT/5)

GREEN = (19, 155, 23)
BLUE = (75, 75, 200)
SKY_BLUE = (169, 247, 252)

def shake():
    s = -1  # looks unnecessary but maybe cool, int((random.randint(0,1)-0.5)*2)
    for _ in range(0, 3):
        for x in range(0, 20, 5):
            yield (x * -1, x * s)
        for x in range(20, 0, 5):
            yield (x * -1, x * s)
        s *= -1
    while True:
        yield (0, 0)
# Todo
# unittests, dir that contains all tests, one test file for one class, secure class function
# pipenv for git, enable cloners to see all depencies




# seperate high to low level --> less function calls, less clutter
class DevScene(object):
    def __init__(self):
        options = config.load_options(config.OPTIONS_PATH)

        # pygame.mixer.music.load('../assets/background_music.mp3')
        assets.song('background_music.mp3', options["music"])

        # pygame.mixer.music.set_volume(options["music"]/10)
        pygame.mixer.music.play(-1, 0)

        pygame.mouse.set_visible(True)
        self.camera = Camera(offset_y=0)
        self.gametime = GameTime.instance()
        self.log = Log()  # can be turned off
        self.water_grid = Water_Grid(pos=(0, 900))
        # self.water_grid.add_reservoir(Water_Reservoir((500, 1290), 36, 30))
        # self.water_grid.add_reservoir(Water_Reservoir((900, 1190), 36, 25))
        # self.water_grid.add_reservoir(Water_Reservoir((1660, 1310), 36, 40))
        self.model = DynamicModel(self.gametime, self.log)
        self.plant = Plant((config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT - config.SCREEN_HEIGHT / 5), self.model,
                           self.camera, self.water_grid, growth_boost=1)
        self.water_grid.add_base_water(
            Base_water(10, 100, config.SCREEN_WIDTH, config.SCREEN_HEIGHT + 400, config.DARK_BLUE, config.LIGHT_BLUE))
        self.environment = Environment(self.plant, self.model, self.water_grid, 0, 0, self.gametime)
        self.ui = UI(1, self.plant, self.model, self.camera)

        '''example_skills_leaf = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     callback=self.plant.organs[2].set_root_tier,post_hover_message=self.ui.post_hover_message, message="Skill Leaf") for i in range(0,4)]
        example_skills_stem = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Stem") for i in range(0,2)]
        example_skills_root = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Root") for i in range(0,2)]
        example_skills_starch = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                       post_hover_message=self.ui.post_hover_message, message="Skill Starch") for i in range(0,3)]
        self.skill_system = Skill_System((1700,420),self.plant, example_skills_leaf, example_skills_stem, example_skills_root, example_skills_starch)
'''
        self.entities = []
        for i in range(0, 10):
            bug = Bug((190 * random.randint(0, 10), 900 + random.randint(0, 200)),
                      pygame.Rect(0, 900, config.SCREEN_WIDTH, 240),
                      [assets.img("bug_purple/bug_purple_{}.png".format(i)) for i in range(0, 5)], self.camera)
            self.entities.append(bug)
        # self.ui.floating_elements.append(FloatingElement((500,500),Rect(400,400,200,200),image=assets.img("stomata/stomata_open.png")))

        # shop items are to be defined by the level
        add_leaf_item = Shop_Item(assets.img("leaf_small.png", (64, 64)), self.activate_add_leaf,
                                  condition=self.plant.organs[0].check_can_add_leaf,
                                  condition_not_met_message="Level up your stem to buy more leaves",
                                  post_hover_message=self.ui.post_hover_message,
                                  message="Leaves enable your plant to produce energy.")

        self.shop = Shop(Rect(1700, 120, 200, 290), [add_leaf_item], self.model, self.water_grid,
                         self.plant, post_hover_message=self.ui.post_hover_message, active=False)

        self.shop.shop_items.append(Shop_Item(assets.img("root_lateral.png", (64, 64)),
                                            self.shop.root_item.activate,
                                            condition=self.plant.organs[2].check_can_add_root,
                                            condition_not_met_message="Level up your roots to buy more leaves",
                                            post_hover_message=self.ui.post_hover_message,
                                            message="Roots are to improve water and nitrate intake."))

        self.shop.add_shop_item(["watering", "blue_grain"])

        # start plant growth timer
        pygame.time.set_timer(GROWTH, 1000)

    def activate_add_leaf(self):
        # if there are funds, buy a leave will enable leave @ mouse pos until clicked again
        self.plant.organs[0].activate_add_leaf()

    def handle_events(self, events):
        for e in events:
            if e.type == GROWTH:
                leaf_percent = self.plant.organs[0].percentage
                stem_percent = self.plant.organs[1].percentage
                root_percent = self.plant.organs[2].percentage
                starch_percent = self.plant.organ_starch.percentage

                # print(leaf_percent, stem_percent, root_percent, starch_percent)
                self.model.calc_growth_rate(leaf_percent, stem_percent, root_percent, starch_percent)

                leaf_rate, stem_rate, root_rate, starch_rate, starch_intake = self.model.get_rates()
                nitrate_pool = self.model.nitrate_pool
                water_pool = self.water_grid.water_pool
                # self.log.append_log(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool)
                # self.log.append_plant_log(self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                self.log.append_row(leaf_rate, stem_rate, root_rate, starch_rate, self.gametime.get_time(),
                                    self.gametime.GAMESPEED, water_pool, nitrate_pool,
                                    self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass,
                                    self.plant.organ_starch.mass)
                self.plant.update_growth_rates(self.model.get_rates())
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.log.close_file()
                # Todo fix back to menu
                self.model = None
                self.manager.go_to(TitleScene(self.manager))
            if e.type == KEYDOWN and e.key == K_r:
                self.water_grid.raining += 0.05
            if e.type == KEYDOWN and e.key == K_s:
                self.water_grid.raining = 0
            if e.type == WIN:
                if self.log:
                    #self.log.write_log(self.ui.name_label)
                    self.log.close_file()
                scoring.upload_score(self.ui.name_label, self.gametime.get_time())
                self.manager.go_to(CustomScene())
            self.shop.handle_event(e)
            self.ui.handle_event(e)
            self.plant.handle_event(e)
            # self.environment.handle_event(e)
            for entity in self.entities:
                entity.handle_event(e)
            self.camera.handle_event(e)
            # self.skill_system.handle_event(e)

    def update(self, dt):
        # get root grid, water grid
        self.water_grid.set_root_grid(self.plant.organs[2].get_root_grid())
        self.water_grid.actual_drain_rate = self.model.get_actual_water_drain()
        self.water_grid.update(dt)

        self.camera.update(dt)
        for entity in self.entities:
            entity.update(dt)
        self.environment.update(dt)
        self.shop.update(dt)
        self.ui.update(dt)

        # self.skill_system.update(dt)
        self.plant.update(dt, self.model.get_photon_upper())

        if self.plant.seedling.max < self.plant.get_biomass():
            self.shop.active = True

        self.model.update(dt,self.plant.organs[2].mass, self.plant.get_PLA(), max(self.environment.get_sun_intensity(), 0),
                          self.water_grid.max_drain_rate)

    def render(self, screen):
        screen.fill((0, 0, 0))
        self.environment.draw_background(temp_surface)

        for entity in self.entities:
            entity.draw(temp_surface)
        self.plant.draw(temp_surface)

        self.environment.draw_foreground(temp_surface)
        self.water_grid.draw(temp_surface)

        screen.blit(temp_surface, (0, self.camera.offset_y))

        self.ui.draw(screen)
        # self.skill_system.draw(screen)
        self.shop.draw(screen)


class Camera:
    def __init__(self, offset_y):
        self.offset_y = offset_y
        self.target_offset = self.offset_y
        self.speed = 10

    def update(self, dt):
        diff = self.target_offset - self.offset_y
        if diff != 0:
            diff = diff/abs(diff)
            self.offset_y += diff*self.speed

    def handle_event(self, e):
        if e.type == KEYDOWN and e.key == K_w:
            self.target_offset = 0
        if e.type == KEYDOWN and e.key == K_s:
            self.target_offset = -400

    def move_up(self):
        self.target_offset = 0

    def move_down(self):
        self.target_offset = -400

class OptionsScene():
    def __init__(self):
        self.options = config.load_options("options.json")

        self.option_label = config.MENU_TITLE.render("Options",True, config.WHITE)
        self.sound_label = config.MENU_SUBTITLE.render("Sound",True, config.WHITE)
        self.music_label = config.BIGGER_FONT.render("Music",True, config.WHITE)
        self.efects_label = config.BIGGER_FONT.render("Effects",True, config.WHITE)
        self.network_label = config.MENU_SUBTITLE.render("Network",True, config.WHITE)
        self.upload_score_label = config.BIGGER_FONT.render("Upload Score",True, config.WHITE)
        self.name_label = config.MENU_SUBTITLE.render("Name", True, config.WHITE)

        self.label_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

        center_w, center_h = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2

        self.music_slider = Slider((center_w-475, 450, 15, 200), config.FONT, (50, 20), percent=self.options["music"]*100,active=True)
        self.effect_slider = Slider((center_w-175, 450, 15, 200), config.FONT, (50, 20),percent=self.options["effects"]*100, active=True)
        self.upload_score_button = ToggleButton(center_w+300,400,50,50,None,pressed=self.options["upload_score"], cross=True)

        self.back = Button(center_w-200,930,200,50,[self.cancel_return_to_menu],config.BIGGER_FONT, "BACK", config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.apply = Button(center_w+50,930,200,50,[self.return_to_menu],config.BIGGER_FONT, "APPLY", config.LIGHT_GRAY,config.WHITE,border_w=2)

        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add([self.upload_score_button, self.back, self.apply])

        self.textbox = Textbox(center_w+160, 600, 280, 50, config.BIGGER_FONT, self.options["name"],background_color=config.LIGHT_GRAY, textcolor=config.WHITE, highlight_color=config.WHITE)


        self.init_labels()

    def return_to_menu(self):
        config.write_options(config.OPTIONS_PATH, self.get_options())
        self.manager.go_to(TitleScene(self.manager))

    def cancel_return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def init_labels(self):
        center_w, center_h = config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2

        pygame.draw.line(self.label_surface,config.WHITE,(100,900),(1820,900))

        self.label_surface.blit(self.option_label, (center_w-self.option_label.get_width()/2,100))
        self.label_surface.blit(self.sound_label, (center_w-300-self.sound_label.get_width()/2,300))
        self.label_surface.blit(self.music_label, (center_w-450-self.music_label.get_width()/2,400))
        self.label_surface.blit(self.efects_label, (center_w-150-self.efects_label.get_width()/2,400))
        self.label_surface.blit(self.network_label, (center_w+300-self.network_label.get_width()/2,300))
        self.label_surface.blit(self.upload_score_label, (center_w+150-self.upload_score_label.get_width()/2,400))
        self.label_surface.blit(self.name_label, (center_w + 300 - self.name_label.get_width() / 2, 500))

        self.label_surface.blit(assets.img("plant_growth_pod/plant_growth_10.png"),(1300,400))

    def update(self, dt):
        self.textbox.update(dt)

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    self.manager.go_to(TitleScene(self.manager))
            self.music_slider.handle_event(e)
            self.effect_slider.handle_event(e)
            self.upload_score_button.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)
            self.textbox.handle_event(e)

    def get_options(self):
        options = {"music": self.music_slider.get_percentage()/100,
                   "effects": self.effect_slider.get_percentage()/100,
                   "upload_score": self.upload_score_button.button_down,
                   "name": self.textbox.text}
        return options

    def render(self, screen):
        screen.fill(config.LIGHT_GRAY)
        screen.blit(self.label_surface,(0,0))
        self.music_slider.draw(screen)
        self.effect_slider.draw(screen)
        self.button_sprites.draw(screen)
        self.textbox.draw(screen)



class DefaultGameScene(object):
    def __init__(self):
        options = config.load_options(config.OPTIONS_PATH)

        #pygame.mixer.music.load('../assets/background_music.mp3')
        assets.song('background_music.mp3', options["music"])

        #pygame.mixer.music.set_volume(options["music"]/10)
        pygame.mixer.music.play(-1, 0)

        pygame.mouse.set_visible(True)
        self.camera = Camera(offset_y=0)
        self.gametime = GameTime.instance()
        self.log = Log()                        # can be turned off
        self.water_grid = Water_Grid(pos=(0,900))
        #self.water_grid.add_reservoir(Water_Reservoir((500, 1290), 36, 30))
        #self.water_grid.add_reservoir(Water_Reservoir((900, 1190), 36, 25))
        #self.water_grid.add_reservoir(Water_Reservoir((1660, 1310), 36, 40))
        self.model = DynamicModel(self.gametime, self.log)
        self.plant = Plant((config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT - config.SCREEN_HEIGHT/5), self.model, self.camera, self.water_grid)
        self.water_grid.add_base_water(Base_water(10,100,config.SCREEN_WIDTH,config.SCREEN_HEIGHT+400,config.DARK_BLUE, config.LIGHT_BLUE))
        self.environment = Environment(self.plant, self.model, self.water_grid, 0, 0, self.gametime)
        self.ui = UI(1, self.plant, self.model, self.camera)

        '''example_skills_leaf = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     callback=self.plant.organs[2].set_root_tier,post_hover_message=self.ui.post_hover_message, message="Skill Leaf") for i in range(0,4)]
        example_skills_stem = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Stem") for i in range(0,2)]
        example_skills_root = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Root") for i in range(0,2)]
        example_skills_starch = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                       post_hover_message=self.ui.post_hover_message, message="Skill Starch") for i in range(0,3)]
        self.skill_system = Skill_System((1700,420),self.plant, example_skills_leaf, example_skills_stem, example_skills_root, example_skills_starch)
'''
        self.entities = []
        for i in range(0,10):
            bug = Bug((190*random.randint(0,10),900+random.randint(0,200)),pygame.Rect(0,900,config.SCREEN_WIDTH,240),[assets.img("bug_purple/bug_purple_{}.png".format(i)) for i in range(0, 5)], self.camera)
            self.entities.append(bug)
        #self.ui.floating_elements.append(FloatingElement((500,500),Rect(400,400,200,200),image=assets.img("stomata/stomata_open.png")))

        #shop items are to be defined by the level
        add_leaf_item = Shop_Item(assets.img("leaf_small.png",(64,64)),self.activate_add_leaf,
                                  condition=self.plant.organs[0].check_can_add_leaf,
                                  condition_not_met_message="Level up your stem to buy more leaves",
                                  post_hover_message=self.ui.post_hover_message,
                                  message="Leaves enable your plant to produce energy.")

        add_root_item = Shop_Item(assets.img("root_lateral.png",(64,64)),self.plant.organs[2].create_new_root,
                                  condition=self.plant.organs[2].check_can_add_root,
                                  condition_not_met_message="Level up your roots to buy more leaves",
                                  post_hover_message=self.ui.post_hover_message,
                                  message="Roots are to improve water and nitrate intake.")

        self.shop = Shop(Rect(1700, 120, 200, 290), [add_leaf_item, add_root_item], self.model, self.water_grid, self.plant, post_hover_message=self.ui.post_hover_message, active=False)
        self.shop.add_shop_item(["watering","blue_grain"])

        # start plant growth timer
        pygame.time.set_timer(GROWTH, 1000)

    def activate_add_leaf(self):
        # if there are funds, buy a leave will enable leave @ mouse pos until clicked again
        self.plant.organs[0].activate_add_leaf()

    def handle_events(self, events):
        for e in events:
            if e.type == GROWTH:
                leaf_percent = self.plant.organs[0].percentage
                stem_percent = self.plant.organs[1].percentage
                root_percent = self.plant.organs[2].percentage
                starch_percent = self.plant.organ_starch.percentage

                #print(leaf_percent, stem_percent, root_percent, starch_percent)
                self.model.calc_growth_rate(leaf_percent, stem_percent, root_percent, starch_percent)

                leaf_rate, stem_rate, root_rate, starch_rate, starch_intake = self.model.get_rates()
                nitrate_pool, water_pool = self.model.get_pools()
                #self.log.append_log(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool)
                #self.log.append_plant_log(self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                self.log.append_row(leaf_rate, stem_rate, root_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool,
                                    self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                self.plant.grow()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.log.close_file()

                # Todo fix back to menu
                self.model = None
                self.manager.go_to(TitleScene(self.manager))
            if e.type == KEYDOWN and e.key == K_r:
                self.water_grid.raining += 0.05
            if e.type == KEYDOWN and e.key == K_s:
                self.water_grid.raining = 0
            if e.type == WIN:
                if self.log:
                    #self.log.write_log(self.ui.name_label)
                    self.log.close_file()
                scoring.upload_score(self.ui.name_label, self.gametime.get_time())
                self.manager.go_to(CustomScene())
            self.shop.handle_event(e)
            self.ui.handle_event(e)
            self.plant.handle_event(e)
            #self.environment.handle_event(e)
            for entity in self.entities:
                entity.handle_event(e)
            self.camera.handle_event(e)
            #self.skill_system.handle_event(e)

    def update(self, dt):
        # get root grid, water grid
        self.water_grid.set_root_grid(self.plant.organs[2].get_root_grid())
        self.water_grid.actual_drain_rate = self.model.get_actual_water_drain()
        self.water_grid.update(dt)

        self.camera.update(dt)
        for entity in self.entities:
            entity.update(dt)
        self.environment.update(dt)
        self.shop.update(dt)
        self.ui.update(dt)

        #self.skill_system.update(dt)
        self.plant.update(dt, self.model.get_photon_upper())

        if self.plant.seedling.max < self.plant.get_biomass():
            self.shop.active = True

        self.model.update(dt,self.plant.organs[2].mass, self.plant.get_PLA(), max(self.environment.get_sun_intensity(), 0),self.water_grid.max_drain_rate)


    def render(self, screen):
        screen.fill((0,0,0))
        self.environment.draw_background(temp_surface)

        for entity in self.entities:
            entity.draw(temp_surface)
        self.plant.draw(temp_surface)

        self.environment.draw_foreground(temp_surface)
        self.water_grid.draw(temp_surface)

        screen.blit(temp_surface,(0,self.camera.offset_y))

        self.ui.draw(screen)
        #self.skill_system.draw(screen)
        self.shop.draw(screen)

class TitleScene(object):
    def __init__(self, manager=None):
        super(TitleScene, self).__init__()
        self.title = config.MENU_TITLE.render("PlantEd",True,config.WHITE)
        self.center_h = config.SCREEN_HEIGHT/2+100
        self.center_w = config.SCREEN_WIDTH/2
        self.card_0 = Card((self.center_w-260,self.center_h-100),assets.img("menu/gatersleben.JPG",(512,512)), "Gatersleben",
                           callback=manager.go_to, callback_var=DefaultGameScene,keywords="Beginner, Medium Temperatures")
        #self.card_1 = Card((self.center_w,self.center_h-100),assets.img("menu/tutorial.JPG",(512,512)), "Tutorial",
        #                   callback=manager.go_to, callback_var=DevScene,keywords="Beginner, Easy")
        self.card_2 = Card((self.center_w+260,self.center_h-100),assets.img("menu/dev.jpg",(512,512)), "Dev ",
                           callback=manager.go_to, callback_var=DevScene,keywords="Test Stuff")


        self.credit_button = Button(self.center_w-450,930,200,50,[self.go_to_credtis],config.BIGGER_FONT,"CREDTIS",config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.options_button = Button(self.center_w-200,930,200,50,[self.go_to_options],config.BIGGER_FONT, "OPTIONS", config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.scores_button = Button(self.center_w+50,930,200,50,[self.go_to_scores],config.BIGGER_FONT, "SCORES", config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.quit_button = Button(self.center_w+300,930,200,50,[self.quit],config.BIGGER_FONT, "QUIT", config.LIGHT_GRAY,config.WHITE,border_w=2)


        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add([self.quit_button,self.credit_button,self.options_button,self.scores_button])

    def render(self, screen):
        screen.fill(config.LIGHT_GRAY)
        screen.blit(self.title,(self.center_w-self.title.get_width()/2,100))
        self.card_0.draw(screen)
        #self.card_1.draw(screen)
        self.card_2.draw(screen)
        pygame.draw.line(screen,config.WHITE,(100,900),(1820,900))
        self.button_sprites.draw(screen)

    def update(self, dt):
        self.card_0.update(dt)
        #self.card_1.update(dt)
        self.card_2.update(dt)

    def quit(self):
        pygame.quit()
        sys.exit()

    def go_to_options(self):
        self.manager.go_to(OptionsScene())

    def go_to_credtis(self):
        self.manager.go_to(Credits())

    def go_to_scores(self):
        self.manager.go_to(CustomScene())

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.quit()
            self.card_0.handle_event(e)
            #self.card_1.handle_event(e)
            self.card_2.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)
            #self.watering_can.handle_event(e)

class CustomScene(object):
    def __init__(self):
        super(CustomScene, self).__init__()
        self.text1 = config.MENU_TITLE.render('Top Plants', True, (255,255,255))
        #self.text3 = config.BIGGER_FONT.render('> press any key to restart <', True, (255,255,255))

        self.name_txt = config.BIGGER_FONT.render('Name', True, (255,255,255))
        self.score_txt = config.BIGGER_FONT.render('Score', True, (255,255,255))
        self.submit_txt = config.BIGGER_FONT.render('Submit Date', True, (255,255,255))

        self.button_sprites = pygame.sprite.Group()
        self.back = Button(860,930,200,50,[self.return_to_menu],config.BIGGER_FONT, "BACK", config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.button_sprites.add(self.back)

        self.winners = scoring.get_scores()
        self.scores = []
        self.names = []
        self.datetimes = []

        self.winners = sorted(self.winners, key=lambda x: x["score"])

        for winner in self.winners:
            score = self.get_day_time(winner['score'])
            score = config.BIGGER_FONT.render(score, True, (255,255,255))
            self.scores.append(score)
            name = config.BIGGER_FONT.render(winner['name'], True, (255, 255, 255))
            self.names.append(name)
            datetime_added = config.BIGGER_FONT.render(datetime.utcfromtimestamp(winner['datetime_added']).strftime('%d/%m/%Y %H:%M'), True, (255, 255, 255))
            self.datetimes.append(datetime_added)

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def get_day_time(self, ticks):
        day = 1000*60*6
        hour = day/24
        min = hour/60
        second = min/60
        days = str(int(ticks/day))
        hours = str(int((ticks % day) / hour))
        minutes = str(int((ticks % hour) / min))
        return (days +  " Days " + hours + " Hours " + minutes + " Minutes")

    def render(self, screen):
        screen.fill((50, 50, 50))
        screen.blit(self.text1, (SCREEN_WIDTH/2-self.text1.get_width()/2, 100))

        pygame.draw.line(screen, config.WHITE, (100, 300), (1820, 300))

        #screen.blit(self.name_txt, (SCREEN_WIDTH / 4 - self.name_txt.get_width()/2, SCREEN_HEIGHT / 3))
        #screen.blit(self.score_txt, (SCREEN_WIDTH / 2 - self.score_txt.get_width()/2, SCREEN_HEIGHT / 3))
        #screen.blit(self.submit_txt, (SCREEN_WIDTH / 4*2 - self.submit_txt.get_width()/2, SCREEN_HEIGHT / 3))

        for i in range(0,min(10,len(self.winners))):
            screen.blit(self.names[i], (SCREEN_WIDTH/4-self.names[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/20*i))
            screen.blit(self.scores[i], (SCREEN_WIDTH/2-self.scores[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/20*i))
            screen.blit(self.datetimes[i], (SCREEN_WIDTH/4*3-self.datetimes[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/20*i))

        pygame.draw.line(screen, config.WHITE, (100, 900), (1820, 900))
        self.button_sprites.draw(screen)

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene(self.manager))
            for button in self.button_sprites:
                button.handle_event(e)

class Credits():
    def __init__(self):
        super(Credits, self).__init__()
        self.center_w, self.center_h = config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2
        self.label_surface = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

        self.init_labels()
        self.button_sprites = pygame.sprite.Group()
        self.back = Button(860,930,200,50,[self.return_to_menu],config.BIGGER_FONT, "BACK", config.LIGHT_GRAY,config.WHITE,border_w=2)
        self.button_sprites.add(self.back)

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def init_labels(self):
        self.label_surface.fill(config.LIGHT_GRAY)
        self.made_by_label = config.MENU_TITLE.render("MADE BY",True,config.WHITE)
        self.daniel = config.MENU_SUBTITLE.render("Daniel",True,config.WHITE)
        self.jj = config.MENU_SUBTITLE.render("JJ",True,config.WHITE)
        self.pouneh = config.MENU_SUBTITLE.render("Pouneh",True,config.WHITE)
        self.mona = config.MENU_SUBTITLE.render("Mona",True,config.WHITE)
        self.nadine = config.MENU_SUBTITLE.render("Nadine",True,config.WHITE)
        self.stefano = config.MENU_SUBTITLE.render("Stefano",True,config.WHITE)

        pygame.draw.line(self.label_surface, config.WHITE, (100, 300), (1820, 300))

        self.label_surface.blit(self.made_by_label,(self.center_w-self.made_by_label.get_width()/2,100))
        self.label_surface.blit(self.daniel,(self.center_w-self.daniel.get_width()/2,400))
        self.label_surface.blit(self.jj,(self.center_w-self.jj.get_width()/2,480))
        self.label_surface.blit(self.pouneh,(self.center_w-self.pouneh.get_width()/2,560))
        self.label_surface.blit(self.mona,(self.center_w-self.mona.get_width()/2,640))
        self.label_surface.blit(self.nadine,(self.center_w-self.nadine.get_width()/2,720))
        self.label_surface.blit(self.stefano,(self.center_w-self.stefano.get_width()/2,780))

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    self.return_to_menu()
            for button in self.button_sprites:
                button.handle_event(e)
    def render(self, screen):
        screen.blit(self.label_surface,(0,0))
        self.button_sprites.draw(screen)


class SceneMananger(object):
    def __init__(self):
        self.go_to(TitleScene(self))

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self

    def render(self, screen):
        self.scene.render(screen)
        #screen.blit(screen_high,(0,-100))
        #self.camera.render(screen_high, screen)


def main():
    pygame.init()
    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("PlantEd_0.1")
    timer = pygame.time.Clock()
    running = True
    #camera = Camera()
    manager = SceneMananger()


    while running:
        dt = timer.tick(60)/1000.0
        fps = str(int(timer.get_fps()))
        fps_text = config.FONT.render(fps, False, (255,255,255))

        if pygame.event.get(QUIT):
            running = False
            return

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        #camera.render(screen)
        screen.blit(fps_text, (800, 30))
        pygame.display.update()

if __name__ == "__main__":
    main()
