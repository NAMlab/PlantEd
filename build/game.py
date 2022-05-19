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

pygame.mixer.music.load('../assets/background_music.mp3')
pygame.mixer.music.set_volume(0.05)
pygame.mixer.music.play(-1,0)

# seperate high to low level --> less function calls, less clutter
class DevScene(object):
    def __init__(self):
        super(DevScene, self).__init__()
        directions = [(-1,0.5),(-1,0),(0,1),(1,0.5),(1,1)]
        self.ls = LSystem([(820,100),(910,120),(1000,100),(1050,90),(1140,100)], directions)
        #directions = [(0,1)]
        #self.ls = LSystem([(900,110)])

    def render(self, screen):
        screen.fill((50,50,50))
        self.ls.draw(screen)

    def update(self, dt):
        self.ls.update(dt)

    def handle_events(self, events):
        for e in events:
            self.ls.handle_event(e)
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

class Camera:
    def __init__(self, offset_y):
        self.offset_y = offset_y

    def handle_event(self, e):
        pass
        '''if e.type == KEYDOWN and e.key == K_w:
            self.offset_y -= 100
        if e.type == KEYDOWN and e.key == K_s:
            self.offset_y += 100'''

class DefaultGameScene(object):
    def __init__(self):
        pygame.mouse.set_visible(True)
        self.camera = Camera(offset_y=0)
        self.gametime = GameTime.instance()
        self.log = Log()                        # can be turned off
        self.model = DynamicModel(self.gametime, self.log)
        self.plant = Plant((config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT - config.SCREEN_HEIGHT/5), self.model, self.camera)
        self.environment = Environment(self.plant, self.model, 0, 0, self.gametime)
        #example_skills_leaf = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png")) for i in range(0,4)]
        #example_skills_stem = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png")) for i in range(0,2)]
        #example_skills_root = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png")) for i in range(0,2)]
        #example_skills_starch = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png")) for i in range(0,3)]
        #self.skill_system = Skill_System((1700,520),self.plant, example_skills_leaf, example_skills_stem, example_skills_root, example_skills_starch)
        self.ui = UI(1, self.plant, self.model)
        self.entities = []
        for i in range(0,10):
            bug = Bug((190*random.randint(0,10),900+random.randint(0,200)),pygame.Rect(0,900,config.SCREEN_WIDTH,240),[assets.img("bug_purple/bug_purple_{}.png".format(i)) for i in range(0, 5)],self.camera)
            self.entities.append(bug)
        #self.ui.floating_elements.append(FloatingElement((500,500),Rect(400,400,200,200),image=assets.img("stomata/stomata_open.png")))

        #shop items are to be defined by the level
        add_leaf_item = Shop_Item(assets.img("leaf_small.png",(64,64)),self.activate_add_leaf, post_hover_message=self.ui.post_hover_message, message="Leaves enable your plant to produce energy.")

        self.shop = Shop(Rect(1700, 220, 200, 290), [add_leaf_item], self.model, self.plant, post_hover_message=self.ui.post_hover_message)
        self.shop.add_shop_item(["watering","blue_grain", "root_item"])
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
                self.model.calc_growth_rate(leaf_percent, starch_percent, root_percent, starch_percent)
                #growth_rate, starch_rate, starch_intake = self.model.get_rates()
                #nitrate_pool, water_pool = self.model.get_pools()
                #self.log.append_log(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool)
                #self.log.append_plant_log(self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                #self.log.append_row(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool,
                #                    self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                self.plant.grow()
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.log.close_file()
                scoring.upload_score(self.ui.textbox.text, -1)
                pygame.quit()
                sys.exit()
            if e.type == WIN:
                if self.log:
                    self.log.write_log(self.ui.textbox.text)
                    self.log.close_file()
                scoring.upload_score(self.ui.textbox.text, self.gametime.get_time())
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
        for entity in self.entities:
            entity.update(dt)
        self.environment.update(dt)
        self.shop.update(dt)
        self.ui.update(dt)
        self.plant.update(dt, self.model.get_photon_upper())
        self.model.update(self.plant.organs[2].mass, self.plant.get_PLA(), max(self.environment.get_sun_intensity(), 0), self.plant.organ_starch.percentage)


    def render(self, screen):
        screen.fill((0,0,0))
        self.environment.draw_background(temp_surface)
        self.shop.draw(temp_surface)
        self.ui.draw(temp_surface)
        for entity in self.entities:
            entity.draw(temp_surface)
        self.plant.draw(temp_surface)
        self.environment.draw_foreground(temp_surface)
        #self.skill_system.draw(temp_surface)

        screen.blit(temp_surface,(0,self.camera.offset_y))


        '''self.environment.draw_background(tmp_screen)
        self.shop.draw(screen)
        self.ui.draw(screen)
        for entity in self.entities:
            entity.draw(screen)
        self.plant.draw(screen)
        self.environment.draw_foreground(screen)'''

