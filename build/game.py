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

currentdir = os.path.abspath('..')
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
pygame.init()
ctypes.windll.user32.SetProcessDPIAware()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)
tmp_screen = pygame.display.set_mode(true_res, pygame.SRCALPHA)
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

#pygame.mixer.music.load('../assets/background_music.mp3', 0.05)
#pygame.mixer.music.play(-1,0)

# seperate high to low level --> less function calls, less clutter
class DevScene(object):
    def __init__(self):
        super(DevScene, self).__init__()
        self.plant = Beziere([(1000,980),(950,900),(1030,830)])
        self.max_wind_force = 0
        self.wind_force = 0
        self.wind_duration = 0
        self.watering_can = Watering_can((0, 0))
        self.blue_grain = Blue_grain((0,0))
        self.wind_time_elapsed = 0 # @60fps

    def render(self, screen):
        tmp_screen.fill((50, 50, 50))
        self.plant.draw(tmp_screen)
        self.blue_grain.draw(screen)
        self.watering_can.draw(screen)
        screen.blit(tmp_screen, (0,0))

    def blow_wind(self, max_wind_force=5, duration=None):
        self.max_wind_force = max_wind_force
        self.wind_duration = duration if duration else 120
        self.wind_time_elapsed = 1

    def update(self, dt):
        if self.wind_duration - self.wind_time_elapsed >=0 and self.wind_time_elapsed > 0:
            # reversed parable to simulate a gust
            #(-(2x-1)*(2x-1)) + 1
            relative_time = self.wind_time_elapsed/self.wind_duration
            self.wind_force = ((-((2*(relative_time)-1)*(2*(relative_time)-1)))+1) * self.max_wind_force
            self.wind_time_elapsed += 1
            print(self.wind_duration, self.wind_time_elapsed, self.wind_force)
        else:
            self.wind_force = 0
            self.wind_duration = 0
            self.wind_time_elapsed = 0
        self.plant.update(dt)
        self.watering_can.update(dt)
        self.blue_grain.update(dt)
        #self.plant.set_force(self.wind_force)

    def handle_events(self, events):
        for e in events:
            self.watering_can.handle_event(e)
            self.blue_grain.handle_event(e)
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if e.type == KEYDOWN and e.key == K_e:
                #self.watering_can.activate(pygame.mouse.get_pos())
                self.blue_grain.activate(pygame.mouse.get_pos())

        self.plant.handle_events(events)

class DefaultGameScene(object):
    def __init__(self):
        #self.ui = UI()
        shop_items = [Shop_Item(assets.img("watering_can_outlined_tilted.png",(64,64)),self.prin) for i in range(0,8)]
        self.shop = Shop((200, 200), shop_items)
        #, image, rect, cost, info_text,

        #self.gameobjects = []
        #self.particle_systems = []
        #self.plant = Plant()

    def init_gameobjects(self):
        pass

    def prin(self):
        print("BUY ME")

    def init_particle_systems(self):
        pass

    def init_plant(self):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            self.shop.handle_event(e)

    def update(self, dt):
        #self.gameobjects.update(dt)
        #self.particle_systems.update(dt)
        self.shop.update(dt)
        #self.plant.update(dt)

    def render(self, screen):
        screen.fill((50, 50, 50))
        #self.gameobjects.draw(screen)
        #self.particle_systems.draw(screen)
        self.shop.draw(screen)
        #self.plant.draw(screen)

