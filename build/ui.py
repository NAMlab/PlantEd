import pygame
from gameobjects.plant import Plant
from utils.gametime import GameTime
from utils.button import DoubleRadioButton,RadioButton, ToggleButton, Button, Slider, SliderGroup, Arrow_Button, Button_Once
from utils.tool_tip import ToolTip, ToolTipManager
from utils.particle import ParticleSystem, PointParticleSystem, StillParticles, Inwards_Particle_System
from utils.animation import Animation
import config
import math
from pygame import rect, Rect
from gameobjects.watering_can import Watering_can
import random
from skillsystem import Skill_System, Skill

# constants in dynamic model, beter in config? dont think so
from fba.dynamic_model import DynamicModel, BIOMASS, STARCH_OUT
from data import assets

HOVER_MESSAGE = pygame.USEREVENT+2

'''
UI: set up all UI elements, update them, link them to functions
@param  scale:size UI dynamically
        Components may differ from level to level --> should be set by file
            Dict active groups for: Organs plus Sliders, Starch deposit, Organ Detail
            
            
Topleft: Stats Bar              Init positions, , labels, Update Value Labels
Below: 4 Organs, Production
            
'''

preset = {"leaf_slider" : 0,
          "stem_slider" : 0,
          "root_slider" : 100,
          "starch_slider" : 0,
          "consume_starch" : False}