class TitleScene(object):
    def __init__(self):
        super(TitleScene, self).__init__()
        self.font = config.TITLE_FONT
        self.sfont = config.FONT
        self.images = [assets.img("plant_growth_pod/plant_growth_{index}.png".format(index=i)).convert_alpha() for i in range(0, 11)]
        self.centre = (SCREEN_WIDTH/2-self.images[0].get_width()/2, SCREEN_HEIGHT/7)
        self.particle_systems = []
        self.watering_can = Watering_can((0, 0),callback=self.grow_plant)#assets.img("watering_can_outlined.png")
        self.watering_can.activate(40)
        self.plant_size = 0
        self.plant_growth_pos = []
        self.offset = repeat((0, 0))
        self.max_plant_size = 200
        self.image = self.images[0]
        self.mouse_pos = pygame.mouse.get_pos()
        pygame.mouse.set_visible(False)
        self.particle_systems.append(
            ParticleSystem(40, spawn_box=Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0), lifetime=8, color=BLUE ,apply_gravity=True,
                           speed=[0,5], spread=[3,0], active = False))
        self.text1 = self.font.render('PlantEd', True, (255, 255, 255))
        self.water_plant_text = self.sfont.render('> water plant to start <', True, (255, 255, 255))
        self.start_game_text = self.sfont.render('> press space to start <', True, (255, 255, 255))
        self.text2 = self.water_plant_text

    def grow_plant(self, rate):
        self.plant_size += 1

    def render(self, screen):
        tmp_screen.fill((50, 50, 50))
        tmp_screen.blit(self.image, self.centre)
        tmp_screen.blit(self.text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        tmp_screen.blit(self.text2, (SCREEN_WIDTH/2-self.water_plant_text.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))
        for system in self.particle_systems:
            if system.active:
                system.draw(screen)
        self.watering_can.draw(tmp_screen)
        #tmp_screen.blit(self.watering_can, (self.mouse_pos[0],self.mouse_pos[1]-100))
        screen.blit(tmp_screen, next(self.offset))

    def update(self, dt):
        step = self.max_plant_size / (len(self.images))
        index = int(self.plant_size/step)
        self.watering_can.update(dt)
        if index < len(self.images):
            self.image = self.images[index]
        if self.mouse_pos[0] > SCREEN_WIDTH / 3 and self.mouse_pos[0] < SCREEN_WIDTH / 3 * 2 and self.particle_systems[0].active:
            self.plant_size += 1
        if self.plant_size > self.max_plant_size:
            self.text2 = self.start_game_text
        for system in self.particle_systems:
            if system.active:
                system.update(dt)

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE:
                if self.plant_size > self.max_plant_size:
                    pygame.mouse.set_visible(False)
                    self.manager.go_to(DefaultGameScene())
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            self.watering_can.handle_event(e)
            '''if e.type == MOUSEBUTTONDOWN:
                self.particle_systems[0].activate()
                self.watering_can = assets.img("watering_can_outlined_tilted.png")
            if e.type == MOUSEMOTION:
                self.mouse_pos = pygame.mouse.get_pos()
                self.particle_systems[0].spawn_box = pygame.Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0)
            if e.type == MOUSEBUTTONUP:
                self.particle_systems[0].deactivate()
                self.watering_can = assets.img("watering_can_outlined.png")'''

class CustomScene(object):
    def __init__(self):
        super(CustomScene, self).__init__()
        self.font = config.TITLE_FONT
        self.sfont = config.FONT
        self.centre = (SCREEN_WIDTH, SCREEN_HEIGHT/2)
        self.text1 = self.font.render('PlantEd', True, (255,255,255))
        self.text2 = self.font.render('Top 10 Plants!', True, (255,255,255))
        self.text3 = self.sfont.render('> press any key to restart <', True, (255,255,255))

        self.name_txt = self.font.render('Name', True, (255,255,255))
        self.score_txt = self.font.render('Score', True, (255,255,255))
        self.submit_txt = self.font.render('Submit Date', True, (255,255,255))

        self.winners = scoring.get_scores()
        self.scores = []
        self.names = []
        self.datetimes = []

        self.winners = sorted(self.winners, key=lambda x: x["score"])

        for winner in self.winners:
            score = self.get_day_time(winner['score'])
            score = self.font.render(score, True, (255,255,255))
            self.scores.append(score)
            name = self.font.render(winner['name'], True, (255, 255, 255))
            self.names.append(name)
            datetime_added = self.font.render(datetime.utcfromtimestamp(winner['datetime_added']).strftime('%d/%m/%Y %H:%M'), True, (255, 255, 255))
            self.datetimes.append(datetime_added)

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
        screen.blit(self.text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        screen.blit(self.text2, (SCREEN_WIDTH/2-self.text2.get_width()/2, SCREEN_HEIGHT/3-SCREEN_HEIGHT/10))
        pygame.draw.rect(screen, (255,255,255), (SCREEN_WIDTH/4, SCREEN_HEIGHT/3-SCREEN_HEIGHT/25+33,SCREEN_WIDTH/2, 5))
        screen.blit(self.text3, (SCREEN_WIDTH/2-self.text3.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))

        screen.blit(self.name_txt, (SCREEN_WIDTH / 3 - self.name_txt.get_width()/2, SCREEN_HEIGHT / 3-50))
        screen.blit(self.score_txt, (SCREEN_WIDTH / 2 - self.score_txt.get_width()/2, SCREEN_HEIGHT / 3-50))
        screen.blit(self.submit_txt, (SCREEN_WIDTH / 3*2 - self.submit_txt.get_width()/2, SCREEN_HEIGHT / 3-50))

        for i in range(0,min(10,len(self.winners))):
            screen.blit(self.names[i], (SCREEN_WIDTH/3-self.names[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/25*i))
            screen.blit(self.scores[i], (SCREEN_WIDTH/2-self.scores[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/25*i))
            screen.blit(self.datetimes[i], (SCREEN_WIDTH/3*2-self.datetimes[i].get_width()/2, SCREEN_HEIGHT/3+SCREEN_HEIGHT/25*i))

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene())

class SceneMananger(object):
    def __init__(self):
        self.go_to(DefaultGameScene())

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


        #fps = str(int(timer.get_fps()))
        #fps_text = config.FONT.render(fps, False, (255,255,255))
        #print(fps)

        if pygame.event.get(QUIT):
            running = False
            return

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        #camera.render(screen)
        #screen.blit(fps_text, (800, 30))
        pygame.display.update()

if __name__ == "__main__":
    main()