class TitleScene(object):
    def __init__(self):
        super(TitleScene, self).__init__()
        self.font = config.TITLE_FONT
        self.sfont = config.FONT
        self.images = [assets.img("plant_growth_pod/plant_growth_{index}.png".format(index=i)).convert_alpha() for i in range(0, 11)]
        self.centre = (SCREEN_WIDTH/2-self.images[0].get_width()/2, SCREEN_HEIGHT/7)
        self.particle_systems = []
        self.watering_can = Watering_can((0, 0))#assets.img("watering_can_outlined.png")
        self.plant_size = 0
        self.plant_growth_pos = []
        self.offset = repeat((0, 0))
        self.max_plant_size = 100
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

    def render(self, screen):
        tmp_screen.fill((50, 50, 50))
        tmp_screen.blit(self.image, self.centre)
        tmp_screen.blit(self.text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        tmp_screen.blit(self.text2, (SCREEN_WIDTH/2-self.water_plant_text.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))
        for system in self.particle_systems:
            if system.active:
                system.draw(screen)
        tmp_screen.blit(self.watering_can, (self.mouse_pos[0],self.mouse_pos[1]-100))
        screen.blit(tmp_screen, next(self.offset))

    def update(self, dt):
        step = self.max_plant_size / (len(self.images))
        index = int(self.plant_size/step)
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
                    self.manager.go_to(GameScene(0))
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if e.type == KEYDOWN and e.key == K_a:
                self.offset = shake()
            if e.type == MOUSEBUTTONDOWN:
                self.particle_systems[0].activate()
                self.watering_can = assets.img("watering_can_outlined_tilted.png")
            if e.type == MOUSEMOTION:
                self.mouse_pos = pygame.mouse.get_pos()
                self.particle_systems[0].spawn_box = pygame.Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0)
            if e.type == MOUSEBUTTONUP:
                self.particle_systems[0].deactivate()
                self.watering_can = assets.img("watering_can_outlined.png")

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

# parent gamescene to hide variables, objects
# gameobjects, particles, weather->gameobject?, UI Elements (button, slider, image, numbers, text)