class UI:
    def __init__(self, scale, plant, model, camera, production_topleft=(10,100), plant_details_topleft=(10,10),
                 organ_details_topleft=(10,430), dev_mode=False):
        self.name = config.load_options(config.OPTIONS_PATH)["name"]
        self.name_label = config.FONT.render(self.name,True,config.BLACK)
        #print(config.OPTIONS_PATH)#config.BIGGER_FONT.render(config.get_options(config.OPTIONS_PATH)["name"],True,config.BLACK)
        #print(config.load_options("options.json"))
        self.plant = plant
        self.model = model
        self.gametime = GameTime.instance()
        self.hover_message = None
        self.hover_timer = 60
        self.camera = camera
        self.dev_mode = dev_mode

        self.danger_timer = 1

        self.danger_box = self.init_danger_box()

        #performance boost:
        self.label_leaf = config.FONT.render("Leaf", True, (0, 0, 0))  # title
        self.label_stem = config.FONT.render("Stem", True, (0, 0, 0))  # title
        self.label_root = config.FONT.render("Root", True, (0, 0, 0))  # title
        self.label_starch = config.FONT.render("Starch", True, (0, 0, 0))  # title

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
        '''self.biomass_particle = ParticleSystem(20, spawn_box=Rect(200, 495, 25, 25), lifetime=8, color=config.GREEN,
                           apply_gravity=False,
                           speed=[0, -4], spread=[2, -2], active=True)

        self.starch_particle = ParticleSystem(20, spawn_box=Rect(200, 535, 25, 25), lifetime=8, color=config.WHITE,
                           apply_gravity=False,
                           speed=[0, 4], spread=[2, -2], active=False)'''

        self.drain_starch_particle = ParticleSystem(20, spawn_box=Rect(self.production_topleft[0]+530, self.production_topleft[1]+80, 0, 20), lifetime=10, color=config.WHITE,
                                              apply_gravity=False,
                                              speed=[-30, 0], spread=[0, 0], active=False)

        self.open_stomata_particle_in = Inwards_Particle_System(20, spawn_box=Rect(self.production_topleft[0] + 10,
                                                                       self.production_topleft[1] + 80, 100, 50),
                                                    lifetime=6, color=config.GRAY, active=False, center=(50,0))

        self.open_stomata_particle_out = ParticleSystem(20, spawn_box=Rect(self.production_topleft[0]+55,
                                                                           self.production_topleft[1]+80, 10, 0),
                                                        lifetime=10, color=config.WHITE,
                                                        apply_gravity=False,
                                                        speed=[0, -4], spread=[5, 5], active=False)

        #self.particle_systems.append(self.biomass_particle)
        #self.particle_systems.append(self.starch_particle)
        self.particle_systems.append(self.drain_starch_particle)
        self.particle_systems.append(self.open_stomata_particle_in)
        self.particle_systems.append(self.open_stomata_particle_out)

        tipps = config.load_tooltipps("tooltipps.json")
        tooltipps = [ToolTip(tip["x"],tip["y"],tip["lines"],headfont=tip["headfont"],mass=tip["mass"],center=tip["center"]) for tip in tipps]
        self.tool_tip_manager = ToolTipManager(tooltipps, callback=self.plant.get_biomass)
        self.button_sprites.add(ToggleButton(260, config.SCREEN_HEIGHT - 50, 64, 32,
                                             [self.tool_tip_manager.toggle_activate], config.FONT,
                                             text="HINT", pressed=True))


        self.button_sprites.add(Arrow_Button(config.SCREEN_WIDTH/2-100,60,200,50,[self.camera.move_up],0,border_w=3))
        self.button_sprites.add(Arrow_Button(config.SCREEN_WIDTH/2-100,config.SCREEN_HEIGHT-60,200,40,[self.camera.move_down],2,border_w=3))

        # init speed control
        speed_options = [RadioButton(120, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.play], config.FONT,
                                     image=assets.img("normal_speed.png")),
                         RadioButton(160, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.faster], config.FONT,
                                     image=assets.img("fast_speed.png")),
                         RadioButton(200, config.SCREEN_HEIGHT - 50, 32, 32, [self.gametime.fastest], config.FONT,
                                     image=assets.img("fastest_speed.png")),
                         ]

        for rb in speed_options:
            rb.setRadioButtons(speed_options)
            self.button_sprites.add(rb)
        speed_options[0].button_down = True

        self.skip_intro = Button_Once(330, config.SCREEN_HEIGHT - 50,140,32,[self.skip_intro_ui],config.FONT,"SKIP INTRO",border_w=3)
        self.button_sprites.add(self.skip_intro)

        self.presets = [preset for i in range(0, 3)]
        self.init_production_ui()

    def skip_intro_ui(self):
        self.tool_tip_manager.deactivate_tooltipps()
        if not self.plant.organ_starch.toggle_button.button_down:
            self.plant.organ_starch.toggle_button.activate()
        self.gametime.forward()

    def handle_event(self, e):
        for button in self.button_sprites:
            # all button_sprites handle their events
            button.handle_event(e)
        for slider in self.sliders:
            slider.handle_event(e)
        for tips in self.tool_tip_manager.tool_tips:
            tips.handle_event(e)
        if e.type == pygame.MOUSEMOTION:
            #self.hover_message = None
            self.hover_timer = 1000

    def update(self, dt):
        if self.plant.get_biomass() >= 4:
            if self.skip_intro is not None:
                self.button_sprites.remove(self.skip_intro)
                self.gametime.play()
                self.skip_intro = None
        if self.plant.danger_mode:
            self.danger_timer -= dt
            if self.danger_timer <= 0:
                self.danger_timer = 1
        else:
            self.danger_timer = 1
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

    def apply_preset(self, id=0):
        preset = self.presets[id]
        self.leaf_slider.set_percentage(preset["leaf_slider"])
        self.stem_slider.set_percentage(preset["stem_slider"])
        self.root_slider.set_percentage(preset["root_slider"])
        self.starch_slider.set_percentage(preset["starch_slider"])
        if preset["consume_starch"] and not self.plant.organs[2].toggle_button.button_down:
            self.plant.organ_starch.toggle_button.activate()

    def generate_preset(self, id=0):
        active_consumption = False
        '''if self.plant.organs[2].toggle_button is not None:
            active_consumption = self.plant.organs[2].toggle_button.active'''
        preset = {"leaf_slider" : self.leaf_slider.get_percentage(),
                  "stem_slider" : self.stem_slider.get_percentage(),
                  "root_slider" : self.root_slider.get_percentage(),
                  "starch_slider" : self.starch_slider.get_percentage(),
                  "consume_starch" : active_consumption}
        self.presets[id] = preset
        return preset

    def draw(self, screen):
        self.button_sprites.draw(screen)
        [slider.draw(screen) for slider in self.sliders]
        self.draw_ui(screen)
        for element in self.floating_elements:
            element.draw(screen)
        for animation in self.animations:
            screen.blit(animation.image,animation.pos)
        for system in self.particle_systems:
            system.draw(screen)
        self.tool_tip_manager.draw(screen)
        self.tool_tip_manager.draw(screen)
        if self.hover_message is not None and self.hover_timer <= 0:
            x,y = pygame.mouse.get_pos()
            if self.hover_message.get_width() > config.SCREEN_WIDTH-x:
                x = x - self.hover_message.get_width()
            pygame.draw.rect(screen,config.WHITE,(x,y,self.hover_message.get_width()+20,self.hover_message.get_height()+6),border_radius=3)
            screen.blit(self.hover_message,(x+10,y+3))

        # draw dange mode
        if self.danger_timer < 0.5:
            pygame.draw.rect(screen,config.RED,(0,0,config.SCREEN_WIDTH,config.SCREEN_HEIGHT),8)
        if self.plant.danger_mode:
            screen.blit(self.danger_box,(1350,750))

    def post_hover_message(self, message=None, timer=None):
        if message is None:
            #deactivate hover message
            self.hover_message = None
        else:
            if timer is not None:
                self.hover_timer=timer
            self.hover_message = config.FONT.render("{}".format(message),True,config.BLACK)

    def toggle_stomata(self):
        if self.model.stomata_open == True:
            self.model.close_stomata()
            self.open_stomata_particle_in.deactivate()
            self.open_stomata_particle_out.deactivate()
        else:
            self.model.open_stomata()
            self.open_stomata_particle_in.activate()
            self.open_stomata_particle_out.activate()

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
        self.draw_clock(self.s)
        self.draw_production(self.s)
        #self.draw_organ_details(self.s)
        #self.draw_starch_details(s)
        # name plant, make textbox
        screen.blit(self.s, (0, 0))

    def draw_plant_details(self, s):
        # details
        topleft = self.plant_details_topleft
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], 700, 40), border_radius=3)


        # plant lvl
        lvl_text = config.FONT.render("LvL:", True, (0, 0, 0))
        s.blit(lvl_text, dest=(topleft[0]+10, topleft[1]+6))
        level = config.FONT.render("{:.0f}".format(self.plant.get_level()), True, (0, 0, 0))  # title
        s.blit(level, dest=(topleft[0]+lvl_text.get_width()+30, topleft[1]+6))

        # biomass
        biomass_text = config.FONT.render("Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(topleft[0]+110, topleft[1]+6))
        biomass = config.FONT.render("{:.2f} g".format(self.plant.get_biomass()), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(topleft[0]+biomass_text.get_width()+130, topleft[1]+6))

        # water_pool_plant
        water_pool_text = config.FONT.render("Water:", True, (0, 0, 0))
        s.blit(water_pool_text, dest=(topleft[0] + 270, topleft[1] + 6))
        water = config.FONT.render("{:.0f} mmol".format(self.model.water_pool/1000), True, (0, 0, 0))  # title
        s.blit(water, dest=(topleft[0] + biomass_text.get_width() + 290, topleft[1] + 6))

        # name
        s.blit(self.name_label, (topleft[0]+500, topleft[1] + 6))


    def get_day_time(self):
        ticks = self.gametime.get_time()
        day = 1000*60*60*24
        hour = day/24
        min = hour/60
        days = int(ticks/day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def draw_clock(self, s):
        days, hours, minutes = self.get_day_time()
        output_string = "Day {0} {1:02}:{2:02}".format(days, int(hours), int(minutes))
        clock_text = config.FONT.render(output_string, True, config.BLACK)
        pygame.draw.rect(s, config.WHITE, Rect(config.SCREEN_WIDTH / 2 - 140, 10, 280, 40), border_radius=3)
        s.blit(clock_text, (config.SCREEN_WIDTH/2-clock_text.get_width()/2,16))


        RH = config.get_y(hours, config.humidity)
        T = config.get_y(hours, config.summer)

        RH_label = config.FONT.render("{:.0f} %".format(RH*100), True, config.BLACK)
        T_label = config.FONT.render("{:.0f} °C".format(T), True, config.BLACK)

        s.blit(RH_label, ((config.SCREEN_WIDTH / 2-110) - RH_label.get_width()/2, 16))
        s.blit(T_label, ((config.SCREEN_WIDTH / 2+110) - T_label.get_width()/2, 16))

    def init_danger_box(self):
        danger_label_0 = config.BIGGER_FONT.render("ENERGY WARNING", True, config.BLACK)
        danger_label_1 = config.BIG_FONT.render("Your plant is not producing energy.", True, config.BLACK)
        danger_label_2 = config.BIG_FONT.render("Enable starch consumption.", True, config.BLACK)
        danger_label_3 = config.BIG_FONT.render("Or buy leaves then open stomata", True, config.BLACK)
        danger_label_4 = config.BIG_FONT.render("to perform photosynthesis.", True, config.BLACK)
        danger_label_5 = config.BIG_FONT.render("Plant is eating itself.", True, config.BLACK)

        danger_box = pygame.Surface((450, 250), pygame.SRCALPHA)
        danger_box.fill(config.LIGHT_RED)
        pygame.draw.rect(danger_box, config.RED,
                         (0, 0, danger_box.get_width(), danger_box.get_height()), 4)
        danger_box.blit(danger_label_0, (danger_box.get_width() / 2 - danger_label_0.get_width() / 2, 10))
        danger_box.blit(danger_label_1, (danger_box.get_width() / 2 - danger_label_1.get_width() / 2, 80))
        danger_box.blit(danger_label_2, (danger_box.get_width() / 2 - danger_label_2.get_width() / 2, 110))
        danger_box.blit(danger_label_3, (danger_box.get_width() / 2 - danger_label_3.get_width() / 2, 140))
        danger_box.blit(danger_label_4, (danger_box.get_width() / 2 - danger_label_4.get_width() / 2, 170))
        danger_box.blit(danger_label_5, (danger_box.get_width() / 2 - danger_label_5.get_width() / 2, 200))

        return danger_box


    def init_production_ui(self):
        topleft = self.production_topleft
        # init organs
        radioButtons = [
            RadioButton(topleft[0], topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_leaf],
                        config.FONT, image=assets.img("leaf_small.png",(100,100))),
            RadioButton(topleft[0]+110, topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_stem],
                        config.FONT, image=assets.img("stem_small.png",(100,100))),
            RadioButton(topleft[0]+220, topleft[1] + 40, 100, 100,
                        [self.plant.set_target_organ_root],
                        config.FONT, image=assets.img("root_deep.png",(100,100))),
        ]

        '''RadioButton(topleft[0] + 540, topleft[1] + 0, 100, 100,
                        [self.plant.set_target_organ_starch],
                        config.FONT, image=assets.img("starch.png", (100, 100))),'''

        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True

        starch_toggle_button = ToggleButton(topleft[0] + 330, topleft[1] + 110, 200, 30,
                                          [self.toggle_starch_as_resource], config.FONT,
                                          "Consume Starch", vertical=False)
        stomata_toggle_button = ToggleButton(topleft[0] + 0, topleft[1] + 360, 200, 30,
                                            [self.toggle_stomata], config.FONT,
                                            "Open Stomata", vertical=False)
        self.button_sprites.add(starch_toggle_button, stomata_toggle_button)
        self.plant.organ_starch.toggle_button = starch_toggle_button

        self.leaf_slider = Slider((topleft[0]+25, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[0],
                                  plant=self.plant, active=False)
        self.stem_slider = Slider((topleft[0]+25+110, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[1],
                                  plant=self.plant, active=False)
        self.root_slider = Slider((topleft[0]+25+220, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                  organ=self.plant.organs[2],
                                  plant=self.plant, percent=100, active=False)
        self.starch_slider = Slider((topleft[0]+25+330, topleft[1] + 150, 15, 200), config.FONT, (50, 20),
                                    organ=self.plant.organ_starch,
                                    plant=self.plant, active=False)

        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        self.sliders.append(self.starch_slider)
        SliderGroup([slider for slider in self.sliders], 100)

        preset = self.generate_preset()

        radioButtons = [
            DoubleRadioButton(topleft[0]+450, topleft[1] + 170, 45, 45,
                        [self.apply_preset,self.generate_preset], preset=preset, callback_var=0,border_radius=1),
            DoubleRadioButton(topleft[0]+450, topleft[1] + 240, 45, 45,
                        [self.apply_preset,self.generate_preset], preset=preset, callback_var=1, border_radius=1),
            DoubleRadioButton(topleft[0]+450, topleft[1] + 310, 45, 45,
                        [self.apply_preset,self.generate_preset], preset=preset, callback_var=2, border_radius=1),
        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True
        # weird to have extra method for one element

    def draw_organ_detail_temp(self, s, organ, pos, label, show_level=True, factor=1):
        skills = organ.skills
        topleft = pos
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], 100, 30), border_radius=3)
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
        text_organ_mass = config.SMALL_FONT.render("{:.2f} / {:.2f}".format(organ.mass/factor,
                                                organ.get_threshold()/factor),
                                                True, (0, 0, 0))

        j = 0
        for i in range(0,len(skills)):
            if skills[i].active == True:
                #pygame.draw.rect(s, config.WHITE_TRANSPARENT, (topleft[0]+15,topleft[1]+360+i*75,70,70),border_radius=3)
                pygame.draw.rect(s, config.WHITE, (topleft[0]+15,topleft[1]+410+j*75,70,70),3,border_radius=3)
                s.blit(skills[i].image_skilled, (topleft[0]+17, topleft[1]+413+j*75))
                j += 1

        s.blit(text_organ_mass, dest=(topleft[0]+exp_width/2-text_organ_mass.get_width()/2, topleft[1]+120))  # Todo change x, y


    def draw_production(self, s):
        topleft = self.production_topleft
        # headbox
        self.draw_organ_detail_temp(s,self.plant.organs[0],topleft,self.label_leaf)
        self.draw_organ_detail_temp(s,self.plant.organs[1],(topleft[0]+110,topleft[1]),self.label_stem)
        self.draw_organ_detail_temp(s,self.plant.organs[2],(topleft[0]+220,topleft[1]),self.label_root)



        #self.draw_organ_detail_temp(s,self.plant.organ_starch,(topleft[0]+330,topleft[1]),self.label_starch, False, factor=1000)
        topleft = (topleft[0]+330,topleft[1])
        organ = self.plant.organ_starch
        pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1], 200, 30), border_radius=3)
        s.blit(self.label_starch, dest=(topleft[0] + 50 - self.label_starch.get_width() / 2, topleft[1]))


        exp_width = 200
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (topleft[0], topleft[1] + 40, exp_width, 30), border_radius=3)
        needed_exp = organ.get_threshold()
        exp = organ.mass / needed_exp
        factor = 1000
        width = min(int(exp_width / 1 * exp), exp_width)
        pygame.draw.rect(s, (255, 255, 255), (topleft[0], topleft[1] + 40, width, 30), border_radius=3)  # exp
        text_organ_mass = config.BIG_FONT.render("{:.2f} / {:.2f}".format(organ.mass / factor,
                                                                            organ.get_threshold() / factor),
                                                   True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(topleft[0]+exp_width/2-text_organ_mass.get_width()/2, topleft[1]+40))  # Todo change x, y


    '''def draw_starch_details(self, s):
        topleft = self.organ_details_topleft
        # draw starch details
        #lvl_pos = (topleft[0] + 128, topleft[1], 64, 64)
        num_arrows = int((self.plant.organ_starch.percentage) / 100 * 3)
        for i in range(0, num_arrows + 1):
            pygame.draw.line(s, (255, 0, 0), (topleft[0] + 545, topleft[1] + 280 + i * 10),
                             (topleft[0] + 560, topleft[1] + 300 + i * 10), width=4)
            pygame.draw.line(s, (255, 0, 0), (topleft[0] + 575, topleft[1] + 280 + i * 10),
                             (topleft[0] + 560, topleft[1] + 300 + i * 10), width=4)'''