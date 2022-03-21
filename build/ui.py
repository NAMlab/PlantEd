import pygame
from gameobjects.plant import Plant
from utils.gametime import GameTime
from utils.button import RadioButton, ToggleButton, Button, Slider, SliderGroup, Textbox
from utils.tool_tip import ToolTip, ToolTipManager
from utils.particle import ParticleSystem, PointParticleSystem, StillParticles
from utils.animation import Animation
import config
import math
from pygame import rect, Rect
from gameobjects.watering_can import Watering_can
import random

# constants in dynamic model, beter in config? dont think so
from fba.dynamic_model import DynamicModel, BIOMASS, STARCH_OUT

from data import assets

'''
UI: set up all UI elements, update them, link them to functions
@param  scale:size UI dynamically
        Components may differ from level to level --> should be set by file
            Dict active groups for: Organs plus Sliders, Starch deposit, Organ Detail
'''
# there is a chance random int leads to no movement
class FloatingElement:
    # bounding rect defines the floating space
    def __init__(self, pos, bounding_rect, image=None, animation=None, active=True):
        self.pos = pos
        self.bounding_rect = bounding_rect
        self.image = image
        self.animation = animation
        self.dir = ((random.randint(0,2)-1), (random.randint(0,2)-1)) #random direction -1,1 -1,1
        self.active = active

    def update(self, dt):
        if self.animation is not None:
            self.animation.update(dt)
        if self.active:
            self.move(dt)

    def move(self, dt):
        if not self.bounding_rect.collidepoint(self.pos[0],self.pos[1]):
            self.dir = (-1*self.dir[0], -1*self.dir[1])
        x = self.dir[0] * dt * 10
        y = self.dir[1] * dt * 10
        self.pos = (self.pos[0]+x, self.pos[1]+y)

    def draw(self, screen):
        #pygame.draw.rect(screen,config.WHITE,self.bounding_rect, width=2, border_radius=3)
        if self.animation:
            screen.blit(self.animation.image,(self.pos[0],self.pos[1]))
        elif self.image:
            screen.blit(self.image, (self.pos[0],self.pos[1]))

class InfoElement:
    '''
    InfoElement is hidden (I) until pressed, then it opens and shows an animation/image, text
    '''
    def __init__(self, rect, image, animation=None, headline=None, text=None, active=False):
        self.info_icon = assets.img("drain_icon.png",(16,16))
        self.rect = rect
        self.image = image
        self.animaiton = animation
        self.headline = headline
        self.text = text
        self.active = active

    def update(self, dt):
        pass

    def draw(self, screen):
        pygame.draw.rect(screen, config.WHITE,self.rect, border_radius=3, width=2)

