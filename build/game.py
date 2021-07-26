import ctypes

import pygame
from pygame.locals import *
import numpy as np
from scipy.interpolate import interp1d

from build import plant
from plant import Plant, Organ
from button import Button, RadioButton, Slider, SliderGroup, ToggleButton
from particle import ParticleSystem, PointParticleSystem
from animation import OneShotAnimation, MoveAnimation
import os, sys
from tool_tip import ToolTipManager, ToolTip
import random

currentdir = os.path.abspath('..')
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
import assets

pygame.init()
ctypes.windll.user32.SetProcessDPIAware()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)
GROWTH = 24
RECALC = 25
WIN = 1
SCREEN_WIDTH = 1920# 1536
SCREEN_HEIGHT = 1080# 864
plant_pos = (SCREEN_WIDTH - SCREEN_WIDTH/4, SCREEN_HEIGHT - SCREEN_HEIGHT/5)

FONT = pygame.font.SysFont('arialblack', 14)
TITLE_FONT = pygame.font.SysFont('arialblack', 20)

GREEN = (19, 155, 23)
BLUE = (75, 75, 200)
GOLDEN_BROWN = (160, 109, 58)
PEACH_PUFF = (255, 218, 185)
HUNTER_GREEN = (53, 88, 52)
QUEEN_BLUE = (58, 110, 165)
ARCTIC_LIME = (210, 255, 40)
SKY_BLUE = (169, 247, 252)

# nice clutter free img manager

fileDir = os.path.dirname(os.path.realpath('__file__'))
assets_dir = os.path.join(fileDir, '../assets/')

_image_library = {}
def get_image(path):
        path = os.path.join(assets_dir, path)
        global _image_library
        image = _image_library.get(path)
        if image == None:
                canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
                image = pygame.image.load(canonicalized_path).convert_alpha()
                _image_library[path] = image
        return image

# init drop sprites
drops = [pygame.transform.scale(get_image("rain/raindrop0.png"), (20, 20)),
                 pygame.transform.scale(get_image("rain/raindrop1.png"), (20, 20)),
                 pygame.transform.scale(get_image("rain/raindrop2.png"), (20, 20))]
splash = [pygame.transform.scale(get_image("rain/raindrop_splash0.png"), (20, 20)),
                  pygame.transform.scale(get_image("rain/raindrop_splash1.png"), (20, 20)),
                  pygame.transform.scale(get_image("rain/raindrop_splash2.png"), (20, 20)),
                  pygame.transform.scale(get_image("rain/raindrop_splash3.png"), (20, 20))]
#menu_plant = pygame.transform.scale(pygame.image.load("plant_complete.png"), (500, 800))
menu_plant = [get_image("plant_growth_pod/plant_growth_{index}.png".format(index=i)).convert_alpha() for i in range(0, 11)]
can = get_image("watering_can_outlined.png")   # pygame.transform.scale(pygame.image.load("watering_can.png"),(128,128)).convert_alpha()
can_tilted = get_image("watering_can_outlined_tilted.png")#pygame.transform.scale(pygame.image.load("watering_can_tilted.png"),(128,128)).convert_alpha()
#leaf_0_yellow = pygame.image.load("leaf_0_yellow.png").convert_alpha()
#leaf_5_yellow = pygame.image.load("leaf_5_yellow.png").convert_alpha()
#root_yellow = pygame.image.load("root_yellow.png").convert_alpha()

