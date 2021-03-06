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

HOVER_MESSAGE = pygame.USEREVENT+2

'''
UI: set up all UI elements, update them, link them to functions
@param  scale:size UI dynamically
        Components may differ from level to level --> should be set by file
            Dict active groups for: Organs plus Sliders, Starch deposit, Organ Detail
'''
class UI:
    def __init__(self, scale, plant, model, production_topleft=(10,100), plant_details_topleft=(10,10),organ_details_topleft=(10,430)):
        self.name = "Plant"
        self.plant = plant
        self.model = model
        self.gametime = GameTime.instance()
        self.hover_message = None
        self.hover_timer = 60

        # layout positions
        self.production_topleft = production_topleft
        self.plant_details_topleft = plant_details_topleft
        self.organ_details_topleft = organ_details_topleft

        self.s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)

        self.sliders = []
        self.button_sprites = pygame.sprite.Group()
        self.particle_systems = []
        self.floating_elements = []
        self.animations = []

        #put somewhere
        topleft = self.organ_details_topleft
        self.biomass_particle = ParticleSystem(20, spawn_box=Rect(200, 495, 25, 25), lifetime=8, color=config.GREEN,
                           apply_gravity=False,
                           speed=[0, -4], spread=[2, -2], active=True)

        self.starch_particle = ParticleSystem(20, spawn_box=Rect(200, 535, 25, 25), lifetime=8, color=config.WHITE,
                           apply_gravity=False,
                           speed=[0, 4], spread=[2, -2], active=False)

        self.drain_starch_particle = ParticleSystem(20, spawn_box=Rect(230, 745, 55, 0), lifetime=8, color=config.WHITE,
                                              apply_gravity=False,
                                              speed=[0, 4], spread=[2, 0], active=False)

        self.particle_systems.append(self.biomass_particle)
        self.particle_systems.append(self.starch_particle)
        self.particle_systems.append(self.drain_starch_particle)

        self.tool_tip_manager = ToolTipManager(config.tooltipps, callback=self.plant.get_biomass)
        self.button_sprites.add(ToggleButton(240, config.SCREEN_HEIGHT - 50, 64, 32,
                                             [self.tool_tip_manager.toggle_activate], config.FONT,
                                             text="HINT", pressed=True))
        # init speed control
        speed_options = [RadioButton(140, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.play], config.FONT,
                                     image=assets.img("normal_speed.png")),
                         RadioButton(180, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.faster], config.FONT,
                                     image=assets.img("fast_speed.png"))
                         ]
        for rb in speed_options:
            rb.setRadioButtons(speed_options)
            self.button_sprites.add(rb)
        speed_options[1].button_down = True

        self.textbox = Textbox(config.SCREEN_WIDTH/2-90, 50, 180, 30, config.FONT, self.name)

        #assets.img("stomata/stomata_open_{}.png".format(0))

        #self.animations.append(Animation([assets.img("stomata/stomata_open_{}.png".format(i)) for i in range(0, 9)],720,(250,500)))
        #self.animations.append(Animation([assets.img("bug/bug_purple_{}.png".format(i)) for i in range(0, 5)], 720, (250, 500)))
        #self.animations.append(Animation([assets.img("stomata/stomata_open_test.png")],720,(250,500)))
        self.init_production_ui()
        #self.init_organ_ui()

    def handle_event(self, e):
        '''if e.type == pygame.KEYDOWN and e.key == pygame.K_x:
            print(pygame.mouse.get_pos())
            #print(self.tool_tip_manager.current_tip)'''
        for button in self.button_sprites:
            # all button_sprites handle their events
            button.handle_event(e)
        for slider in self.sliders:
            slider.handle_event(e)
        for tips in self.tool_tip_manager.tool_tips:
            tips.handle_event(e)
        self.textbox.handle_event(e)
        if e.type == pygame.MOUSEMOTION:
            self.hover_message = None
            self.hover_timer = 1000
            self.check_mouse_pos()


    def check_mouse_pos(self):
        x, y = pygame.mouse.get_pos()
        if 10 < x < 760 and 10 < y < 50:
            message = None
            if 10 < x < 90:
                message = "Level is a combination of all three organ levels."
            if 90 < x < 260:
                message = "Plant Mass, measured as dry weight in gramm."
            if 260 < x < 320:
                message = "Green Thumbs are used to buy items in the shop."
            if 320 < x < 440:
                message = "Water availability in the environment."
            if 440 < x < 580:
                message = "Nitrate availability in the environment."
            if 580 < x < 760:
                message = "Starch that your plant has stored."
            if message is not None:
                self.post_hover_message(message)


    def update(self, dt):
        for slider in self.sliders:
            slider.update()
        for system in self.particle_systems:
            system.update(dt)
        self.tool_tip_manager.update()
        for element in self.floating_elements:
            element.update(dt)
        for animation in self.animations:
            animation.update()

        # maybe put it to event and make userevent
        self.hover_timer -= 1/dt

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
        if self.hover_message is not None and self.hover_timer <= 0:
            x,y = pygame.mouse.get_pos()
            pygame.draw.rect(screen,config.WHITE_TRANSPARENT,(x,y,self.hover_message.get_width()+20,self.hover_message.get_height()+6),border_radius=3)
            screen.blit(self.hover_message,(x+10,y+3))

    def post_hover_message(self, message):
        self.hover_message = config.FONT.render("{}".format(message),True,config.BLACK)

    def toggle_starch_as_resource(self):
        #self.starch_particle.particles.clear()
        if self.model.use_starch:
            #self.starch_particle.active = False
            self.drain_starch_particle.deactivate()
            self.model.deactivate_starch_resource()
        else:
            #self.starch_particle.active = True
            self.drain_starch_particle.activate()
            self.model.activate_starch_resource()

    def draw_ui(self, screen):
        # new surface to get alpha
        #self.s.fill((0,0,0))
        self.s.fill((0,0,0,0))
        self.draw_plant_details(self.s)
        self.draw_production(self.s)
        #self.draw_organ_details(self.s)
        #self.draw_starch_details(s)
        # name plant, make textbox
        self.textbox.draw(self.s)
        screen.blit(self.s, (0, 0))

    def draw_plant_details(self, s):
        # details
        topleft = self.plant_details_topleft
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], 750, 40), border_radius=3)

        # plant lvl
        lvl_text = config.FONT.render("LvL:", True, (0, 0, 0))
        s.blit(lvl_text, dest=(topleft[0]+10, topleft[1]+6))
        level = config.FONT.render("{:.0f}".format(self.plant.get_level()), True, (0, 0, 0))  # title
        s.blit(level, dest=(topleft[0]+lvl_text.get_width()+20, topleft[1]+6))

        # biomass
        biomass_text = config.FONT.render("Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(topleft[0]+80, topleft[1]+6))
        biomass = config.FONT.render("{:.2f} gramm".format(self.plant.get_biomass()), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(topleft[0]+biomass_text.get_width()+85, topleft[1]+6))

        # skillpoints greenthumb
        #s.blit(assets.img("green_thumb.png", (25, 25)),
        #       (topleft[0]+200, topleft[1] + 7))
        #skillpoints_text = config.FONT.render("Thumbs:", True, (0, 0, 0))
        #s.blit(skillpoints_text, dest=(topleft[0] + 190, topleft[1] + 6))
        skillpoints = config.FONT.render("{}".format(self.plant.upgrade_points), True, (0, 0, 0))  # title
        s.blit(skillpoints, dest=(topleft[0]+255, topleft[1]+6))
        s.blit(assets.img("green_thumb.png",(20,20)),(topleft[0]+skillpoints.get_width() + 270,topleft[1]+10))

        # water
        water_level_text = config.FONT.render("Water:", True, (0, 0, 0))
        s.blit(water_level_text, dest=(topleft[0]+310, topleft[1]+6))
        water_level = config.FONT.render("{:.2f}".format(self.model.water_pool), True, (0, 0, 0))  # title
        s.blit(water_level, dest=(topleft[0]+water_level_text.get_width()+320, topleft[1]+6))

        # nitrate
        nitrate_level_text = config.FONT.render("Nitrate:", True, (0, 0, 0))
        s.blit(nitrate_level_text, dest=(topleft[0]+430, topleft[1]+6))
        nitrate_level = config.FONT.render("{:.2f}".format(self.model.nitrate_pool), True, (0, 0, 0))  # title
        s.blit(nitrate_level, dest=(topleft[0]+nitrate_level_text.get_width()+440, topleft[1]+6))

        # starch
        starch_pool_text = config.FONT.render("Starch:", True, (0,0,0))
        s.blit(starch_pool_text, dest=(topleft[0]+570, topleft[1]+6))
        starch_pool = config.FONT.render("{:.2f}/{:.2f}".format(self.plant.organ_starch.mass, self.plant.organ_starch.get_threshold()),True,(0,0,0))
        s.blit(starch_pool, dest=(topleft[0]+580+starch_pool_text.get_width(),topleft[1]+6))


    def draw_organ_details(self, s):
        topleft = self.organ_details_topleft

        # organ details
        if self.plant.target_organ.type == self.plant.LEAF:
            image = assets.img("leaf_small.png", (128, 128))
            topleft = (topleft[0],topleft[1])
            # self.button_sprites.add(self.button)
        elif self.plant.target_organ.type == self.plant.STEM:
            image = assets.img("stem_small.png", (128, 128))
            topleft = (topleft[0]+80, topleft[1])
        elif self.plant.target_organ.type == self.plant.ROOTS:
            image = assets.img("roots_small.png", (128, 128))
            topleft = (topleft[0]+160, topleft[1])
        elif self.plant.target_organ.type == self.plant.STARCH:
            image = assets.img("starch.png", (128, 128))
            topleft = (topleft[0]+260, topleft[1])

        # draw plant image + exp + lvl + rate + mass

        # headbox
        width = 128
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], width, 30), border_radius=3)
        leave_title = config.FONT.render("Organ:{}".format(self.plant.target_organ.type), True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(topleft[0]+width / 2 - leave_title.get_width() / 2, topleft[1]))

        s.blit(image, (topleft[0], topleft[1]+40))

        exp_width = 128
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (topleft[0], topleft[1]+158, exp_width, 25), border_radius=0)
        needed_exp = self.plant.target_organ.get_threshold()
        exp = self.plant.target_organ.mass / needed_exp
        width = min(int(exp_width / 1 * exp), exp_width)
        pygame.draw.rect(s, (255, 255, 255), (topleft[0], topleft[1]+158, width, 25), border_radius=0)  # exp
        text_organ_mass = config.FONT.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                threshold=self.plant.target_organ.get_threshold()),
                                                True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(topleft[0]+exp_width/2-text_organ_mass.get_width()/2, topleft[1]+158))  # Todo change x, y

        # level
        pygame.draw.circle(s, config.WHITE_TRANSPARENT, (topleft[0]+20,topleft[1]+60), 20)
        pygame.draw.circle(s, config.WHITE, (topleft[0]+20,topleft[1]+60), 20, width=3)
        level = config.FONT.render("{:.0f}".format(self.plant.target_organ.level), True, (0, 0, 0))
        s.blit(level, (topleft[0]+20 - level.get_width() / 2, topleft[1]+60 - level.get_height() / 2))

        '''#skills
        if skills:
            for i in range(0,len(skills)):
                skills[i].pos = (topleft[0]+138+i*80,topleft[1]+50)
                s.blit(skills[i].image,(topleft[0]+138+i*80,topleft[1]+50))'''



    def init_organ_ui(self):
        topleft = self.organ_details_topleft
        # below so it does not get in group
        self.starch_consumption_slider = Slider((topleft[0], topleft[1], 15, 182), config.FONT, (50, 20),
                                                organ=self.plant.organ_starch, plant=self.plant, percent=30,
                                                visible=True)
        self.sliders.append(self.starch_consumption_slider)
        self.starch_consumption_slider.x = topleft[0] + 138
        self.starch_consumption_slider.y = topleft[1]

    def init_production_ui(self):
        topleft = self.production_topleft
        # init organs
        radioButtons = [
            RadioButton(topleft[0], topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_leaf, self.activate_biomass_objective],
                        config.FONT, image=assets.img("leaf_small.png",(100,100))),
            RadioButton(topleft[0]+110, topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_stem, self.activate_biomass_objective],
                        config.FONT, image=assets.img("stem_small.png",(100,100))),
            RadioButton(topleft[0]+220, topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_root, self.activate_biomass_objective],
                        config.FONT, image=assets.img("roots_small.png",(100,100))),
            RadioButton(topleft[0] + 110, topleft[1] + 540, 100,100,
                        [self.plant.set_target_organ_starch],
                        config.FONT, image=assets.img("starch.png",(100,100)))

        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True

        #self.button_sprites.add(
        #    ToggleButton(topleft[0] + 100, topleft[1] + 385, 210, 40, [], config.FONT, "Photosysnthesis", pressed=True,
        #                 fixed=True))
        '''production_buttons = [RadioButton(topleft[0] + 20, topleft[1] + 390, 160, 30,
                                          [self.activate_biomass_objective], config.FONT,
                                          "Produce Biomass", border_radius=3),
                              RadioButton(topleft[0] + 20, topleft[1] + 432, 160,30,
                                            [self.activate_starch_objective],
                                            config.FONT, "Produce Starch", border_radius=3)]

        production_buttons[0].setRadioButtons(production_buttons)
        production_buttons[1].setRadioButtons(production_buttons)
        production_buttons[0].button_down = True'''


        #self.plant.organ_starch.toggle_button = produce_biomass_button
        self.button_sprites.add(production_buttons[0])
        self.button_sprites.add(production_buttons[1])

        starch_toggle_button = ToggleButton(topleft[0] + 215, topleft[1] + 615, 60, 22,
                                          [self.toggle_starch_as_resource], config.FONT,
                                          "Drain", vertical=False)
        self.button_sprites.add(starch_toggle_button)
        self.plant.organ_starch.toggle_button = starch_toggle_button

        self.leaf_slider = Slider((topleft[0]+25, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[0],
                                  plant=self.plant, active=False)
        self.stem_slider = Slider((topleft[0]+25+110, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[1],
                                  plant=self.plant, active=False)
        self.root_slider = Slider((topleft[0]+25+220, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[2],
                                  plant=self.plant, percent=100)
        #self.starch_slider = Slider((topleft[0] + 240, topleft[1] + 110, 15, 200), config.FONT, (50, 20),
        #                          organ=self.plant.organ_starch,
        #                          plant=self.plant, active=False)
        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        #self.sliders.append(self.starch_slider)
        SliderGroup([slider for slider in self.sliders], 100)

        self.starch_consumption_slider = Slider((topleft[0] + 220, topleft[1] + 500, 15, 110), config.FONT, (50, 20),
                                                organ=self.plant.organ_starch, plant=self.plant, percent=30)
        self.sliders.append(self.starch_consumption_slider)

        '''self.sliders.append(
            Slider((topleft[0] + 536, topleft[1] + 70, 15, 200), config.FONT, (50, 20), organ=self.plant.organ_starch,
                   plant=self.plant, percent=30))
        self.photosynthesis_particle = PointParticleSystem([[topleft[0] + 330, topleft[1] + 405],
                                                            [topleft[0] + 380, topleft[1] + 405],
                                                            [topleft[0] + 380, topleft[1] + 100],
                                                            [topleft[0] + 330, topleft[1] + 100]],
                                                           self.model.get_photon_upper(),
                                                           images=[assets.img("photo_energy.png", (15, 15))],
                                                           speed=(2, 0), callback=self.model.get_photon_upper,
                                                           nmin=0, nmax=80)
        self.particle_systems.append(self.photosynthesis_particle)
        self.starch_particle = PointParticleSystem([[topleft[0] + 430, topleft[1] + 405],
                                                    [topleft[0] + 380, topleft[1] + 405],
                                                    [topleft[0] + 380, topleft[1] + 100],
                                                    [topleft[0] + 330, topleft[1] + 100]],
                                                   30, images=[assets.img("starch_energy.png", (15, 15))],
                                                   speed=(2, 0), active=False,
                                                   callback=self.plant.organ_starch.get_intake, factor=20,
                                                   nmin=1, nmax=40)
        self.particle_systems.append(self.starch_particle)'''

    # weird to have extra method for one element

    def draw_organ_detail_temp(self, s, organ, pos, name, show_level=True):
        topleft = pos
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], 100, 30), border_radius=3)
        label = config.FONT.render(name, True, (0, 0, 0))  # title
        s.blit(label, dest=(topleft[0] + 50 - label.get_width() / 2, topleft[1]))

        if show_level:
            pygame.draw.circle(s, config.WHITE_TRANSPARENT, (topleft[0] + 20, topleft[1] + 60), 20)
            pygame.draw.circle(s, config.WHITE, (topleft[0] + 20, topleft[1] + 60), 20, width=3)
            level = organ.level
            level_label = config.FONT.render("{:.0f}".format(level), True, (0, 0, 0))
            s.blit(level_label, (topleft[0] + 20 - level_label.get_width() / 2, topleft[1] + 60 - level_label.get_height() / 2))

        exp_width = 100
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (topleft[0], topleft[1]+120, exp_width, 16), border_radius=3)
        needed_exp = organ.get_threshold()
        exp = organ.mass / needed_exp
        width = min(int(exp_width / 1 * exp), exp_width)
        pygame.draw.rect(s, (255, 255, 255), (topleft[0], topleft[1]+120, width, 16), border_radius=3)  # exp
        text_organ_mass = config.SMALL_FONT.render("{:.2f} / {threshold}".format(organ.mass,
                                                threshold=organ.get_threshold()),
                                                True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(topleft[0]+exp_width/2-text_organ_mass.get_width()/2, topleft[1]+120))  # Todo change x, y




    def draw_production(self, s):
        topleft = self.production_topleft
        # headbox
        self.draw_organ_detail_temp(s,self.plant.organs[0],topleft,"Leaf")
        self.draw_organ_detail_temp(s,self.plant.organs[1],(topleft[0]+110,topleft[1]),"Stem")
        self.draw_organ_detail_temp(s,self.plant.organs[2],(topleft[0]+220,topleft[1]),"Root")

        self.draw_organ_detail_temp(s,self.plant.organ_starch,(topleft[0]+110,topleft[1]+500),"Starch", False)

        #self.draw_organ_detail_temp(s,3,(topleft[0]+330,topleft[1]),"Starch")
        #pygame.draw.line(s,config.WHITE_TRANSPARENT,(topleft[0]+260,topleft[1]+40),(topleft[0]+260,topleft[1]+300),width=2)
        # rest of production consists of sliders and buttons

    def draw_starch_details(self, s):
        topleft = self.organ_details_topleft
        # draw starch details
        #lvl_pos = (topleft[0] + 128, topleft[1], 64, 64)
        num_arrows = int((self.plant.organ_starch.percentage) / 100 * 3)
        for i in range(0, num_arrows + 1):
            pygame.draw.line(s, (255, 0, 0), (topleft[0] + 545, topleft[1] + 280 + i * 10),
                             (topleft[0] + 560, topleft[1] + 300 + i * 10), width=4)
            pygame.draw.line(s, (255, 0, 0), (topleft[0] + 575, topleft[1] + 280 + i * 10),
                             (topleft[0] + 560, topleft[1] + 300 + i * 10), width=4)

        '''# draw starch pool
        pool_height = 180
        pool_rect = (topleft[0] + 138, topleft[1], 32, pool_height)
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, pool_rect, border_radius=3)
        pool_limit = self.plant.organ_starch.get_threshold()
        pool_level = self.plant.organ_starch.mass * pool_height / pool_limit
        pool_rect = Rect(pool_rect[0], pool_rect[1] + pool_height - pool_level, 32, pool_level)
        pygame.draw.rect(s, config.WHITE, pool_rect, border_radius=3)
        pool_level_text = config.FONT.render("{:.1f}".format(self.plant.organ_starch.mass), True, (0, 0, 0))  # title
        s.blit(pool_level_text, pool_level_text.get_rect(center=pool_rect.center))'''