class GameScene():
    # multiple inits to separate gameobjects, window, ui (slider, button), ...
    def __init__(self, level):
        #super(GameScene, self).__init__()
        pygame.mouse.set_visible(True)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.gametime = GameTime.instance()
        self.log = Log()
        self.offset = repeat((0, 0))
        self.manager = None
        self.hover_message = None
        self.font = config.TITLE_FONT
        self.name = "Generic Plant"
        self.sfont = config.FONT
        self._running = True
        self.pause = False
        self.model = DynamicModel(self.gametime, self.log)
        self.plant = Plant(plant_pos, self.model)
        self.environment = Environment(SCREEN_WIDTH, SCREEN_HEIGHT, self.plant, self.model, 0, 0, self.gametime, self.activate_hawk)
        self.particle_systems = []
        self.sprites = pygame.sprite.Group()
        self.button_sprites = pygame.sprite.Group()
        self.sliders = []
        self.items = []
        self.animations = []
        self.quick_time_events = []
        self.entities = []
        '''
        self.watering_can = {"active": False,
                             "button": Button(780, 270, 64, 64, [self.activate_watering_can], self.sfont,
                                              image=assets.img("watering_can_outlined.png", (64,64)), post_hover_message=self.post_hover_message,
                                              hover_message="Water Your Plant, Cost: 1",  hover_message_image=assets.img("green_thumb.png", (20, 20)), button_sound=assets.sfx('button_klick.mp3', 0.8)),
                             "image": assets.img("watering_can_outlined.png"),
                             "amount": 0,
                             "rate": 0.15,
                             "cost": 1,
                             "pouring": False}
        
        self.blue_grain = {"active": False,
                           "button": Button(780, 354, 64,64, [self.activate_blue_grain], self.sfont,
                                            image=assets.img("blue_grain_0.png"), post_hover_message=self.post_hover_message,
                                            hover_message="Blue Grain to Fertilize, Cost 2", hover_message_image=assets.img("green_thumb.png", (20, 20)), button_sound=assets.sfx('button_klick.mp3', 0.8)),
                           "image": assets.img("blue_grain_bag.png"),
                           "amount": 5, #mg
                           "effect": self.model.increase_nitrate_pool, #0.5mg
                           "cost": 2,
                           "system": ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 50, 50),
                                                    boundary_box=Rect(0,0, SCREEN_WIDTH, SCREEN_HEIGHT-220),
                                                    lifetime=20, size=8, color=BLUE,apply_gravity=True,speed=[0, 5],
                                                    spread=[6,0], active=False, once=True, size_over_lifetime=False)}
        '''
        self.button_sprites.add(self.blue_grain["button"])
        self.button_sprites.add(self.watering_can["button"])
        self.particle_systems.append(self.blue_grain["system"])
        add_leaf_button = Button(676, 270, 64, 64, [self.plant.organs[0].activate_add_leaf], self.sfont,
                                 image=assets.img("leaf_small.png"), post_hover_message=self.post_hover_message, hover_message="Buy one leaf, Cost: 1", hover_message_image=assets.img("green_thumb.png", (20, 20)), button_sound=assets.sfx('button_klick.mp3', 0.8))
        self.button_sprites.add(add_leaf_button)
        self.scarecrow = {"active": False,
                          "button": Button(676, 354, 64, 64, [self.activate_scarecrow], self.sfont,
                                 image=assets.img("scarecrow.png", (64, 64)), post_hover_message=self.post_hover_message,
                                 hover_message="Buy a scarecrow, Cost: 5",  hover_message_image=assets.img("green_thumb.png", (20, 20)), button_sound=assets.sfx('button_klick.mp3', 0.8)),
                          "effect": None,
                          "cost": 5}
        #self.button_sprites.add(add_leaf_button)
        self.button_sprites.add(self.scarecrow["button"])

        radioButtons = [
            RadioButton(100, 70, 64, 64, [self.plant.set_target_organ_leaf, self.activate_biomass_objective], self.sfont, image=assets.img("leaf_small.png")),
            RadioButton(180, 70, 64, 64, [self.plant.set_target_organ_stem, self.activate_biomass_objective], self.sfont, image=assets.img("stem_small.png")),
            RadioButton(260, 70, 64, 64, [self.plant.set_target_organ_root, self.activate_biomass_objective], self.sfont, image=assets.img("roots_small.png")),
            RadioButton(460, 70, 64, 64, [self.plant.set_target_organ_starch, self.activate_starch_objective], self.sfont, image=assets.img("starch.png"))
        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True

        speed_options = [
            RadioButton(100, self.height-50, 32, 32, [self.gametime.start_pause],
                        self.sfont, image=assets.img("pause.png")),
            RadioButton(140, self.height - 50, 32, 32, [self.gametime.play],
                        self.sfont, image=assets.img("normal_speed.png")),
            RadioButton(180, self.height - 50, 32, 32, [self.gametime.faster],
                        self.sfont, image=assets.img("fast_speed.png"))
        ]
        for rb in speed_options:
            rb.setRadioButtons(speed_options)
            self.button_sprites.add(rb)
        speed_options[1].button_down = True

        #self.add_leaf_button = Button(523, 503, 100, 40, [self.plant.get_actions().add_leave] , self.sfont, text="Buy Leaf")
        #self.button_sprites.add(Button(600, 600, 64, 64, [self.activate_watering_can()] , self.sfont, text="Activate Can"))

        self.button_sprites.add(ToggleButton(100, 385, 210, 40, [], self.sfont, "Photosysnthesis", pressed=True, fixed=True))
        toggle_starch_button = ToggleButton(460, 385, 150, 40, [self.toggle_starch_as_resource], self.sfont, "Drain Starch")
        self.plant.organ_starch.toggle_button = toggle_starch_button
        self.button_sprites.add(toggle_starch_button)
        self.leaf_slider = Slider((100, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[0], plant=self.plant, active=False)
        self.stem_slider = Slider((180, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[1], plant=self.plant, active=False)
        self.root_slider = Slider((260, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[2], plant=self.plant, percent=100)
        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        SliderGroup([slider for slider in self.sliders], 100)
        self.sliders.append(Slider((536, 70, 15, 200), self.sfont, (50, 20), organ=self.plant.organ_starch, plant=self.plant, percent=30))
        particle_photosynthesis_points = [[330,405],[380,405],[380,100],[330,100]]
        self.photosynthesis_particle = PointParticleSystem(particle_photosynthesis_points,self.model.get_photon_upper(), images=[assets.img("photo_energy.png", (15, 15))], speed=(2,0), callback=self.model.get_photon_upper, nmin=0, nmax=80)
        particle_starch_points = [[430, 405], [380, 405], [380, 100], [330, 100]]
        self.starch_particle = PointParticleSystem(particle_starch_points, 30, images=[assets.img("starch_energy.png", (15, 15))], speed=(2,0), active=False, callback=self.plant.organ_starch.get_intake, factor=20, nmin=1, nmax=40)
        self.particle_systems.append(self.photosynthesis_particle)
        self.particle_systems.append(self.starch_particle)
        #self.can_particle_system = ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE, apply_gravity=True, speed=[0, 3], spread=True, active=False)
        #self.can_particle_system = ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE,apply_gravity=True,speed=[0, 5], spread=[3, 0], active=False)
        self.particle_systems.append(self.can_particle_system)

        self.textbox = Textbox(660, 10, 200, 30,self.sfont, self.name)

        tooltipps = config.tooltipps
        self.tool_tip_manager = ToolTipManager(tooltipps, callback=self.plant.get_biomass)
        self.button_sprites.add(ToggleButton(240, self.height - 50, 64, 32, [self.tool_tip_manager.toggle_activate], self.sfont, text="HINT", pressed=True))
        pygame.time.set_timer(GROWTH, 1000)

    def handle_events(self, event):
        for e in event:
            if e.type == GROWTH:
                self.model.calc_growth_rate()
                growth_rate, starch_rate, starch_intake = self.model.get_rates()
                nitrate_pool, water_pool = self.model.get_pools()
                self.log.append_log(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool, nitrate_pool)
                self.log.append_plant_log(self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass, self.plant.organ_starch.mass)
                self.plant.grow()
                #self.model.update_pools()
            if e.type == QUIT:
                raise SystemExit("QUIT")
            if e.type == WIN:
                if self.log:
                    self.log.write_log(self.textbox.text)
                #if self.log:
                #    self.log.write_log(self.name)
                scoring.upload_score(self.textbox.text, self.gametime.get_time())
                self.manager.go_to(CustomScene())
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                if self.log:
                    self.log.write_log(self.name)
                self.manager.go_to(TitleScene())

            #if e.type == KEYDOWN and e.key == K_SPACE:
            #    self.manager.go_to(GameScene(0))
            if e.type == KEYDOWN and e.key == K_UP:
                self.gametime.change_speed()
            if e.type == KEYDOWN and e.key == K_DOWN:
                self.gametime.change_speed(0.5)

            self.textbox.handle_event(e)
            for button in self.button_sprites:
                # all button_sprites handle their events
                button.handle_event(e)
            for quick_time_event in self.quick_time_events:
                quick_time_event.handle_event(e)
            if self.watering_can["active"]:
                if e.type == MOUSEBUTTONDOWN:
                        self.watering_can["image"] = assets.img("watering_can_outlined_tilted.png")
                        self.watering_can["pouring"] = True
                        self.can_particle_system.activate()
                        pygame.mixer.Sound.play(assets.sfx('water_can.mp3', 0.05), -1)
                if e.type == MOUSEBUTTONUP:
                    self.watering_can["image"] = assets.img("watering_can_outlined.png")
                    self.can_particle_system.deactivate()
                    pygame.mixer.Sound.stop(assets.sfx('water_can.mp3', 0.05))
                    self.watering_can["pouring"] = False
                if e.type == MOUSEMOTION:
                    x,y = pygame.mouse.get_pos()
                    self.can_particle_system.spawn_box = Rect(x,y+100,0,0)
            if self.blue_grain["active"]:
                x, y = pygame.mouse.get_pos()
                if e.type == MOUSEBUTTONDOWN:
                    pygame.mixer.Sound.play(assets.sfx('gravel.mp3', 0.7))
                    # one function to rule them all
                    self.blue_grain["system"].spawn_box = Rect(x,y,0,0)
                    self.blue_grain["system"].deactivate()
                    self.blue_grain["system"].activate()
                    self.blue_grain["effect"](self.blue_grain["amount"])    # looks very ugly, shopitems should maybe have a class?
                    self.blue_grain["active"] = False
                    pygame.mouse.set_visible(True)

            if e.type == KEYDOWN and e.key == K_a:
                pass
            for slider in self.sliders:
                slider.handle_event(e)
            self.plant.handle_event(e)
            for tips in self.tool_tip_manager.tool_tips:
                tips.handle_event(e)

    def update(self, dt):
        if self.gametime.pause:
            return
        for animation in self.animations:
            animation.update()
        for quick_time_event in self.quick_time_events:
            quick_time_event.update()
        self.quick_time_events = [quick_time_event for quick_time_event in self.quick_time_events if quick_time_event.active]
        self.plant.update()
        self.environment.update(dt)

        # beware of ugly
        if self.plant.get_biomass() > self.plant.seedling.max and not self.stem_slider.active:
            self.stem_slider.active = True
            self.leaf_slider.active = True

        self.model.update(self.plant.organs[2].mass, self.plant.get_PLA(), max(self.environment.get_sun_intensity(), 0), self.plant.organ_starch.percentage)

        for slider in self.sliders:
            slider.update()
        for system in self.particle_systems:
            system.update(dt*math.sqrt(self.gametime.GAMESPEED))

        for entity in self.entities:
            entity.update()

        '''
        # watering can
        if self.watering_can["pouring"]:
            self.watering_can["amount"] -= self.watering_can["rate"]
            self.model.water_pool += self.watering_can["rate"]
            if self.watering_can["amount"] <= 0:
                self.deactivate_watering_can()
        '''
        self.tool_tip_manager.update()

    def render(self, screen):
        #self.draw_background(tmp_screen)
        self.environment.draw_background(tmp_screen)

        # TODO: use for all lists, make more beautiful
        # loop through list of lists
        for sprite in self.sprites:
            if not sprite.update():
                self.sprites.remove(sprite)

        for animation in self.animations:
            tmp_screen.blit(animation.image, animation.pos)

        self.plant.draw(tmp_screen)
        #self.darken_display_daytime(tmp_screen) # --> find smth better
        self.sprites.draw(tmp_screen)
        for quick_time_event in self.quick_time_events:
            quick_time_event.draw(tmp_screen)
        for entity in self.entities:
            entity.draw(tmp_screen)
        for system in self.particle_systems:
            system.draw(tmp_screen)
        self.draw_organ_ui(tmp_screen)
        if self.scarecrow["active"]:
            tmp_screen.blit(assets.img("scarecrow.png", (256, 256)), (1050,580))
        self.environment.draw_foreground(tmp_screen)
        self.button_sprites.draw(tmp_screen)
        self.tool_tip_manager.draw(tmp_screen)

        if self.hover_message:
            x,y = pygame.mouse.get_pos()
            tmp_screen.blit(self.hover_message, (x+10,y))

        if self.watering_can["active"]:
            mouse_pos = pygame.mouse.get_pos()
            normalized_amount = (self.watering_can["image"].get_width()/10)*self.watering_can["amount"] # for max 100 amount
            pygame.draw.rect(tmp_screen, (255,255,255), (mouse_pos[0], mouse_pos[1],normalized_amount, 20))
            tmp_screen.blit(self.watering_can["image"], (mouse_pos))
        if self.blue_grain["active"]:
            mouse_pos = pygame.mouse.get_pos()
            image = self.blue_grain["image"]
            pos = (mouse_pos[0]-image.get_width(),mouse_pos[1]-image.get_height())
            tmp_screen.blit(image, (pos))
        if self.plant.organs[0].can_add_leaf:
            mouse_pos = pygame.mouse.get_pos()
            image = assets.img("leaf_small.png")
            pos = (mouse_pos[0], mouse_pos[1])
            tmp_screen.blit(image, (pos))

        #screen.blit(tmp_screen, next(self.offset))
        screen.blit(tmp_screen, next(self.offset))


    def post_hover_message(self, message):
        self.hover_message = message if message else None

    def activate_starch_objective(self):
        # change particle system to follow new lines
        if self.model.objective == BIOMASS:
            photosysnthesis_lines = self.photosynthesis_particle.points
            photosysnthesis_lines[3] = [430, 100]
            self.photosynthesis_particle.change_points(photosysnthesis_lines)
            self.photosynthesis_particle.particle_counter = 0
            self.photosynthesis_particle.particles.clear()
            starch_lines = self.starch_particle.points
            starch_lines[3] = [430, 100]
            self.starch_particle.change_points(starch_lines)
            self.starch_particle.particle_counter = 0
            self.starch_particle.particles.clear()
            self.model.set_objective(STARCH_OUT)

    def toggle_starch_as_resource(self):
        self.starch_particle.particles.clear()
        if self.model.use_starch:
            self.starch_particle.active = False
            self.model.deactivate_starch_resource()
        else:
            self.starch_particle.active = True
            self.model.activate_starch_resource()
        #self.plant.update_growth_rates(self.model.get_rates())

    def activate_biomass_objective(self):
        if self.model.objective == STARCH_OUT:
            photosysnthesis_lines = self.photosynthesis_particle.points
            photosysnthesis_lines[3] = [330, 100]
            self.photosynthesis_particle.change_points(photosysnthesis_lines)
            self.photosynthesis_particle.particle_counter = 0
            self.photosynthesis_particle.particles.clear()
            starch_lines = self.starch_particle.points
            starch_lines[3] = [330, 100]
            self.starch_particle.change_points(starch_lines)
            self.starch_particle.particle_counter = 0
            self.starch_particle.particles.clear()
            self.model.set_objective(BIOMASS)

    def activate_blue_grain(self):
        if self.plant.upgrade_points - self.blue_grain["cost"] < 0:
            return
        self.plant.upgrade_points -= self.blue_grain["cost"]
        pygame.mouse.set_visible(False)
        self.blue_grain["active"] = True

    def activate_scarecrow(self):
        if self.plant.upgrade_points - self.scarecrow["cost"] < 0:
            return
        self.plant.upgrade_points -= self.scarecrow["cost"]
        self.scarecrow["active"] = True

    def activate_hawk(self):

        if len(self.plant.organs[0].leaves) > 0 and not self.scarecrow["active"]:
            self.offset = shake()
            leaf = self.plant.organs[0].get_random_leave()
            eagle = Eagle(SCREEN_WIDTH, SCREEN_HEIGHT, leaf, Animation([pygame.transform.scale(assets.img("bird/Eagle Normal_{}.png".format(i)), (128, 128)) for i in range(1, 20)], 500), 40,
                          action_sound=assets.sfx('eagle_flap.mp3', 0.7), callback=self.plant.organs[0].remove_leaf)
            self.entities.append(eagle)
            self.quick_time_events.append(
                QuickTimeEvent((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), 5, eagle, assets.img("danger_bird.png", (128, 128)), self.entities,
                               assets.sfx('eagle_screech.mp3', 0.5)))

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))

    def set_growth_target_leaves(self):
        self.plant.target_organ = self.plant.LEAF

    def set_growth_target_stem(self):
        self.plant.target_organ = self.plant.STEM

    def set_growth_target_roots(self):
        self.plant.target_organ = self.plant.ROOTS

    def draw_particle_systems(self, screen):
        for system in self.particle_systems:
            system.draw(screen)

    def draw_background(self, screen):
        screen.fill(SKY_BLUE)
        screen.blit(assets.img("background_empty_sky.png", (SCREEN_WIDTH, SCREEN_HEIGHT)), (0,0))

    def draw_organ_ui(self, screen):
        white = (255, 255, 255)
        white_transparent = (255, 255, 255, 128)
        # new surface to get alpha
        s = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT), pygame.SRCALPHA)
        w,h = s.get_size()

        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), Rect(60, 10, 580, 30), border_radius=3)
        production_text = self.font.render("Production", True, (0, 0, 0))  # title
        s.blit(production_text, dest=(290-production_text.get_size()[0]/2, 10))

        for slider in self.sliders:
            slider.draw(screen)

        # draw life tax
        #life_tax_pos = Rect(360, 230, 64, 64)
        #pygame.draw.rect(s, white_transparent, life_tax_pos, border_radius=5)
        #starch_lvl = self.sfont.render("TAX", True, (0, 0, 0))  # title
        #s.blit(starch_lvl, starch_lvl.get_rect(center=life_tax_pos.center))

        # draw starch details
        lvl_pos = Rect(530, 270, 64, 64)
        # linecolor white to red for flow, 0 -> 0, 0.1 -> 1,
        num_arrows = int((self.plant.organ_starch.percentage)/100 * 3)
        for i in range(0,num_arrows+1):
            pygame.draw.line(s, (255, 0, 0), (545, 280+i*10), (560, 300+i*10), width=4)
            pygame.draw.line(s, (255, 0, 0), (575, 280+i*10), (560, 300+i*10), width=4)

        # draw starch pool
        pool_height = 180
        pool_rect = Rect(476, 150, 32, pool_height)
        pygame.draw.rect(s, white_transparent, pool_rect, border_radius=3)
        pool_limit = self.plant.organ_starch.get_threshold()
        pool_level = self.plant.organ_starch.mass * pool_height/pool_limit
        pool_rect = Rect(pool_rect[0], pool_rect[1]+pool_height-pool_level, 32, pool_level)
        pygame.draw.rect(s, white, pool_rect, border_radius=3)
        pool_level_text = self.sfont.render("{:.1f}".format(self.plant.organ_starch.mass), True, (0, 0, 0))  # title
        s.blit(pool_level_text, pool_level_text.get_rect(center=pool_rect.center))


        # name plant, make textbox
        self.textbox.draw(s)
        #pygame.draw.rect(s, (255,255,255,180), (660, 10, 200, 30), border_radius=3)
        #pygame.draw.rect(s, (255,255,255,180), (660, 10, 200, 30), width=3, border_radius=3)
        #plant_text = self.font.render(self.name, True, (0, 0, 0))  # title
        #s.blit(plant_text, dest=(760-plant_text.get_size()[0]/2, 10))

        # stats background
        pygame.draw.rect(s, white_transparent, (660, 50, 200, 160), border_radius=3)

        # plant lvl
        lvl_text = self.sfont.render("Plant Level:", True, (0, 0, 0))
        s.blit(lvl_text, dest=(670, 60))
        level = self.sfont.render("{:.0f}".format(self.plant.get_level()), True, (0, 0, 0))  # title
        s.blit(level, dest=(860 - level.get_width() - 5, 60))

        # biomass
        biomass_text = self.sfont.render("Plant Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(670, 90))
        biomass = self.sfont.render("{:.4f}".format(self.plant.get_biomass()), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(860-biomass.get_width()-5, 90))

        # skillpoints greenthumb
        skillpoints_text = self.sfont.render("Green Thumbs:", True, (0, 0, 0))
        s.blit(skillpoints_text, dest=(670, 120))
        skillpoints = self.sfont.render("{}".format(self.plant.upgrade_points), True, (0, 0, 0))  # title
        s.blit(assets.img("green_thumb.png", (20, 20)), (860-assets.img("green_thumb.png", (20, 20)).get_width()-1, 123))
        s.blit(skillpoints, dest=(860-skillpoints.get_width()-26, 120))

        # water
        water_level_text = self.sfont.render("Water:", True, (0, 0, 0))
        s.blit(water_level_text, dest=(670, 150))
        water_level = self.sfont.render("{:.2f}".format(self.model.water_pool), True, (0, 0, 0))  # title
        s.blit(water_level, dest=(860 - water_level.get_width(), 150))

        # nitrate
        nitrate_level_text = self.sfont.render("Nitrate:", True, (0, 0, 0))
        s.blit(nitrate_level_text, dest=(670, 180))
        nitrate_level = self.sfont.render("{:.2f}".format(self.model.nitrate_pool), True, (0, 0, 0))  # title
        s.blit(nitrate_level, dest=(860 - nitrate_level.get_width(), 180))

        # shop
        pygame.draw.rect(s, (255, 255, 255, 180), (660, 220, 200, 30), border_radius=3)
        shop_text = self.font.render("Shop", True, (0, 0, 0))  # title
        s.blit(shop_text, dest=(760 - shop_text.get_size()[0] / 2, 220))

        pygame.draw.rect(s, white_transparent, (660, 260, 200, 175), border_radius=3)
        #items

        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), Rect(60, 450, 580, 30), border_radius=3)
        leave_title = self.font.render("Organ", True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(290 - leave_title.get_size()[0] / 2, 450))
        if self.plant.target_organ.type == self.plant.LEAF:
            image = assets.img("leaf_small.png", (128,128))
            #self.button_sprites.add(self.button)
        elif self.plant.target_organ.type == self.plant.STEM:
            image = assets.img("stem_small.png", (128,128))
        elif self.plant.target_organ.type == self.plant.ROOTS:
            image = assets.img("roots_small.png", (128,128))
        elif self.plant.target_organ.type == self.plant.STARCH:
            image = assets.img("starch.png", (128,128))

        # draw plant image + exp + lvl + rate + mass
        s.blit(image, (100,490))

        exp_width = 128
        pygame.draw.rect(s, white_transparent, Rect(100, 600, exp_width, 25), border_radius=0)
        needed_exp = self.plant.target_organ.get_threshold()
        exp = self.plant.target_organ.mass / needed_exp
        width = min(int(exp_width / 1 * exp),exp_width)
        pygame.draw.rect(s, (255, 255, 255), Rect(100, 600, width, 25), border_radius=0)  # exp
        text_organ_mass = self.font.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                                    threshold=self.plant.target_organ.get_threshold()),
                                      True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(105, 596))  # Todo change x, y

        pygame.draw.rect(s, white_transparent,(245, 490, 395, 130), border_radius=3)

        # growth_rate in seconds
        growth_rate = self.sfont.render("Growth Rate", True, (0, 0, 0)) #hourly
        s.blit(growth_rate, dest=(245, 500))  # Todo change x, y
        growth_rate_text = self.sfont.render("{:.10f} /s".format(self.plant.target_organ.growth_rate), True,(0, 0, 0))  # hourly
        s.blit(growth_rate_text, dest=(635-growth_rate_text.get_width(), 500))  # Todo change x, y

        # mass
        mass_text = self.sfont.render("Organ Mass", True, (0, 0, 0))
        s.blit(mass_text, dest=(245, 525))
        mass = self.sfont.render("{:.10f} /g".format(self.plant.target_organ.mass), True, (0, 0, 0))
        s.blit(mass, dest=(635 - mass.get_width(), 525))

        # intake water
        #if self.plant.target_organ.type == self.plant.ROOTS:
        water_intake_text = self.sfont.render("Water intake", True,(0, 0, 0))
        s.blit(water_intake_text, dest=(245,550))
        water_intake = self.sfont.render("{:.10f} /h".format(self.model.water_intake), True,(0, 0, 0))
        s.blit(water_intake, dest=(635-water_intake.get_width(), 550))

        # nitrate water
        # if self.plant.target_organ.type == self.plant.ROOTS:
        nitrate_intake_text = self.sfont.render("Nitrate intake", True, (0, 0, 0))
        s.blit(nitrate_intake_text, dest=(245, 575))
        nitrate_intake = self.sfont.render("{:.10f} /h".format(self.model.nitrate_intake), True, (0, 0, 0))
        s.blit(nitrate_intake, dest=(635 - nitrate_intake.get_width(), 575))


        # level
        pygame.draw.circle(s, white_transparent, (100, 510,), 20)
        pygame.draw.circle(s, white, (100, 510,), 20, width=3)
        level = self.sfont.render("{:.0f}".format(self.plant.target_organ.level), True, (0, 0, 0))
        s.blit(level, (100-level.get_width()/2,510-level.get_height()/2))

        screen.blit(s, (0, 0))

    def on_cleanup(self):
        pygame.quit()


    def exit(self):
        self.manager.go_to(CustomScene("You win!"))

    def die(self):
        self.manager.go_to(CustomScene("You lose!"))


def main():
    pygame.init()

    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("PlantEd_0.1")
    timer = pygame.time.Clock()
    running = True

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
        #screen.blit(fps_text, (800, 30))
        pygame.display.update()

if __name__ == "__main__":
    main()
