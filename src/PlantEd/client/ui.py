from typing import Tuple
import pygame
from pygame import Rect, KEYDOWN, K_ESCAPE

from PlantEd import config
from PlantEd.data.sound_control import SoundControl
from PlantEd.client.camera import Camera
from PlantEd.client.gameobjects.plant import Plant, Organ
from PlantEd.client.utils.gametime import GameTime
from PlantEd.client.utils.particle import ParticleSystem
from PlantEd.client.utils.narrator import Narrator
from PlantEd.client.utils.hover_message import Hover_Message
from PlantEd.data.assets import AssetHandler
from PlantEd.client.utils.button import (
    RadioButton,
    ToggleButton,
    Slider,
    SliderGroup,
    Arrow_Button,
    ButtonArray,
    NegativeSlider, Button, Textbox,
)

"""
UI: set up all UI elements, update them, link them to functions
@param  scale:size UI dynamically
        Components may differ from level to level --> should be set by file
            Dict active groups for: Organs plus Sliders, Starch deposit, Organ Detail
            
            
Topleft: Stats Bar              Init positions, , labels, Update Value Labels
Below: 4 Organs, Production
            
"""


class UI:
    def __init__(
            self,
            plant: Plant,
            narrator: Narrator,
            camera: Camera,
            sound_control: SoundControl,
            production_topleft: Tuple[int, int] = (10, 100),
            plant_details_topleft: Tuple[int, int] = (10, 10),
            organ_details_topleft: Tuple[int, int] = (10, 430),
            dev_mode: bool = False,
            quit=None
    ):
        self.asset_handler = AssetHandler.instance()
        self.name = config.load_options()["name"]
        self.name_label = self.asset_handler.FONT.render(self.name, True, config.BLACK)
        self.plant = plant
        self.narrator = narrator


        self.humidity = 0
        self.temperature = 0
        self.gametime = GameTime.instance()

        self.hover = Hover_Message(self.asset_handler.FONT, 30, 5)
        self.camera = camera
        self.sound_control = sound_control
        self.dev_mode = dev_mode
        self.quit = quit

        self.stomata_hours = [False for i in range(12)]
        self.pause = False
        self.danger_timer = 1

        self.label_leaf = self.asset_handler.FONT.render("Leaf", True, (0, 0, 0))  # title
        self.label_stem = self.asset_handler.FONT.render("Stem", True, (0, 0, 0))  # title
        self.label_root = self.asset_handler.FONT.render("Root", True, (0, 0, 0))  # title
        self.label_starch = self.asset_handler.FONT.render(
            "Starch", True, (0, 0, 0)
        )  # title
        self.label_water = self.asset_handler.FONT.render(
            "Water", True, (0, 0, 0)
        )  # title
        self.label_producing = self.asset_handler.FONT.render(
            "producing", True, config.GREEN
        )  # title
        self.label_producing = pygame.transform.rotate(
            self.label_producing, 90
        )
        self.label_consuming = self.asset_handler.FONT.render(
            "consuming", True, config.RED
        )  # title
        self.label_consuming = pygame.transform.rotate(
            self.label_consuming, 90
        )

        self.s = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        self.sliders = []
        self.button_sprites = pygame.sprite.Group()
        self.particle_systems = []
        self.floating_elements = []
        self.animations = []

        # layout positions
        self.production_topleft = production_topleft
        self.plant_details_topleft = plant_details_topleft
        self.organ_details_topleft = organ_details_topleft

        self.drain_starch_particle = ParticleSystem(
            20,
            spawn_box=Rect(
                self.production_topleft[0] + 530,
                self.production_topleft[1] + 80,
                0,
                20,
            ),
            lifetime=10,
            color=config.WHITE,
            vel=(-30, 0),
            spread=(0, 0),
            active=False,
        )

        '''self.open_stomata_particle_in = Inwards_Particle_System(
            20,
            spawn_box=Rect(
                self.production_topleft[0] + 10,
                self.production_topleft[1] + 80,
                100,
                50,
            ),
            lifetime=6,
            color=config.GRAY,
            active=False,
            center=(50, 0),
        )'''

        self.open_stomata_particle_out = ParticleSystem(
            20,
            spawn_box=Rect(
                self.production_topleft[0] + 55,
                self.production_topleft[1] + 80,
                10,
                0,
            ),
            lifetime=10,
            color=config.WHITE,
            vel=(0, -4),
            spread=(5, 5),
            active=False,
        )

        self.particle_systems.append(self.drain_starch_particle)
        #self.particle_systems.append(self.open_stomata_particle_in)
        self.particle_systems.append(self.open_stomata_particle_out)

        self.button_sprites.add(
            Arrow_Button(
                config.SCREEN_WIDTH / 2 - 100,
                60,
                200,
                50,
                [self.sound_control.play_select_sfx, self.camera.move_up],
                0,
                border_w=3,
            )
        )

        sfx_mute_icon = self.asset_handler.img("sfx.png", (35, 35))
        self.button_sprites.add(
            ToggleButton(
                30,
                config.SCREEN_HEIGHT - 60,
                50,
                50,
                [self.sound_control.play_toggle_sfx, self.narrator.toggle_mute],
                self.asset_handler.FONT,
                image=sfx_mute_icon,
                border_w=3,
                border_radius=25,
                cross=True,
                cross_size=(10, 10, 40, 40)
            )
        )

        self.button_sprites.add(
            Arrow_Button(
                config.SCREEN_WIDTH / 2 - 100,
                config.SCREEN_HEIGHT - 60,
                200,
                40,
                [self.sound_control.play_select_sfx, self.camera.move_down],
                2,
                border_w=3,
            )
        )

        # init speed control
        speed_options = [
            RadioButton(
                120,
                config.SCREEN_HEIGHT - 50,
                32,
                32,
                [self.gametime.play],
                self.asset_handler.FONT,
                border_w=2,
                image=self.asset_handler.img("normal_speed.PNG"),
            ),
            RadioButton(
                160,
                config.SCREEN_HEIGHT - 50,
                32,
                32,
                [self.gametime.faster],
                self.asset_handler.FONT,
                border_w=2,
                image=self.asset_handler.img("fast_speed.PNG"),
            ),
            RadioButton(
                200,
                config.SCREEN_HEIGHT - 50,
                32,
                32,
                [self.gametime.fastest],
                self.asset_handler.FONT,
                border_w=2,
                image=self.asset_handler.img("fastest_speed.PNG"),
            ),
        ]
        for rb in speed_options:
            rb.setRadioButtons(speed_options)
            self.button_sprites.add(rb)
        speed_options[0].button_down = True

        self.button_array = ButtonArray(
            (1405, 10, 30, 30),
            12,
            2,
            5,
            self.set_stomata_automation,
            self.hover.set_message,
            start_color=(250, 250, 110),
            end_color=(42, 72, 88),
            border_w=2,
            select_sound=self.sound_control.play_select_sfx
        )

        self.preset_day = {
            "type": "day",
            "leaf_slider": 0,
            "stem_slider": 0,
            "root_slider": 100,
            "starch_slider": 0,
        }
        self.preset_night = {
            "type": "night",
            "leaf_slider": 0,
            "stem_slider": 0,
            "root_slider": 100,
            "starch_slider": 0,
        }

        self.active_preset = self.preset_night

        self.init_production_ui()
        self.init_pause_ui()
        # self.gradient = self.init_gradient()

    def switch_preset(self, preset):
        if preset["type"] == "night":
            self.preset_night = preset
            self.active_preset = self.preset_day
        else:
            self.preset_day = preset
            self.active_preset = self.preset_night
        self.leaf_slider.set_percentage(self.active_preset["leaf_slider"])
        self.stem_slider.set_percentage(self.active_preset["stem_slider"])
        self.root_slider.set_percentage(self.active_preset["root_slider"])
        self.starch_slider.set_percentage((self.active_preset["starch_slider"]) / 2 + 50)

    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            self.gametime.pause()
        else:
            self.gametime.unpause()

    def handle_event(self, e: pygame.event.Event):
        if e.type == KEYDOWN and e.key == K_ESCAPE:
            self.toggle_pause()
        if self.pause:
            self.pause_button_exit.handle_event(e)
            self.pause_button_resume.handle_event(e)
            self.narator_slider.handle_event(e)
            self.sfx_slider.handle_event(e)
            self.music_slider.handle_event(e)
            self.textbox.handle_event(e)
            self.apply_button.handle_event(e)
            return
        self.hover.handle_event(e)
        self.button_array.handle_event(e)

        for button in self.button_sprites:
            # all button_sprites handle their events
            button.handle_event(e)
        for slider in self.sliders:
            slider.handle_event(e)
        # for tips in self.tool_tip_manager.tool_tips:
        #    tips.handle_event(e)

    def update(self, dt):
        if self.pause:
            self.textbox.update(dt)
            return
        self.hover.update(dt)
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
        for element in self.floating_elements:
            element.update(dt)
        for animation in self.animations:
            animation.update()
        self.update_stomata_automation()

    def draw(self, screen):
        if self.pause:
            self.draw_pause_menu(screen)
            return
        self.button_array.draw(screen)
        self.button_sprites.draw(screen)
        days, hours, minutes = self.get_day_time()
        slider_color = config.YELLOW if 8 < hours < 20 else config.BLUE
        [slider.draw(screen, slider_color) for slider in self.sliders]
        self.draw_ui(screen)
        for element in self.floating_elements:
            element.draw(screen)
        for animation in self.animations:
            screen.blit(animation.image, animation.pos)
        for system in self.particle_systems:
            system.draw(screen)

        # draw danger mode
        if self.danger_timer < 0.5:
            pygame.draw.rect(
                screen,
                config.RED,
                (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
                8,
            )
        if self.plant.danger_mode:
            screen.blit(self.danger_box, (1350, 750))
        self.hover.draw(screen)

    def set_stomata_automation(self, hours):
        self.stomata_hours = hours

    def update_stomata_automation(self):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = 1000 * 60 * 60
        hours = (ticks % day) / hour
        self.button_array.update(hours)
        hours = (int)(hours / 2)
        open = self.stomata_hours[hours]
        if open and self.plant.get_stomata_open() is False:
            self.open_stomata()
            self.button_array.go_green()
        if not open and self.plant.get_stomata_open() is True:
            self.close_stomata()
            self.button_array.go_red()

    def open_stomata(self):
        self.plant.organs[0].stomata_open = True
        #self.open_stomata_particle_in.activate()
        #self.open_stomata_particle_out.activate()

    def close_stomata(self):
        self.plant.organs[0].stomata_open = False
        #self.open_stomata_particle_in.deactivate()
        #self.open_stomata_particle_out.deactivate()

    def draw_ui(self, screen):
        self.s.fill((0, 0, 0, 0))
        self.draw_plant_details(self.s)
        self.draw_clock(self.s)
        self.draw_production(self.s)
        screen.blit(self.s, (0, 0))

    def draw_plant_details(self, s, factor=100):
        # details
        topleft = self.plant_details_topleft
        pygame.draw.rect(
            s, config.WHITE, (topleft[0], topleft[1], 470, 40), border_radius=3
        )

        # biomass
        biomass_text = self.asset_handler.FONT.render("Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(topleft[0] + 10, topleft[1] + 6))
        biomass = self.asset_handler.FONT.render(
            "{:.2f} x10⁻² gDW".format(self.plant.get_biomass() * factor), True, (0, 0, 0)
        )  # title
        s.blit(
            biomass,
            dest=(topleft[0] + biomass_text.get_width() + 30, topleft[1] + 6),
        )
        # name
        s.blit(self.name_label, (topleft[0] + 460 - self.name_label.get_width(), topleft[1] + 6))

    def get_day_time(self):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        min = hour / 60
        days = int(ticks / day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def draw_clock(self, s):
        days, hours, minutes = self.get_day_time()
        output_string = "Day {0}/45 {1:02}:{2:02}".format(
            days + 10, int(hours), int(minutes)
        )
        clock_text = self.asset_handler.FONT.render(output_string, True, config.BLACK)
        pygame.draw.rect(
            s,
            config.WHITE,
            Rect(config.SCREEN_WIDTH / 2 - 140, 10, 280, 40),
            border_radius=3,
        )
        s.blit(
            clock_text,
            (config.SCREEN_WIDTH / 2 - clock_text.get_width() / 2, 16),
        )

        humidity_label = self.asset_handler.FONT.render(
            "{:.0f} %".format(self.humidity), True, config.BLACK
        )
        temperature_label = self.asset_handler.FONT.render("{:.0f} °C".format(self.temperature), True, config.BLACK)

        s.blit(
            humidity_label,
            ((config.SCREEN_WIDTH / 2 - 110) - humidity_label.get_width() / 2, 16),
        )
        s.blit(
            temperature_label,
            ((config.SCREEN_WIDTH / 2 + 110) - temperature_label.get_width() / 2, 16),
        )

    def init_pause_ui(self):
        self.options = config.load_options()

        self.music_label = self.asset_handler.BIGGER_FONT.render(
            "Music", True, config.WHITE
        )
        self.sfx_label = self.asset_handler.BIGGER_FONT.render(
            "SFX", True, config.WHITE
        )
        self.narator_label = self.asset_handler.BIGGER_FONT.render(
            "Narator", True, config.WHITE
        )

        self.pause_label = self.asset_handler.MENU_TITLE.render(
            "Game Paused", True, config.WHITE
        )
        self.pause_button_resume = Button(
            700,
            config.SCREEN_HEIGHT - 250,
            200,
            50,
            [self.sound_control.play_select_sfx, self.resume],
            self.asset_handler.BIG_FONT,
            "RESUME",
            border_w=2
        )
        self.pause_button_exit = Button(
            1020,
            config.SCREEN_HEIGHT - 250,
            200,
            50,
            [self.quit],
            self.asset_handler.BIG_FONT,
            "QUIT GAME",
            border_w=2,
        )

        self.music_slider = Slider(
            (config.SCREEN_WIDTH / 2 - 300 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["music_volume"] * 100,
            active=True,
        )
        self.narator_slider = Slider(
            (config.SCREEN_WIDTH / 2 - 150 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["narator_volume"] * 100,
            active=True,
        )
        self.sfx_slider = Slider(
            (config.SCREEN_WIDTH / 2 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["sfx_volume"] * 100,
            active=True,
        )

        self.textbox = Textbox(
            config.SCREEN_WIDTH / 2 + 100,
            360,
            200,
            50,
            self.asset_handler.BIGGER_FONT,
            self.options["name"],
            background_color=config.LIGHT_GRAY,
            textcolor=config.WHITE,
            highlight_color=config.WHITE,
        )

        self.apply_button = Button(
            config.SCREEN_WIDTH / 2 + 100,
            460,
            200,
            50,
            [self.apply_options, self.sound_control.reload_options, self.narrator.reload_options],
            self.asset_handler.BIG_FONT,
            "APPLY",
            border_w=2,
        )

    def apply_options(self):
        config.write_options(self.get_options())
        self.name = config.load_options()["name"]
        self.name_label = self.asset_handler.FONT.render(self.name, True, config.BLACK)

    def get_options(self):
        upload_score = config.load_options()["upload_score"]
        options = {
            "music_volume": self.music_slider.get_percentage() / 100,
            "sfx_volume": self.sfx_slider.get_percentage() / 100,
            "narator_volume": self.narator_slider.get_percentage() / 100,
            "name": self.textbox.text,
            "upload_score": upload_score
        }
        return options

    def resume(self):
        self.pause = False
        self.gametime.unpause()

    def init_production_ui(self):
        topleft = self.production_topleft
        # init organs
        radioButtons = [
            RadioButton(
                topleft[0],
                topleft[1] + 40,
                100,
                100,
                [self.sound_control.play_select_organs_sfx, self.plant.set_target_organ_leaf],
                self.asset_handler.FONT,
                image=self.asset_handler.img("leaf_small.PNG", (100, 100)),
            ),
            RadioButton(
                topleft[0] + 110,
                topleft[1] + 40,
                100,
                100,
                [self.sound_control.play_select_organs_sfx, self.plant.set_target_organ_stem],
                self.asset_handler.FONT,
                image=self.asset_handler.img("stem_small.PNG", (100, 100)),
            ),
            RadioButton(
                topleft[0] + 220,
                topleft[1] + 40,
                100,
                100,
                [self.sound_control.play_select_organs_sfx, self.plant.set_target_organ_root],
                self.asset_handler.FONT,
                image=self.asset_handler.img("root_deep.PNG", (100, 100)),
            ),
        ]

        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True

        self.leaf_slider = Slider(
            (topleft[0] + 25, topleft[1] + 150, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            organ=self.plant.organs[0],
            plant=self.plant,
            active=False,
        )
        self.stem_slider = Slider(
            (topleft[0] + 25 + 110, topleft[1] + 150, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            organ=self.plant.organs[1],
            plant=self.plant,
            active=False,
        )
        self.root_slider = Slider(
            (topleft[0] + 25 + 220, topleft[1] + 150, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            organ=self.plant.organs[2],
            plant=self.plant,
            percent=100,
            active=False,
        )
        self.starch_slider = NegativeSlider(
            (topleft[0] + 25 + 330, topleft[1] + 150, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            organ=self.plant.organ_starch,
            plant=self.plant,
            callback=self.plant.organs[2].set_percentage,
            percent=45,
            active=False,
        )

        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        self.sliders.append(self.starch_slider)
        SliderGroup([slider for slider in self.sliders], 100)

    def draw_pause_menu(self, s):
        pygame.draw.rect(s, config.WHITE, (config.SCREEN_WIDTH / 2 - 400, 220, 800, 430), border_radius=3, width=1)
        s.blit(self.music_label, (config.SCREEN_WIDTH / 2 - self.music_label.get_width() / 2 - 300, 300))
        s.blit(self.narator_label, (config.SCREEN_WIDTH / 2 - self.narator_label.get_width() / 2 - 150, 300))
        s.blit(self.sfx_label, (config.SCREEN_WIDTH / 2 - self.sfx_label.get_width() / 2, 300))
        s.blit(self.pause_label, (config.SCREEN_WIDTH / 2 - self.pause_label.get_width() / 2, 100))

        self.pause_button_exit.draw(s)
        self.pause_button_resume.draw(s)
        self.narator_slider.draw(s)
        self.sfx_slider.draw(s)
        self.music_slider.draw(s)
        self.textbox.draw(s)
        self.apply_button.draw(s)

    def draw_organ_detail_temp(
            self, s, organ: Organ, pos, label, show_amount=True, factor=1
    ):
        topleft = pos
        pygame.draw.rect(
            s, config.WHITE, (topleft[0], topleft[1], 100, 30), border_radius=3
        )
        s.blit(
            label, dest=(topleft[0] + 50 - label.get_width() / 2, topleft[1])
        )

        if show_amount:
            pygame.draw.circle(
                s,
                config.WHITE_TRANSPARENT,
                (topleft[0] + 20, topleft[1] + 60),
                20,
            )
            pygame.draw.circle(
                s,
                config.WHITE,
                (topleft[0] + 20, topleft[1] + 60),
                20,
                width=3,
            )
            amount = organ.get_organ_amount()
            amount_label = self.asset_handler.FONT.render(
                "{:.0f}".format(amount), True, (0, 0, 0)
            )
            s.blit(
                amount_label,
                (
                    topleft[0] + 20 - amount_label.get_width() / 2,
                    topleft[1] + 60 - amount_label.get_height() / 2,
                ),
            )

        exp_width = 100
        pygame.draw.rect(
            s,
            config.WHITE_TRANSPARENT,
            (topleft[0], topleft[1] + 120, exp_width, 16),
            border_radius=3,
        )
        maximum_growable_mass = organ.get_maximum_growable_mass()
        relative_mass = organ.get_mass() / maximum_growable_mass if maximum_growable_mass is not 0 else 1
        width = min(int(exp_width / 1 * relative_mass), exp_width)
        pygame.draw.rect(
            s,
            (255, 255, 255),
            (topleft[0], topleft[1] + 120, width, 16),
            border_radius=3,
        )  # exp
        text_organ_mass = self.asset_handler.SMALL_FONT.render(
            "{:.1f} / {:.1f}".format(
                organ.get_mass() * factor, organ.get_maximum_growable_mass() * factor
            ),
            True,
            (0, 0, 0),
        )

        s.blit(
            text_organ_mass,
            dest=(
                topleft[0] + exp_width / 2 - text_organ_mass.get_width() / 2,
                topleft[1] + 120,
            ),
        )
        # indicate blocked organ
        if organ.blocked_growth:
            if organ.type == Plant.LEAF:
                pygame.draw.rect(s, config.RED, (topleft[0], topleft[1], 100, 370), border_radius=3, width=3)

                label = self.asset_handler.TITLE_FONT.render("LEAF GROWTH BLOCKED: Buy new leaves to grow", True, config.BLACK)
                width = label.get_width() + 10
                height = label.get_height() + 10
                pygame.draw.rect(s, config.WHITE_TRANSPARENT, (topleft[0], topleft[1] + 380, width, height),
                                 border_radius=3)
                # pygame.draw.rect(s, config.WHITE, (topleft[0], topleft[1]+380, width, height), border_radius=3, width=3)
                s.blit(label, (topleft[0] + 5, topleft[1] + 385))

    def draw_production(self, s):
        topleft = self.production_topleft
        # headbox
        self.draw_organ_detail_temp(
            s,
            self.plant.organs[0],
            topleft,
            self.label_leaf
        )
        self.draw_organ_detail_temp(
            s,
            self.plant.organs[1],
            (topleft[0] + 110, topleft[1]),
            self.label_stem,
        )
        self.draw_organ_detail_temp(
            s,
            self.plant.organs[2],
            (topleft[0] + 220, topleft[1]),
            self.label_root,
        )

        # WATER
        topleft = (topleft[0] + 330, topleft[1])
        pygame.draw.rect(
            s, config.WHITE, (topleft[0], topleft[1], 140, 30), border_radius=3
        )
        s.blit(
            self.label_water,
            dest=(
                topleft[0] + 70 - self.label_water.get_width() / 2,
                topleft[1],
            ),
        )

        width = 140

        pygame.draw.rect(
            s,
            config.WHITE_TRANSPARENT,
            (topleft[0], topleft[1] + 40, width, 30),
            border_radius=3,
        )

        pygame.draw.rect(
            s,
            config.BLUE,
            (topleft[0], topleft[1] + 40, int(width * self.plant.water_pool/self.plant.max_water_pool), 30),
            border_radius=3,
        )  # exp
        text_water_pool = self.asset_handler.FONT.render(
            "{:.0f} MMol".format(self.plant.water_pool / 1000), True, (0, 0, 0)
        )
        s.blit(
            text_water_pool,
            dest=(
                topleft[0] + width / 2 - text_water_pool.get_width() / 2,
                topleft[1] + 45,
            ),
        )  # Todo change x, y

        # draw starch bar
        organ = self.plant.organ_starch
        pygame.draw.rect(
            s,
            config.WHITE,
            (topleft[0], topleft[1] + 100, 140, 30),
            border_radius=3,
        )
        s.blit(
            self.label_starch,
            dest=(
                topleft[0] + 70 - self.label_starch.get_width() / 2,
                topleft[1] + 100,
            ),
        )

        exp_height = 200
        pygame.draw.rect(
            s,
            config.WHITE_TRANSPARENT,
            (topleft[0] + 100, topleft[1] + 150, 30, exp_height),
            border_radius=3,
        )
        exp = organ.mass / organ.max_pool
        # factor = 10000
        height = min(int(exp_height / 1 * exp), exp_height)
        pygame.draw.rect(
            s,
            (255, 255, 255),
            (
                topleft[0] + 100,
                topleft[1] + 150 + exp_height - height,
                30,
                height,
            ),
            border_radius=3,
        )  # exp
        if organ.percentage > 0:
            s.blit(
                self.label_producing,
                dest=(
                    topleft[0] + 100,
                    topleft[1]
                    + 150
                    + 100
                    - self.label_producing.get_height() / 2,
                ),
            )
        else:
            s.blit(
                self.label_consuming,
                dest=(
                    topleft[0] + 100,
                    topleft[1]
                    + 150
                    + 100
                    - self.label_consuming.get_height() / 2,
                ),
            )