background = pygame.transform.scale(get_image("background_empty_sky.png"), (SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
#day_night = pygame.image.load("day_night.png").convert_alpha()

leaf_icon = get_image("leaf_small.png").convert_alpha()
leaf_icon_big = pygame.transform.scale(leaf_icon, (128,128)).convert_alpha()
stem_icon = get_image("stem_small.png").convert_alpha()
stem_icon_big = pygame.transform.scale(stem_icon, (128,128)).convert_alpha()
root_icon = get_image("roots_small.png").convert_alpha()
root_icon_big = pygame.transform.scale(root_icon, (128,128)).convert_alpha()
starch_icon = get_image("starch.png").convert_alpha()
starch_icon_big = pygame.transform.scale(starch_icon, (128,128)).convert_alpha()
drain_icon = get_image("drain_icon.png").convert_alpha()
photo_energy = pygame.transform.scale(get_image("photo_energy.png"),(15,15)).convert_alpha()
starch_energy = pygame.transform.scale(get_image("starch_energy.png"),(15,15)).convert_alpha()
# load plant
#seedlings = [pygame.image.load("seedling_{index}.png".format(index=i)) for i in range(0, 2)]
pygame.mixer.music.load('../assets/plopp.wav')


class Scene(object):
    def __init__(self):
        pass

    def render(self, screen):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def handle_events(self, events):
        raise NotImplementedError

class TitleScene(object):

    def __init__(self):
        super(TitleScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.centre = (SCREEN_WIDTH/2-menu_plant[0].get_width()/2, SCREEN_HEIGHT/7)
        self.particle_systems = []
        self.watering_can = can
        self.plant_size = 0
        self.max_plant_size = 100
        self.images = menu_plant
        self.image = self.images[0]
        self.mouse_pos = pygame.mouse.get_pos()
        pygame.mouse.set_visible(False)
        self.particle_systems.append(
            ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE ,apply_gravity=True,
                           speed=[3,3], active = False))

        self.text1 = self.font.render('PlantEd', True, (255, 255, 255))
        self.water_plant_text = self.sfont.render('> water plant to start <', True, (255, 255, 255))
        self.start_game_text = self.sfont.render('> press space to start <', True, (255, 255, 255))
        self.text2 = self.water_plant_text

    def render(self, screen):

        screen.fill((50, 50, 50))
        screen.blit(self.image, self.centre)

        screen.blit(self.text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        screen.blit(self.text2, (SCREEN_WIDTH/2-self.water_plant_text.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))

        for system in self.particle_systems:
            if system.active:
                system.draw(screen)
        screen.blit(self.watering_can, (self.mouse_pos[0],self.mouse_pos[1]-100))

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
            if e.type == MOUSEBUTTONDOWN:
                self.particle_systems[0].active = True
                self.watering_can = can_tilted
            if e.type == MOUSEMOTION:
                self.mouse_pos = pygame.mouse.get_pos()
                self.particle_systems[0].spawn_box = pygame.Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0)
            if e.type == MOUSEBUTTONUP:
                self.particle_systems[0].active = False
                self.particle_systems[0].particles.clear()
                self.watering_can = can


class CustomScene(object):
    def __init__(self, text):
        self.text = text
        super(CustomScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.centre = (SCREEN_WIDTH, SCREEN_HEIGHT/2)


    def render(self, screen):
        #screen.blit(background, (0, 0))
        screen.fill((0, 0, 0))
        text1 = self.font.render('PlantEd', True, (0, 0, 0))
        text2 = self.sfont.render('YOU WON!', True, (0, 0, 0))
        text3 = self.sfont.render('> press any key to continue <', True, (0, 0, 0))
        screen.blit(text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        screen.blit(text2, (SCREEN_WIDTH/8, SCREEN_HEIGHT/6))
        screen.blit(text3, (SCREEN_WIDTH/2-text3.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene())

class SceneMananger(object):
    def __init__(self):
        self.go_to(TitleScene())

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self

class GameScene(Scene):
    def __init__(self, level):
        super(GameScene, self).__init__()
        pygame.mouse.set_visible(True)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.screen_changes = [pygame.Rect(0,0,SCREEN_WIDTH, SCREEN_HEIGHT)]
        self.manager = None
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self._running = True
        self.plant = Plant(plant_pos)
        self.particle_systems = []
        self.sprites = pygame.sprite.Group()
        self.button_sprites = pygame.sprite.Group()
        self.sliders = []
        self.animations = []
        self.use_watering_can = False
        self.can = can

        radioButtons = [
            RadioButton(100, 70, 64, 64, [self.plant.set_target_organ_leaf, self.activate_biomass_objective], FONT, image=leaf_icon),
            RadioButton(180, 70, 64, 64, [self.plant.set_target_organ_stem, self.activate_biomass_objective], FONT, image=stem_icon),
            RadioButton(260, 70, 64, 64, [self.plant.set_target_organ_root, self.activate_biomass_objective], FONT, image=root_icon),
            RadioButton(460, 70, 64, 64, [self.plant.set_target_organ_starch, self.activate_starch_objective], FONT, image=starch_icon)
        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True
        #self.button = Button(600, 600, 64, 64, [self.plant.get_actions().add_leave] , FONT, text="Add Leave")
        #self.button_sprites.add(Button(600, 600, 64, 64, [self.activate_watering_can()] , FONT, text="Activate Can"))

        self.button_sprites.add(ToggleButton(100, 385, 210, 40, [], FONT, "Activate C3 Photosynthese", pressed=True, fixed=True))
        toggle_starch_button = ToggleButton(460, 385, 150, 40, [self.toggle_starch_as_resource], FONT, "Use Energy Depot")
        self.plant.organs[3].toggle_button = toggle_starch_button
        self.button_sprites.add(toggle_starch_button)
        self.leaf_slider = Slider((100, 140, 15, 200), FONT, (50, 20), organ=self.plant.organs[0], plant=self.plant, active=False)
        self.stem_slider = Slider((180, 140, 15, 200), FONT, (50, 20), organ=self.plant.organs[1], plant=self.plant, active=False)
        self.root_slider = Slider((260, 140, 15, 200), FONT, (50, 20), organ=self.plant.organs[2], plant=self.plant, percent=100)
        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        SliderGroup([slider for slider in self.sliders], 100)
        self.sliders.append(Slider((536, 70, 15, 200), FONT, (50, 20), organ=self.plant.organs[3], plant=self.plant))
        particle_photosynthesis_points = [[330,405],[380,405],[380,100],[330,100]]
        self.photosynthesis_particle = PointParticleSystem(particle_photosynthesis_points,self.plant.get_growth_rate()*20, images=[photo_energy], speed=(2,0), callback=self.plant.get_leaf_photon)
        particle_starch_points = [[430, 405], [380, 405], [380, 100], [330, 100]]
        self.starch_particle = PointParticleSystem(particle_starch_points, 30, images=[starch_energy], speed=(2,0), active=False, callback=self.plant.organs[3].get_rate)
        self.particle_systems.append(self.photosynthesis_particle)
        self.particle_systems.append(self.starch_particle)
        self.can_particle_system = ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE, apply_gravity=True, speed=[3, 3], active=False)
        self.particle_systems.append(self.can_particle_system)

        self.tool_tip_manager = ToolTipManager([ToolTip(700,300,100,200,["Make sure to", "use starch"], self.sfont, button_group=self.button_sprites, point=(-50,20))])

        # start growth every second
        pygame.time.set_timer(GROWTH, 1000)
        #self.init()




    def init(self):
        pass
        # init display --> check for 1080p
        #self.width = SCREEN_WIDTH
        #self.height = SCREEN_HEIGHT
        # get percentage of height/width
        #self.pixel_part_width = self.width / 1000
        #self.pixel_part_height = self.height / 1000
        # define plant origin
        #self.plant.x = self.pixel_part_width * 500
        #self.plant.y = self.pixel_part_height * 900
        # append rain
        #self.particle_systems.append(
        #    ParticleSystem(100, Rect(680, 0, 1300, 0), Rect(680, 0, 1320, self.height), BLUE, direction=(0, 1),
        #                   make_spline_particle=True, images=drops, despawn_animation=self.add_animation,
        #                   despawn_images=splash))
        #self.activate_biomass_production()
        # set growth timer



    def handle_events(self, event):
        for e in event:
            if e.type == GROWTH:
                self.plant.grow()
            if e.type == QUIT: raise SystemExit("QUIT")
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.manager.go_to(TitleScene())
            if e.type == KEYDOWN and e.key == K_SPACE:
                self.manager.go_to(GameScene(0))
            if e.type == KEYDOWN and e.key == K_a:
                self.plant.soil_moisture = self.plant.soil_moisture + 1
            if e.type == KEYDOWN and e.key == K_d:
                self.plant.soil_moisture = self.plant.soil_moisture - 1
            if e.type == MOUSEBUTTONDOWN and self.use_watering_can:
                self.can = can_tilted
                self.can_particle_system.particles.clear()
                self.can_particle_system.active = True
                return
            if e.type == MOUSEBUTTONUP and self.use_watering_can:
                self.can_particle_system.active = False
                self.can = can
            for button in self.button_sprites:
                # all button_sprites handle their events
                button.handle_event(e)
            for slider in self.sliders:
                slider.handle_event(e)
            self.plant.handle_event(e)

            '''if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                 self.plant.organs[0].add_growth_target(pygame.mouse.get_pos())
                 print(pygame.mouse.get_pos())
            if e.type == WIN:
                print("you won")
                self.exit()'''

    # update gameobjects, particles, ...
    def update(self, dt):
        #for animation in self.animations:
            #animation.update()
        self.plant.update()
        # beware of ugly
        if self.plant.get_biomass() > self.plant.seedling.max and not self.stem_slider.active:
            self.stem_slider.active = True
        if self.plant.organs[1].active_threshold >= 2 and not self.leaf_slider.active:
            self.leaf_slider.active = True
        for slider in self.sliders:
            slider.update()
        for system in self.particle_systems:
            system.update(dt)

    def render(self, screen):
        self.draw_background(screen)
        # currently used for drops
        for sprite in self.sprites:
        # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite)

        self.draw_plant(screen)
        self.darken_display_daytime(screen) # --> find smth better
        self.sprites.draw(screen)
        self.button_sprites.draw(screen)

        self.draw_particle_systems(screen)
        self.draw_organ_ui(screen)

        self.tool_tip_manager.draw(screen)

        if self.use_watering_can:
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(can, (mouse_pos))

    def exit(self):
        self.manager.go_to(CustomScene("You win!"))

    def die(self):
        self.manager.go_to(CustomScene("You lose!"))

    def activate_starch_objective(self):
        # change particle system to follow new lines
        if self.plant.produce_biomass:
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
            self.plant.activate_starch_objective()

    def toggle_starch_as_resource(self):
        self.starch_particle.particles.clear()
        if self.plant.use_starch:
            self.starch_particle.active = False
            self.plant.deactivate_starch_resource()
        else:
            self.starch_particle.active = True
            self.plant.activate_starch_resource()

    def activate_biomass_objective(self):
        if not self.plant.produce_biomass:
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
            self.plant.activate_biomass_objective()


    def get_day_time(self):
        # one day rl: ticks*60*60*24, ingame: ticks*6*60
        # one hour rl: ticks*60*60, ingame: ticks*6*60/24
        # one minute rl: ticks*60, ingame: ticks*6/24
        ticks = pygame.time.get_ticks()
        day = 1000*60
        hour = day/24
        min = hour/60
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return hours, minutes

    def get_sun_intensity(self):
        return (np.sin(np.pi/2-np.pi/5+((pygame.time.get_ticks()/(1000 * 60)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    def activate_watering_can(self):
        self.use_watering_can = True
        pygame.mouse.set_visible(False)

    def deactivate_watering_can(self):
        self.use_watering_can = False
        pygame.mouse.set_visible(False)

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))

    def set_growth_target_leaves(self):
        self.plant.target_organ = self.plant.LEAVES

    def set_growth_target_stem(self):
        self.plant.target_organ = self.plant.STEM

    def set_growth_target_roots(self):
        self.plant.target_organ = self.plant.ROOTS

    def draw_particle_systems(self, screen):
        for system in self.particle_systems:
            system.draw(screen)

    def darken_display_daytime(self, screen):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        day_time = (((self.get_sun_intensity() + 1) / 2) * 128)

        #if day_time > 0.5:

        #if day_time > 0.5:
        #    pygame.draw.rect(s, (0, 0, 0, day_time), Rect(0, 0, self.width, self.height))
        #    screen.blit(s, (0, 0))

    def draw_leave(self, screen, pos, size, rot, color):
        leave_surface = pygame.Surface((size[0], size[1]))
        surface = leave_surface.convert_alpha()  # check if necessary
        surface.fill((0, 0, 0, 0))  # "
        pygame.draw.ellipse(surface, color, Rect(0, 0, leave_surface.get_width(), leave_surface.get_height()))
        surface = pygame.transform.rotate(surface, rot)
        screen.blit(surface, (pos[0], pos[1] - surface.get_bounding_rect().height))

    def draw_background(self, screen):
        #screen.fill(SKY_BLUE)
        #day_time_angle = ((self.get_day_time() + 1) / 2) * 360
        #s = pygame.Surface((2160, 2160))
        #s.fill((0, 0, 0))
        #pygame.draw.rect(s, (255,255,255),(0,0,2160, 1080))
        #self.rotate_pivot(screen, s, day_time_angle, (SCREEN_WIDTH/2, SCREEN_HEIGHT/8))
        #bg = pygame.transform.scale(background, (size[0], size[1]))
        screen.fill(SKY_BLUE)
        screen.blit(background, (0,0))

    def draw_organ_ui(self, screen):
        color = (255, 255, 255)
        # new surface to get alpha
        s = pygame.Surface((SCREEN_WIDTH / 3, SCREEN_HEIGHT), pygame.SRCALPHA)
        w,h = s.get_size()

        # headbox
        pygame.draw.rect(s, (color[0], color[1], color[2], 180), Rect(60, 10, w - 60, 30), border_radius=3)
        production_text = TITLE_FONT.render("Production", True, (0, 0, 0))  # title
        s.blit(production_text, dest=(w/2-production_text.get_size()[0]/2, 10))

        for slider in self.sliders:
            slider.draw(screen)

        # draw life tax
        life_tax_pos = Rect(360, 230, 64, 64)
        pygame.draw.rect(s, (color[0], color[1], color[2], 128), life_tax_pos, border_radius=5)
        starch_lvl = FONT.render("TAX", True, (0, 0, 0))  # title
        s.blit(starch_lvl, starch_lvl.get_rect(center=life_tax_pos.center))

        # draw starch details
        lvl_pos = Rect(530, 270, 64, 64)
        if drain_icon:
            s.blit(drain_icon, (lvl_pos[0],lvl_pos[1]))
        else:
            pygame.draw.rect(s, (color[0], color[1], color[2], 128), lvl_pos, border_radius=5)
        starch_lvl = FONT.render("Drain", True, (0, 0, 0))  # title
        s.blit(starch_lvl, starch_lvl.get_rect(center=lvl_pos.center))

        # draw starch pool
        pool_height = 180
        pool_rect = Rect(476, 150, 32, pool_height)
        pygame.draw.rect(s, (color[0], color[1], color[2], 128), pool_rect, border_radius=3)
        pool_limit = self.plant.organs[3].get_threshold()
        pool_level = self.plant.organs[3].mass * pool_height/pool_limit
        pool_rect = Rect(pool_rect[0], pool_rect[1]+pool_height-pool_level, 32, pool_level)
        pygame.draw.rect(s, color, pool_rect, border_radius=3)
        pool_level_text = FONT.render("{:.0f}".format(self.plant.organs[3].mass), True, (0, 0, 0))  # title
        s.blit(pool_level_text, pool_level_text.get_rect(center=pool_rect.center))

        #pygame.draw.rect()

        # headbox
        pygame.draw.rect(s, (color[0], color[1], color[2], 180), Rect(60, 450, w - 60, 30), border_radius=3)
        leave_title = TITLE_FONT.render("Organ", True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(w / 2 - leave_title.get_size()[0] / 2, 450))
        if self.plant.target_organ.type == self.plant.LEAVES:
            image = leaf_icon_big
            #self.button_sprites.add(self.button)

            #color = HUNTER_GREEN
            #s.fill((color[0], color[1], color[2], 128))
        elif self.plant.target_organ.type == self.plant.STEM:
            image = stem_icon_big#pygame.transform.scale(stem_icon, (128, 128))
            # self.button_sprites.remove(self.button)
            #color = HUNTER_GREEN
            #s.fill((color[0], color[1], color[2], 128))
        elif self.plant.target_organ.type == self.plant.ROOTS:
            image = root_icon_big #pygame.transform.scale(root_icon, (128,128))
            #self.button_sprites.remove(self.button)
            #text_soil_moisture = FONT.render("{}".format(self.plant.soil_moisture),
            #                              True, (0, 0, 0))
            #color = GOLDEN_BROWN
            #s.fill((color[0], color[1], color[2], 128))
            #s.blit(text_soil_moisture, dest=(60, 80))  # Todo change x, y
        elif self.plant.target_organ.type == self.plant.STARCH:
            image = starch_icon_big #pygame.transform.scale(starch_icon, (128,128))

        # draw plant image + exp + lvl + rate + mass
        s.blit(image, (100,490))

        exp_width = 128
        pygame.draw.rect(s, (color[0], color[1], color[2], 128), Rect(100, 600, exp_width, 15), border_radius=0)
        needed_exp = self.plant.target_organ.get_threshold()
        exp = self.plant.target_organ.mass / needed_exp
        width = int(exp_width / 1 * exp)
        pygame.draw.rect(s, (255, 255, 255), Rect(100, 600, width, 15), border_radius=0)  # exp
        text_organ_mass = FONT.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                                    threshold=self.plant.target_organ.get_threshold()),
                                      True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(105, 596))  # Todo change x, y

        pygame.draw.rect(s, (color[0], color[1], color[2], 128),(245, 490, 400, 125), border_radius=3)

        # growth_rate in seconds
        growth_rate = FONT.render("Growth Rate /s {:.5f}".format(self.plant.target_organ.growth_rate), True, (0, 0, 0))
        s.blit(growth_rate, dest=(245, 500))  # Todo change x, y

        # upgrade_points
        upgrade_points = FONT.render("Skill Points {:.0f}".format(self.plant.target_organ.upgrade_points), True, (0, 0, 0))
        s.blit(upgrade_points, dest=(245, 525))

        # mass
        mass = FONT.render("Organ Mass {:.5f}".format(self.plant.target_organ.mass), True, (0, 0, 0))
        s.blit(mass, dest=(245, 550))

        # clock
        hours, minutes = self.get_day_time()
        output_string = "{0:02}:{1:02}".format(int(hours), int(minutes))
        clock_text = FONT.render(output_string, True, (0, 0, 0))
        screen.blit(clock_text, clock_text.get_rect(center=(SCREEN_WIDTH/2,20)))

        day_time = ((self.get_sun_intensity() + 1) / 2)
        sun_intensity = FONT.render("{:.2}".format(day_time), True, (0, 0, 0))
        screen.blit(sun_intensity, sun_intensity.get_rect(center=(SCREEN_WIDTH / 2+100, 20)))

        '''
        # organ_head
        pygame.draw.rect(s, (color[0], color[1], color[2], 180), Rect(10, 10, self.width / 3 - 20, 30), border_radius=3)
        leave_title = TITLE_FONT.render("{}".format(self.plant.target_organ.name), True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(20, 10))

        # exp
        pygame.draw.rect(s, (color[0], color[1], color[2], 180), Rect(10, 45, self.width / 3 - 20, 15), border_radius=0)
        needed_exp = self.plant.target_organ.thresholds[self.plant.target_organ.active_threshold]
        exp = self.plant.target_organ.mass / needed_exp
        width = int((self.width / 3 - 20) / 1 * exp)
        pygame.draw.rect(s, QUEEN_BLUE, Rect(10, 45, width, 15), border_radius=0)  # exp
        text_organ_mass = FONT.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                                    threshold = self.plant.target_organ.get_threshold()), True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(60, 42))  # Todo change x, y

        text_organ_mass = FONT.render("{:.2f}".format(self.plant.target_organ.growth_rate),True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(60, 110))  # Todo change x, y

        # upgrade_points
        upgrade_points = FONT.render("{:.2f}".format(self.plant.target_organ.upgrade_points), True, (0, 0, 0))
        s.blit(upgrade_points, dest=(60, 60))
        
        '''
        screen.blit(s, (0, 0))

    def draw_time_line(self, screen):
        # draw a simple grey line with 90° crosses
        line_length = int(self.width/2)
        surface = pygame.Surface((line_length, int(self.height/10)), pygame.SRCALPHA)
        pygame.draw.line(surface, (169, 169, 169, 100),
                         (0, int(self.height / 20)),
                         (line_length, int(self.height / 20)),
                         width=2)
        for i in range(0, 9):
            pygame.draw.line(surface, (169, 169, 169, 100),
                             (i*line_length/9+1, int(self.height / 20)-10),
                             (i*line_length/9+1, int(self.height / 20)+10),
                             width=2)
        screen.blit(surface, (self.width/2, 0))

    #def draw_weather_event(self, index, time_to_event=0):
    #    for i in range(self.weather_system.index, len(self.weather_system.event_list)-1):
    #        self.weather_system.index, self.weather_system.get_start_time(event_id=i)

    def draw_plant(self, screen):
        # draw roots
        #self.draw_roots(screen)
        self.plant.draw(screen)
        # draw stem
        #self.draw_stem(screen, color=GREEN)
        # draw leaves
        #leave_size = int((self.plant.organs[0].active_threshold + 3) * 8)

        # dirty leave blits, offsets are nice, scaling is shit
        #for leave in self.plant.organs[0].leaves:
        #    old_size = leave.image.get_rect(topleft=(leave.x, leave.y))
        #    scaled_leaf = pygame.transform.scale(leave.image, (leave_size, leave_size))
        #    new_size = scaled_leaf.get_rect(topleft=(leave.x, leave.y))
        #    ratio = (new_size[2]/old_size[2], new_size[3]/old_size[3])
        #    screen.blit(leave.image, (leave.x-(leave.offset_x*ratio[0]), leave.y-(leave.offset_y*ratio[1])))

    def draw_roots(self, screen):
        pass
        '''
        image = plant.roots[0]
        pivot = plant.roots[1]
        old_size = image.get_size()
        root_size_ratio = old_size[1] / old_size[0]
        root_size = int((self.plant.organs[2].active_threshold + 3) * 20)
        scaled_stem = pygame.transform.scale(image, (root_size, int(root_size * root_size_ratio)))
        new_size = scaled_stem.get_size()
        old_new_ratio = (new_size[0] / old_size[0], new_size[1] / old_size[1])
        screen.blit(scaled_stem, (plant_pos[0] - (pivot[0] * old_new_ratio[0]), plant_pos[1] - (pivot[1] * old_new_ratio[1])))


        
        for target in self.plant.organs[2].targets:
            angle = np.arctan2(target[0], target[1]) * 180 / np.pi
            image = pygame.image.load("root.png")
            # image = pygame.transform.scale(image, (int(coeff/4), int(coeff))) # Todo fix scaling
            self.rotate_pivot(screen, image, angle + 180, (self.plant.x, self.plant.y))  # Todo why +180 degree?
        '''

    def draw_stem(self, screen, color, rot=0):
        pass
        '''
        if self.plant.organs[1].image:
            screen.blit(self.plant.organs[1])
        image = plant.stem[0]
        pivot = plant.stem[1]
        old_size = image.get_size()
        stem_size_ratio = old_size[1]/old_size[0]
        stem_size = int((self.plant.organs[1].active_threshold + 2) * 10)
        scaled_stem = pygame.transform.scale(image, (stem_size, int(stem_size*stem_size_ratio)))
        new_size = scaled_stem.get_size()
        old_new_ratio = (new_size[0] / old_size[0], new_size[1] / old_size[1])
        screen.blit(scaled_stem, (plant_pos[0] - (pivot[0] * old_new_ratio[0]), plant_pos[1] - (pivot[1] * old_new_ratio[1])))
        '''
        # get mass, calc height
        # get targets, calc curve
        # draw lines
        '''
        draw_height = int((self.height - 150) * self.plant.organs[1].clipped_mass())
        stem_surface = pygame.Surface((int(draw_height / 20), int(draw_height)))
        targets = self.plant.organs[1].targets
        if len(targets) > 3:
            x, y = [], []
            for target in targets:
                x.append(target[1])
                y.append(target[0])
                pygame.draw.rect(screen, pygame.Color("red"), Rect(target[0], target[1], 5, 5))
            f = interp1d(x, y, kind='cubic')
            xnew = np.linspace(min(x), max(x), num=len(targets) * 2, endpoint=True)  # Todo select resolution
            b_points = [(int(f(x)), int(x)) for x in xnew]
            pygame.draw.lines(screen, pygame.Color("green"), False, b_points, 5)
        else:
            pygame.draw.rect(stem_surface, color, Rect(0, 0, stem_surface.get_width(), stem_surface.get_height()))
        screen.blit(stem_surface, (self.plant.x - int(draw_height / 20), self.plant.y - draw_height))
        '''

    def on_cleanup(self):
        pygame.quit()


def main():
    pygame.init()

    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("PlantEd_0.1")
    timer = pygame.time.Clock()
    running = True

    manager = SceneMananger()

    while running:
        #timer.tick(30)
        dt = timer.tick(60)/1000.0


        #fps = str(int(timer.get_fps()))
        #fps_text = FONT.render(fps, False, (255,255,255))
        #print(fps)

        #print(fps)

        if pygame.event.get(QUIT):
            running = False
            return

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        #screen.blit(fps_text, (800, 30))
        #pygame.display.flip()
        pygame.display.update()


if __name__ == "__main__":
    main()