class UI:
    def __init__(self, scale, plant, model):
        self.name = "Plant"
        self.plant = plant
        self.model = model
        self.gametime = GameTime.instance()
        self.sliders = []
        self.button_sprites = pygame.sprite.Group()
        self.particle_systems = []
        self.floating_elements = []
        self.animations = []

        #assets.img("stomata/stomata_open_{}.png".format(0))

        self.animations.append(Animation([assets.img("stomata/stomata_open_{}.png".format(i)) for i in range(0, 9)],720,(250,500)))
        self.animations.append(Animation([assets.img("bug/bug_purple_{}.png".format(i)) for i in range(0, 5)], 720, (250, 500)))
        #self.animations.append(Animation([assets.img("stomata/stomata_open_test.png")],720,(250,500)))

        # init organs
        radioButtons = [
            RadioButton(100, 70, 64, 64, [self.plant.set_target_organ_leaf, self.activate_biomass_objective],
                        config.FONT, image=assets.img("leaf_small.png")),
            RadioButton(180, 70, 64, 64, [self.plant.set_target_organ_stem, self.activate_biomass_objective],
                        config.FONT, image=assets.img("stem_small.png")),
            RadioButton(260, 70, 64, 64, [self.plant.set_target_organ_root, self.activate_biomass_objective],
                        config.FONT, image=assets.img("roots_small.png")),
            RadioButton(460, 70, 64, 64, [self.plant.set_target_organ_starch, self.activate_starch_objective],
                        config.FONT, image=assets.img("starch.png"))
        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True

        self.button_sprites.add(ToggleButton(100, 385, 210, 40, [], config.FONT, "Photosysnthesis", pressed=True, fixed=True))
        toggle_starch_button = ToggleButton(460, 385, 150, 40, [self.toggle_starch_as_resource], config.FONT,"Drain Starch")
        self.plant.organ_starch.toggle_button = toggle_starch_button
        self.button_sprites.add(toggle_starch_button)
        self.leaf_slider = Slider((100, 140, 15, 200), config.FONT, (50, 20), organ=self.plant.organs[0],plant=self.plant, active=False)
        self.stem_slider = Slider((180, 140, 15, 200), config.FONT, (50, 20), organ=self.plant.organs[1],plant=self.plant, active=False)
        self.root_slider = Slider((260, 140, 15, 200), config.FONT, (50, 20), organ=self.plant.organs[2],plant=self.plant, percent=100)
        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        SliderGroup([slider for slider in self.sliders], 100)
        self.sliders.append(Slider((536, 70, 15, 200), config.FONT, (50, 20), organ=self.plant.organ_starch, plant=self.plant,percent=30))
        self.photosynthesis_particle = PointParticleSystem([[330, 405], [380, 405], [380, 100], [330, 100]],
                                                           self.model.get_photon_upper(),
                                                           images=[assets.img("photo_energy.png", (15, 15))],
                                                           speed=(2, 0), callback=self.model.get_photon_upper, nmin=0,
                                                           nmax=80)
        self.particle_systems.append(self.photosynthesis_particle)
        self.starch_particle = PointParticleSystem([[430, 405], [380, 405], [380, 100], [330, 100]], 30,
                                                   images=[assets.img("starch_energy.png", (15, 15))], speed=(2, 0),
                                                   active=False, callback=self.plant.organ_starch.get_intake, factor=20,
                                                   nmin=1, nmax=40)
        self.particle_systems.append(self.starch_particle)
        self.textbox = Textbox(660, 10, 200, 30, config.FONT, self.name)
        self.tool_tip_manager = ToolTipManager(config.tooltipps, callback=self.plant.get_biomass)
        self.button_sprites.add(ToggleButton(240, config.SCREEN_HEIGHT - 50, 64, 32, [self.tool_tip_manager.toggle_activate], config.FONT,text="HINT", pressed=True))

        # init speed control
        speed_options = [RadioButton(140, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.play],config.FONT, image=assets.img("normal_speed.png")),
                         RadioButton(180, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.faster],config.FONT, image=assets.img("fast_speed.png"))
        ]
        for rb in speed_options:
            rb.setRadioButtons(speed_options)
            self.button_sprites.add(rb)
        speed_options[1].button_down = True

    def handle_event(self, e):
        for button in self.button_sprites:
            # all button_sprites handle their events
            button.handle_event(e)
        for slider in self.sliders:
            slider.handle_event(e)
        for tips in self.tool_tip_manager.tool_tips:
            tips.handle_event(e)
        self.textbox.handle_event(e)

    def update(self, dt):
        for slider in self.sliders:
            slider.update()
        for system in self.particle_systems:
            system.update(dt*math.sqrt(self.gametime.GAMESPEED))
        self.tool_tip_manager.update()
        for element in self.floating_elements:
            element.update(dt)
        for animation in self.animations:
            animation.update()

    def draw(self, screen):
        for system in self.particle_systems:
            system.draw(screen)
        self.button_sprites.draw(screen)
        [slider.draw(screen) for slider in self.sliders]
        self.draw_ui(screen)
        for element in self.floating_elements:
            element.draw(screen)
        for animation in self.animations:
            screen.blit(animation.image,animation.pos)
        self.tool_tip_manager.draw(screen)



    # this should focus on UI components
    def activate_biomass_objective(self):
        if self.model.objective == STARCH_OUT:
            # to much code
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
            # is this the right place?
            self.model.set_objective(BIOMASS)


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

    def draw_ui(self, screen):
        # new surface to get alpha
        s = pygame.Surface((config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.draw_plant_details(s)
        self.draw_production(s)
        self.draw_organ_details(s)
        self.draw_starch_details(s)
        # name plant, make textbox
        self.textbox.draw(s)
        screen.blit(s, (0, 0))

    def draw_plant_details(self, s):
        # details
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (660, 50, 200, 160), border_radius=3)

        # plant lvl
        lvl_text = config.FONT.render("Plant Level:", True, (0, 0, 0))
        s.blit(lvl_text, dest=(670, 60))
        level = config.FONT.render("{:.0f}".format(self.plant.get_level()), True, (0, 0, 0))  # title
        s.blit(level, dest=(860 - level.get_width() - 5, 60))

        # biomass
        biomass_text = config.FONT.render("Plant Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(670, 90))
        biomass = config.FONT.render("{:.4f}".format(self.plant.get_biomass()), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(860 - biomass.get_width() - 5, 90))

        # skillpoints greenthumb
        skillpoints_text = config.FONT.render("Green Thumbs:", True, (0, 0, 0))
        s.blit(skillpoints_text, dest=(670, 120))
        skillpoints = config.FONT.render("{}".format(self.plant.upgrade_points), True, (0, 0, 0))  # title
        s.blit(assets.img("green_thumb.png", (20, 20)),
               (860 - assets.img("green_thumb.png", (20, 20)).get_width() - 1, 123))
        s.blit(skillpoints, dest=(860 - skillpoints.get_width() - 26, 120))

        # water
        water_level_text = config.FONT.render("Water:", True, (0, 0, 0))
        s.blit(water_level_text, dest=(670, 150))
        water_level = config.FONT.render("{:.2f}".format(self.model.water_pool), True, (0, 0, 0))  # title
        s.blit(water_level, dest=(860 - water_level.get_width(), 150))

        # nitrate
        nitrate_level_text = config.FONT.render("Nitrate:", True, (0, 0, 0))
        s.blit(nitrate_level_text, dest=(670, 180))
        nitrate_level = config.FONT.render("{:.2f}".format(self.model.nitrate_pool), True, (0, 0, 0))  # title
        s.blit(nitrate_level, dest=(860 - nitrate_level.get_width(), 180))

    def draw_production(self, s):
        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), (60, 10, 580, 30), border_radius=3)
        production_text = config.FONT.render("Production", True, (0, 0, 0))  # title
        s.blit(production_text, dest=(320 - production_text.get_size()[0] / 2, 10))

        # rest of production consists of sliders and buttons

    def draw_organ_details(self, s):
        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), Rect(60, 450, 580, 30), border_radius=3)
        leave_title = config.FONT.render("Organ:{}".format(self.plant.target_organ.type), True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(290 - leave_title.get_size()[0] / 2, 450))

        # organ details
        if self.plant.target_organ.type == self.plant.LEAF:
            image = assets.img("leaf_small.png", (128, 128))
            # self.button_sprites.add(self.button)
        elif self.plant.target_organ.type == self.plant.STEM:
            image = assets.img("stem_small.png", (128, 128))
        elif self.plant.target_organ.type == self.plant.ROOTS:
            image = assets.img("roots_small.png", (128, 128))
        elif self.plant.target_organ.type == self.plant.STARCH:
            image = assets.img("starch.png", (128, 128))
        # draw plant image + exp + lvl + rate + mass
        s.blit(image, (100, 490))

        exp_width = 128
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, Rect(100, 600, exp_width, 25), border_radius=0)
        needed_exp = self.plant.target_organ.get_threshold()
        exp = self.plant.target_organ.mass / needed_exp
        width = min(int(exp_width / 1 * exp), exp_width)
        pygame.draw.rect(s, (255, 255, 255), Rect(100, 600, width, 25), border_radius=0)  # exp
        text_organ_mass = config.FONT.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                                           threshold=self.plant.target_organ.get_threshold()),
                                             True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(105, 596))  # Todo change x, y

        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (245, 490, 395, 130), border_radius=3)

        '''
        # growth_rate in seconds
        growth_rate = config.FONT.render("Growth Rate", True, (0, 0, 0))  # hourly
        s.blit(growth_rate, dest=(245, 500))  # Todo change x, y
        growth_rate_text = config.FONT.render("{:.10f} /s".format(self.plant.target_organ.growth_rate), True,
                                              (0, 0, 0))  # hourly
        s.blit(growth_rate_text, dest=(635 - growth_rate_text.get_width(), 500))  # Todo change x, y

        # mass
        mass_text = config.FONT.render("Organ Mass", True, (0, 0, 0))
        s.blit(mass_text, dest=(245, 525))
        mass = config.FONT.render("{:.10f} /g".format(self.plant.target_organ.mass), True, (0, 0, 0))
        s.blit(mass, dest=(635 - mass.get_width(), 525))

        # intake water
        # if self.plant.target_organ.type == self.plant.ROOTS:
        water_intake_text = config.FONT.render("Water intake", True, (0, 0, 0))
        s.blit(water_intake_text, dest=(245, 550))
        water_intake = config.FONT.render("{:.10f} /h".format(self.model.water_intake), True, (0, 0, 0))
        s.blit(water_intake, dest=(635 - water_intake.get_width(), 550))

        # nitrate water
        # if self.plant.target_organ.type == self.plant.ROOTS:
        nitrate_intake_text = config.FONT.render("Nitrate intake", True, (0, 0, 0))
        s.blit(nitrate_intake_text, dest=(245, 575))
        nitrate_intake = config.FONT.render("{:.10f} /h".format(self.model.nitrate_intake), True, (0, 0, 0))
        s.blit(nitrate_intake, dest=(635 - nitrate_intake.get_width(), 575))
        '''

        # level
        pygame.draw.circle(s, config.WHITE_TRANSPARENT, (100, 510,), 20)
        pygame.draw.circle(s, config.WHITE, (100, 510,), 20, width=3)
        level = config.FONT.render("{:.0f}".format(self.plant.target_organ.level), True, (0, 0, 0))
        s.blit(level, (100 - level.get_width() / 2, 510 - level.get_height() / 2))

    def draw_starch_details(self, s):
        # draw starch details
        lvl_pos = (530, 270, 64, 64)
        num_arrows = int((self.plant.organ_starch.percentage) / 100 * 3)
        for i in range(0, num_arrows + 1):
            pygame.draw.line(s, (255, 0, 0), (545, 280 + i * 10), (560, 300 + i * 10), width=4)
            pygame.draw.line(s, (255, 0, 0), (575, 280 + i * 10), (560, 300 + i * 10), width=4)

        # draw starch pool
        pool_height = 180
        pool_rect = (476, 150, 32, pool_height)
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, pool_rect, border_radius=3)
        pool_limit = self.plant.organ_starch.get_threshold()
        pool_level = self.plant.organ_starch.mass * pool_height / pool_limit
        pool_rect = Rect(pool_rect[0], pool_rect[1] + pool_height - pool_level, 32, pool_level)
        pygame.draw.rect(s, config.WHITE, pool_rect, border_radius=3)
        pool_level_text = config.FONT.render("{:.1f}".format(self.plant.organ_starch.mass), True, (0, 0, 0))  # title
        s.blit(pool_level_text, pool_level_text.get_rect(center=pool_rect.center))