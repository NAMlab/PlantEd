import argparse
import os
import random
import sys
import time
from datetime import datetime
from typing import List

import pygame
from pygame.locals import *

import config
from PlantEd.analysis import scoring
from PlantEd.analysis.logger import Log
from PlantEd.camera import Camera
from PlantEd.client.client import Client
from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.client.growth_rates import GrowthRates
from PlantEd.data import assets
from PlantEd.fba.dynamic_model import DynamicModel
from PlantEd.gameobjects.bee import Bee, Hive
from PlantEd.gameobjects.bug import Bug
from PlantEd.gameobjects.level_card import Card
from PlantEd.gameobjects.plant import Plant
from PlantEd.gameobjects.shop import (
    Shop,
    Shop_Item,
    FloatingShopItem,
    FloatingShop,
)
from PlantEd.gameobjects.snail import Snail
from PlantEd.gameobjects.tree import Tree
from PlantEd.gameobjects.water_reservoir import Water_Grid, Base_water
from PlantEd.server.server import Server
from PlantEd.ui import UI
from PlantEd.utils.button import Button, Slider, ToggleButton, Textbox
from PlantEd.utils.gametime import GameTime
from PlantEd.weather import Environment

# currentdir = os.path.abspath('../..')
# parentdir = os.path.dirname(currentdir)
# sys.path.insert(0, parentdir)
pygame.init()
# ctypes.windll.user32.SetProcessDPIAware()
true_res = (
    1920,
    1080,
)  # (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(
    true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16
)
# pygame.display.toggle_fullscreen()
# print(pygame.display.list_modes(depth=0, flags=pygame.FULLSCREEN, display=0))
# screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
# screen_high = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT*2), pygame.DOUBLEBUF)
tmp_screen = pygame.display.set_mode(
    true_res, pygame.FULLSCREEN | pygame.SRCALPHA
)
temp_surface = pygame.Surface((1920, 2160), pygame.SRCALPHA)
# screen_high = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT*2), pygame.SRCALPHA)
GROWTH = 24
RECALC = 25
WIN = pygame.USEREVENT + 1

# stupid, change dynamically
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
plant_pos = (
    SCREEN_WIDTH - SCREEN_WIDTH / 4,
    SCREEN_HEIGHT - SCREEN_HEIGHT / 5,
)

GREEN = (19, 155, 23)
BLUE = (75, 75, 200)
SKY_BLUE = (169, 247, 252)

plant = None

import logging

logger = logging.getLogger(__name__)


def shake():
    s = (
        -1
    )  # looks unnecessary but maybe cool, int((random.randint(0,1)-0.5)*2)
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


class OptionsScene:
    def __init__(self):
        self.options = config.load_options()

        self.option_label = config.MENU_TITLE.render(
            "Options", True, config.WHITE
        )
        self.sound_label = config.MENU_SUBTITLE.render(
            "Sound", True, config.WHITE
        )
        self.music_label = config.BIGGER_FONT.render(
            "Music", True, config.WHITE
        )
        self.efects_label = config.BIGGER_FONT.render(
            "Effects", True, config.WHITE
        )
        self.network_label = config.MENU_SUBTITLE.render(
            "Network", True, config.WHITE
        )
        self.upload_score_label = config.BIGGER_FONT.render(
            "Upload Score", True, config.WHITE
        )
        self.name_label = config.MENU_SUBTITLE.render(
            "Name", True, config.WHITE
        )

        self.label_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        center_w, center_h = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2

        self.music_slider = Slider(
            (center_w - 475, 450, 15, 200),
            config.FONT,
            (50, 20),
            percent=self.options["music"] * 100,
            active=True,
        )
        self.effect_slider = Slider(
            (center_w - 175, 450, 15, 200),
            config.FONT,
            (50, 20),
            percent=self.options["effects"] * 100,
            active=True,
        )
        self.upload_score_button = ToggleButton(
            center_w + 300,
            400,
            50,
            50,
            None,
            pressed=self.options["upload_score"],
            cross=True,
        )

        self.back = Button(
            center_w - 200,
            930,
            200,
            50,
            [self.cancel_return_to_menu],
            config.BIGGER_FONT,
            "BACK",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.apply = Button(
            center_w + 50,
            930,
            200,
            50,
            [self.return_to_menu],
            config.BIGGER_FONT,
            "APPLY",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )

        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add(
            [self.upload_score_button, self.back, self.apply]
        )

        self.textbox = Textbox(
            center_w + 160,
            600,
            280,
            50,
            config.BIGGER_FONT,
            self.options["name"],
            background_color=config.LIGHT_GRAY,
            textcolor=config.WHITE,
            highlight_color=config.WHITE,
        )

        self.init_labels()

    def return_to_menu(self):
        config.write_options(self.get_options())
        self.manager.go_to(TitleScene(self.manager))

    def cancel_return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def init_labels(self):
        center_w, center_h = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2

        pygame.draw.line(
            self.label_surface, config.WHITE, (100, 900), (1820, 900)
        )

        self.label_surface.blit(
            self.option_label,
            (center_w - self.option_label.get_width() / 2, 100),
        )
        self.label_surface.blit(
            self.sound_label,
            (center_w - 300 - self.sound_label.get_width() / 2, 300),
        )
        self.label_surface.blit(
            self.music_label,
            (center_w - 450 - self.music_label.get_width() / 2, 400),
        )
        self.label_surface.blit(
            self.efects_label,
            (center_w - 150 - self.efects_label.get_width() / 2, 400),
        )
        self.label_surface.blit(
            self.network_label,
            (center_w + 300 - self.network_label.get_width() / 2, 300),
        )
        self.label_surface.blit(
            self.upload_score_label,
            (center_w + 150 - self.upload_score_label.get_width() / 2, 400),
        )
        self.label_surface.blit(
            self.name_label,
            (center_w + 300 - self.name_label.get_width() / 2, 500),
        )

        self.label_surface.blit(
            assets.img("plant_growth_pod/plant_growth_10.PNG"), (1300, 400)
        )

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
        options = {
            "music": self.music_slider.get_percentage() / 100,
            "effects": self.effect_slider.get_percentage() / 100,
            "upload_score": self.upload_score_button.button_down,
            "name": self.textbox.text,
        }
        return options

    def render(self, screen):
        screen.fill(config.LIGHT_GRAY)
        screen.blit(self.label_surface, (0, 0))
        self.music_slider.draw(screen)
        self.effect_slider.draw(screen)
        self.button_sprites.draw(screen)
        self.textbox.draw(screen)


class DefaultGameScene(object):
    def __init__(self):
        options = config.load_options()

        global plant

        # pygame.mixer.music.load('../assets/background_music.mp3')
        assets.song("background_music.mp3", options["music"])

        # pygame.mixer.music.set_volume(options["music"]/10)
        pygame.mixer.music.play(-1, 0)
        pygame.mouse.set_visible(True)
        self.pause = False
        self.pause_label = config.MENU_TITLE.render(
            "Game Paused", True, config.WHITE
        )
        self.pause_button_resume = Button(
            700,
            560,
            200,
            50,
            [self.resume],
            config.BIG_FONT,
            "RESUME",
            border_w=2,
        )
        self.pause_button_exit = Button(
            1020,
            560,
            200,
            50,
            [self.quit],
            config.BIG_FONT,
            "QUIT GAME",
            border_w=2,
        )
        self.camera = Camera(offset_y=0)
        self.gametime = GameTime.instance()
        self.log = Log()  # can be turned off
        self.water_grid = Water_Grid(pos=(0, 900))
        # self.water_grid.add_reservoir(Water_Reservoir((500, 1290), 36, 30))
        # self.water_grid.add_reservoir(Water_Reservoir((900, 1190), 36, 25))
        # self.water_grid.add_reservoir(Water_Reservoir((1660, 1310), 36, 40))

        self.model = DynamicModel(self.gametime, self.log)

        model = self.model

        logger.info("Starting Server and client")
        logger.debug("Creating server")
        self.server = Server(model=model)
        logger.debug("Starting server")
        self.server.start()

        logger.debug("Starting Client")
        self.client = Client()

        self.plant = Plant(
            pos=(
                config.SCREEN_WIDTH / 2,
                config.SCREEN_HEIGHT - config.SCREEN_HEIGHT / 5,
            ),
            camera=self.camera,
            client=self.client,
            water_grid=self.water_grid,
            growth_boost=1,
        )

        self.water_grid.add_base_water(
            Base_water(
                10,
                100,
                config.SCREEN_WIDTH,
                config.SCREEN_HEIGHT + 450,
                config.DARK_BLUE,
                config.LIGHT_BLUE,
            )
        )
        self.environment = Environment(
            plant=self.plant,
            client=self.client,
            water_grid=self.water_grid,
            nitrate=0,
            water=0,
            gametime=self.gametime,
        )

        growth_rates = GrowthRates("grams", 0, 0, 0, 0, 0, 0)
        self.ui = UI(
            scale=1,
            plant=self.plant,
            client=self.client,
            environment=self.environment,
            camera=self.camera,
            growth_rates=growth_rates,
        )

        """example_skills_leaf = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     callback=self.plant.organs[2].set_root_tier,post_hover_message=self.ui.post_hover_message, message="Skill Leaf") for i in range(0,4)]
        example_skills_stem = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Stem") for i in range(0,2)]
        example_skills_root = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                     post_hover_message=self.ui.post_hover_message, message="Skill Root") for i in range(0,2)]
        example_skills_starch = [Skill(assets.img("skills/leaf_not_skilled.png"),assets.img("skills/leaf_skilled.png"),
                                       post_hover_message=self.ui.post_hover_message, message="Skill Starch") for i in range(0,3)]
        self.skill_system = Skill_System((1700,420),self.plant, example_skills_leaf, example_skills_stem, example_skills_root, example_skills_starch)
"""
        self.entities = []

        self.hive = Hive((1500, 600), 10, self.plant, self.camera, 10)
        self.entities.append(self.hive)

        for i in range(0, 5):
            bee = Bee(
                (190 * random.randint(0, 10), random.randint(0, 800)),
                pygame.Rect(
                    0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - 200
                ),
                [
                    assets.img("bee/{}.PNG".format(i), (64, 64))
                    for i in range(6)
                ],
                self.camera,
                self.plant.organs[3].pollinate,
                hive_pos=(1500, 600),
            )
            self.entities.append(bee)

        for i in range(0, 10):
            bug = Bug(
                (190 * random.randint(0, 10), 900 + random.randint(0, 200)),
                pygame.Rect(0, 900, config.SCREEN_WIDTH, 240),
                [
                    assets.img("bug_purple/bug_purple_{}.png".format(i))
                    for i in range(0, 3)
                ],
                self.camera,
            )
            self.entities.append(bug)

        self.tree = Tree(
            (1100, 20),
            [
                (assets.img("tree/{index}.PNG".format(index=i), (1024, 1024)))
                for i in range(0, 4)
            ],
            self.environment,
        )
        # self.tree = Tree((1100,20),[assets.img("tree/1.PNG", (1024,1024))], self.environment)
        # self.tree = Tree((1100,20),[assets.img("tree/2.PNG", (1024,1024))], self.environment)
        # self.tree = Tree((1100,20),[assets.img("tree/3.PNG", (1024,1024))], self.environment)
        self.entities.append(self.tree)

        for i in range(0, 3):
            snail = Snail(
                (190 * random.randint(0, 10), 870 + random.randint(0, 10)),
                pygame.Rect(0, 870, config.SCREEN_WIDTH, 240),
                [assets.img("snail/{}.png".format(i)) for i in range(0, 3)],
                [assets.img("snail/{}.png".format(i)) for i in range(3, 6)],
                self.camera,
            )
            self.entities.append(snail)
        # self.ui.floating_elements.append(FloatingElement((500,500),Rect(400,400,200,200),image=assets.img("stomata/stomata_open.png")))

        # shop items are to be defined by the level
        add_leaf_item = Shop_Item(
            assets.img("leaf_small.PNG", (64, 64)),
            self.activate_add_leaf,
            condition=self.plant.organs[1].check_can_add_leaf,
            condition_not_met_message="Level up your stem to buy more leaves",
            post_hover_message=self.ui.hover.set_message,
            message="Leaves enable your plant to produce energy.",
        )

        self.shop = Shop(
            rect=Rect(1700, 120, 200, 450),
            shop_items=[add_leaf_item],
            client=self.client,
            water_grid=self.water_grid,
            plant=self.plant,
            post_hover_message=self.ui.hover.set_message,
            active=False,
        )

        self.shop.shop_items.append(
            Shop_Item(
                assets.img("root_lateral.PNG", (64, 64)),
                self.shop.root_item.activate,
                condition=self.plant.organs[2].check_can_add_root,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Roots are grown to improve water and nitrate intake.",
            )
        )

        self.shop.shop_items.append(
            Shop_Item(
                assets.img("root_lateral.PNG", (64, 64)),
                self.plant.organs[1].activate_add_branch,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Branches will provide more spots for leaves or flowers.",
            )
        )

        self.shop.shop_items.append(
            Shop_Item(
                assets.img("sunflowers/1.PNG", (64, 64)),
                self.plant.organs[3].activate_add_flower,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Flowers will enable you to start seed production.",
            )
        )

        self.shop.add_shop_item(["watering", "blue_grain", "spraycan"])

        self.floating_shop = FloatingShop((0, 0))
        add_leaf_item_floating = FloatingShopItem(
            (0, 0),
            self.activate_add_leaf,
            assets.img("leaf_small.PNG", (64, 64)),
            1,
            self.plant,
        )
        add_branch_item_floating = FloatingShopItem(
            (0, 0),
            self.plant.organs[1].activate_add_branch,
            assets.img("leaf_small.PNG", (64, 64)),
            1,
            self.plant,
        )
        add_flower_item_floating = FloatingShopItem(
            (0, 0),
            self.plant.organs[3].activate_add_flower,
            assets.img("leaf_small.PNG", (64, 64)),
            1,
            self.plant,
        )

        self.floating_shop.add_item(add_leaf_item_floating)
        self.floating_shop.add_item(add_branch_item_floating)
        self.floating_shop.add_item(add_flower_item_floating)
        self.plant.organs[0].floating_shop = self.floating_shop
        self.plant.organs[1].floating_shop = self.floating_shop
        self.plant.organs[2].floating_shop = self.floating_shop

        # start plant growth timer
        pygame.time.set_timer(GROWTH, 1000)

    def activate_add_leaf(self):
        # if there are funds, buy a leave will enable leave @ mouse pos until clicked again
        self.plant.organs[0].activate_add_leaf()

    def quit(self):
        self.log.close_file()
        self.log.close_model_file()
        pygame.quit()
        sys.exit()

    def resume(self):
        self.pause = False
        self.gametime.unpause()

    def toggle_pause(self):
        self.pause = not self.pause
        if self.pause:
            self.gametime.pause()
        else:
            self.gametime.unpause()

    def handle_events(self, events: List[pygame.event.Event]):
        for e in events:
            if self.pause:
                self.pause_button_resume.handle_event(e)
                self.pause_button_exit.handle_event(e)
            if e.type == GROWTH:
                starch_percent = self.plant.organ_starch.percentage
                if starch_percent < 0:
                    starch_percent = 0

                flowering_flowers = self.plant.organs[
                    3
                ].get_flowering_flowers()
                flower_percent = 0
                # Todo fix percentages
                for flower in flowering_flowers:
                    flower_percent += 10
                    self.plant.organs[3].percentage = flower_percent

                # print(leaf_percent, stem_percent, root_percent, starch_percent)

                growth_percent = GrowthPercent(
                    leaf=self.plant.organs[0].percentage,
                    stem=self.plant.organs[1].percentage,
                    root=self.plant.organs[2].percentage,
                    starch=self.plant.organ_starch.percentage,
                    flower=self.plant.organs[3].percentage,
                )

                growth_rates = self.client.growth_rate(
                    growth_percent=growth_percent
                )
                self.ui.growth_rates = growth_rates

                self.plant.update_growth_rates(growth_rates)

            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.toggle_pause()
            if e.type == KEYDOWN and e.key == K_o:
                self.floating_shop.activate((500, 500))
            if e.type == KEYDOWN and e.key == K_k:
                # self.ui.init_flowering_ui()
                self.plant.organs[3].start_flowering()
            if e.type == KEYDOWN and e.key == K_h:
                # self.ui.init_flowering_ui()
                flower_pos = (
                    self.plant.organs[3].flowers[0]["x"]
                    + self.plant.organs[3].flowers[0]["offset_x"] / 2,
                    self.plant.organs[3].flowers[0]["y"]
                    + self.plant.organs[3].flowers[0]["offset_y"] / 2
                    - 20,
                )
                self.hive.start_pollination(flower_pos)

            # if e.type == KEYDOWN and e.key == K_p:
            #     NITRATE = "Nitrate_tx_root"
            #     WATER = "H2O_tx_root"
            #     PHOTON = "Photon_tx_leaf"
            #     STARCH_IN = "Starch_in_tx_stem"
            #
            #     water_in = self.model.get_bounds(WATER)[1]
            #     nitrate_in = self.model.get_bounds(NITRATE)[1]
            #     starch_in = self.model.get_bounds(STARCH_IN)[1]
            #     photon_in = self.model.get_bounds(PHOTON)[1]
            #
            #     leaf_mass = self.plant.organs[0].mass
            #     stem_mass = self.plant.organs[1].mass
            #     root_mass = self.plant.organs[2].mass
            #     seed_mass = 0
            #
            #     water_pool = self.model.water_pool
            #     starch_pool = self.plant.organ_starch.mass
            #     nitrate_pool = self.model.nitrate_pool
            #
            #     leaf_rate = self.model.growth_rates.leaf_rate
            #     stem_rate = self.model.growth_rates.stem_rate
            #     root_rate = self.model.growth_rates.root_rate
            #     seed_rate = 0
            #
            #     ticks = self.gametime.get_time()
            #     day = 1000 * 60 * 60 * 24
            #     hour = day / 24
            #     min = hour / 60
            #     days = int(ticks / day)
            #     hours = int((ticks % day) / hour)
            #     minutes = int((ticks % hour) / min)
            #
            #     self.log.append_model_row(days, hours, minutes, water_in, nitrate_in, starch_in, photon_in, leaf_mass, stem_mass, root_mass,
            #                               seed_mass, water_pool, starch_pool, nitrate_pool, leaf_rate, stem_rate,
            #                               root_rate, seed_rate)
            if e.type == WIN:
                if self.log:
                    # self.log.write_log(self.ui.name_label)
                    self.log.close_file()
                    self.log.close_model_file()
                scoring.upload_score(self.ui.name, self.gametime.get_time())
                self.manager.go_to(CustomScene())
            self.ui.handle_event(e)
            self.shop.handle_event(e)
            self.floating_shop.handle_event(e)

            self.plant.handle_event(e)
            # self.environment.handle_event(e)
            for entity in self.entities:
                entity.handle_event(e)
            self.camera.handle_event(e)

    def check_game_end(self, days):
        if days > config.MAX_DAYS:
            pygame.event.post(pygame.event.Event(WIN))

    def update(self, dt):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        hours = (ticks % day) / hour
        if 8 < hours < 20:
            # print(hours)
            shadow_map, resolution = self.environment.calc_shadowmap(
                self.plant.organs[0].leaves,
                sun_dir=(((-(20 / 12) * hours) + 23.33), 1),
            )
            # apply shadow penalty to leaves
            for leaf in self.plant.organs[0].leaves:
                x = int((leaf["x"] - leaf["offset_x"]) / resolution)
                y = int((leaf["y"] - leaf["offset_y"]) / resolution)

                width = int(leaf["image"].get_width() / resolution)
                height = int(leaf["image"].get_height() / resolution)

                # rect = pygame.Rect(x,y,width,height)

                dots = width * height
                shadow_dots = 0
                for i in range(x, x + width):
                    for j in range(y, y + height):
                        shadow_dots += shadow_map[i, j]

                leaf["shadow_score"] = shadow_dots / dots
                # print(leaf["x"], leaf["y"], dots, shadow_dots, shadow_dots/(dots*3))
            # print((-(20/12)*hours)+23.33)
        else:
            self.environment.shadow_map = None
        # get root grid, water grid
        self.water_grid.set_root_grid(self.plant.organs[2].get_root_grid())
        self.water_grid.actual_drain_rate = (
            self.client.get_actual_water_drain()
        )
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

        self.model.update(
            dt,
            self.plant.organs[0].mass,
            self.plant.organs[1].mass,
            self.plant.organs[2].mass,
            self.plant.get_PLA(),
            max(self.environment.get_sun_intensity(), 0),
            self.water_grid.max_drain_rate,
            self.plant.get_biomass(),
            self.environment.humidity,
            self.environment.temperature,
        )

    def render(self, screen):
        screen.fill((0, 0, 0))
        if self.pause:
            screen.blit(
                self.pause_label, (960 - self.pause_label.get_width() / 2, 300)
            )
            self.pause_button_resume.draw(screen)
            self.pause_button_exit.draw(screen)
            return

        self.environment.draw_background(temp_surface)

        for entity in self.entities:
            entity.draw(temp_surface)
        self.plant.draw(temp_surface)

        self.environment.draw_foreground(temp_surface)
        self.water_grid.draw(temp_surface)
        self.environment.draw_shadows(temp_surface)
        self.floating_shop.draw(temp_surface)
        self.shop.draw(temp_surface)

        self.ui.draw(temp_surface)
        screen.blit(temp_surface, (0, self.camera.offset_y))

        screen.blit(temp_surface, (0, 0))


class TitleScene(object):
    def __init__(self, manager=None):
        super(TitleScene, self).__init__()
        self.title = config.MENU_TITLE.render("PlantEd", True, config.WHITE)
        self.center_h = config.SCREEN_HEIGHT / 2 + 100
        self.center_w = config.SCREEN_WIDTH / 2
        self.card_0 = Card(
            (self.center_w, self.center_h - 100),
            assets.img("menu/gatersleben.JPG", (512, 512)),
            "Gatersleben",
            callback=manager.go_to,
            callback_var=DefaultGameScene,
            keywords="Beginner, Medium Temperatures",
        )
        # self.card_1 = Card((self.center_w,self.center_h-100),assets.img("menu/tutorial.JPG",(512,512)), "Tutorial",
        #                   callback=manager.go_to, callback_var=DevScene,keywords="Beginner, Easy")
        # self.card_2 = Card((self.center_w+260,self.center_h-100),assets.img("menu/dev.jpg",(512,512)), "Dev ",
        #                   callback=manager.go_to, callback_var=DevScene,keywords="Test Stuff")

        self.credit_button = Button(
            self.center_w - 450,
            930,
            200,
            50,
            [self.go_to_credtis],
            config.BIGGER_FONT,
            "CREDTIS",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.options_button = Button(
            self.center_w - 200,
            930,
            200,
            50,
            [self.go_to_options],
            config.BIGGER_FONT,
            "OPTIONS",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.scores_button = Button(
            self.center_w + 50,
            930,
            200,
            50,
            [self.go_to_scores],
            config.BIGGER_FONT,
            "SCORES",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.quit_button = Button(
            self.center_w + 300,
            930,
            200,
            50,
            [self.quit],
            config.BIGGER_FONT,
            "QUIT",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )

        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add(
            [
                self.quit_button,
                self.credit_button,
                self.options_button,
                self.scores_button,
            ]
        )

    def render(self, screen):
        screen.fill(config.LIGHT_GRAY)
        screen.blit(
            self.title, (self.center_w - self.title.get_width() / 2, 100)
        )
        self.card_0.draw(screen)
        # self.card_1.draw(screen)
        # self.card_2.draw(screen)
        pygame.draw.line(screen, config.WHITE, (100, 900), (1820, 900))
        self.button_sprites.draw(screen)

    def update(self, dt):
        self.card_0.update(dt)
        # self.card_1.update(dt)
        # self.card_2.update(dt)

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
            # self.card_1.handle_event(e)
            # self.card_2.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)
            # self.watering_can.handle_event(e)


class CustomScene(object):
    def __init__(self):
        super(CustomScene, self).__init__()
        self.text1 = config.MENU_TITLE.render(
            "Top Plants", True, (255, 255, 255)
        )
        # self.text3 = config.BIGGER_FONT.render('> press any key to restart <', True, (255,255,255))

        self.name_txt = config.BIGGER_FONT.render(
            "Name", True, (255, 255, 255)
        )
        self.score_txt = config.BIGGER_FONT.render(
            "Score", True, (255, 255, 255)
        )
        self.submit_txt = config.BIGGER_FONT.render(
            "Submit Date", True, (255, 255, 255)
        )

        self.button_sprites = pygame.sprite.Group()
        self.back = Button(
            860,
            930,
            200,
            50,
            [self.return_to_menu],
            config.BIGGER_FONT,
            "BACK",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.button_sprites.add(self.back)

        self.winners = scoring.get_scores()
        self.scores = []
        self.names = []
        self.datetimes = []

        self.winners = sorted(self.winners, key=lambda x: x["score"])

        for winner in self.winners:
            score = self.get_day_time(winner["score"])
            score = config.BIGGER_FONT.render(score, True, (255, 255, 255))
            self.scores.append(score)
            name = config.BIGGER_FONT.render(
                winner["name"], True, (255, 255, 255)
            )
            self.names.append(name)
            datetime_added = config.BIGGER_FONT.render(
                datetime.utcfromtimestamp(winner["datetime_added"]).strftime(
                    "%d/%m/%Y %H:%M"
                ),
                True,
                (255, 255, 255),
            )
            self.datetimes.append(datetime_added)

    def return_to_menu(self):
        pygame.quit()
        sys.exit()
        # self.manager.go_to(TitleScene(self.manager))

    def get_day_time(self, ticks):
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        min = hour / 60
        second = min / 60
        days = str(int(ticks / day))
        hours = str(int((ticks % day) / hour))
        minutes = str(int((ticks % hour) / min))
        return days + " Days " + hours + " Hours " + minutes + " Minutes"

    def render(self, screen):
        screen.fill((50, 50, 50))
        screen.blit(
            self.text1, (SCREEN_WIDTH / 2 - self.text1.get_width() / 2, 100)
        )

        pygame.draw.line(screen, config.WHITE, (100, 300), (1820, 300))

        # screen.blit(self.name_txt, (SCREEN_WIDTH / 4 - self.name_txt.get_width()/2, SCREEN_HEIGHT / 3))
        # screen.blit(self.score_txt, (SCREEN_WIDTH / 2 - self.score_txt.get_width()/2, SCREEN_HEIGHT / 3))
        # screen.blit(self.submit_txt, (SCREEN_WIDTH / 4*2 - self.submit_txt.get_width()/2, SCREEN_HEIGHT / 3))

        for i in range(0, min(10, len(self.winners))):
            screen.blit(
                self.names[i],
                (
                    SCREEN_WIDTH / 4 - self.names[i].get_width() / 2,
                    SCREEN_HEIGHT / 3 + SCREEN_HEIGHT / 20 * i,
                ),
            )
            screen.blit(
                self.scores[i],
                (
                    SCREEN_WIDTH / 2 - self.scores[i].get_width() / 2,
                    SCREEN_HEIGHT / 3 + SCREEN_HEIGHT / 20 * i,
                ),
            )
            screen.blit(
                self.datetimes[i],
                (
                    SCREEN_WIDTH / 4 * 3 - self.datetimes[i].get_width() / 2,
                    SCREEN_HEIGHT / 3 + SCREEN_HEIGHT / 20 * i,
                ),
            )

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


class Credits:
    def __init__(self):
        super(Credits, self).__init__()
        self.center_w, self.center_h = (
            config.SCREEN_WIDTH / 2,
            config.SCREEN_HEIGHT / 2,
        )
        self.label_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        self.init_labels()
        self.button_sprites = pygame.sprite.Group()
        self.back = Button(
            860,
            930,
            200,
            50,
            [self.return_to_menu],
            config.BIGGER_FONT,
            "BACK",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.button_sprites.add(self.back)

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def init_labels(self):
        self.label_surface.fill(config.LIGHT_GRAY)
        self.made_by_label = config.MENU_TITLE.render(
            "MADE BY", True, config.WHITE
        )
        self.daniel = config.MENU_SUBTITLE.render(
            "Daniel Koch", True, config.WHITE
        )
        self.jj = config.MENU_SUBTITLE.render(
            "Jedrzej J. Szymanski", True, config.WHITE
        )
        self.nadine = config.MENU_SUBTITLE.render(
            "Nadine Töpfer", True, config.WHITE
        )
        self.mona = config.MENU_SUBTITLE.render(
            "Stefano A. Cruz", True, config.WHITE
        )
        self.pouneh = config.MENU_SUBTITLE.render(
            "Pouneh Pouramini", True, config.WHITE
        )

        pygame.draw.line(
            self.label_surface, config.WHITE, (100, 300), (1820, 300)
        )

        self.label_surface.blit(
            self.made_by_label,
            (self.center_w - self.made_by_label.get_width() / 2, 100),
        )
        self.label_surface.blit(
            self.daniel, (self.center_w - self.daniel.get_width() / 2, 400)
        )
        self.label_surface.blit(
            self.jj, (self.center_w - self.jj.get_width() / 2, 480)
        )
        self.label_surface.blit(
            self.pouneh, (self.center_w - self.pouneh.get_width() / 2, 560)
        )
        self.label_surface.blit(
            self.mona, (self.center_w - self.mona.get_width() / 2, 640)
        )
        self.label_surface.blit(
            self.nadine, (self.center_w - self.nadine.get_width() / 2, 720)
        )

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
        screen.blit(self.label_surface, (0, 0))
        self.button_sprites.draw(screen)


class SceneMananger(object):
    def __init__(self):
        self.go_to(TitleScene(self))

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self

    def render(self, screen):
        self.scene.render(screen)
        # screen.blit(screen_high,(0,-100))
        # self.camera.render(screen_high, screen)


def main():
    pygame.init()
    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_mode((0, 0), pygame.RESIZABLE)
    pygame.display.set_caption("PlantEd_0.1")
    timer = pygame.time.Clock()
    running = True
    # camera = Camera()
    manager = SceneMananger()

    pause = False
    pause_label = config.BIGGER_FONT.render("PAUSE", True, (255, 255, 255))

    while running:
        dt = timer.tick(60) / 1000.0
        fps = str(int(timer.get_fps()))
        fps_text = config.FONT.render(fps, False, (255, 255, 255))

        if pygame.event.get(QUIT):
            running = False
            return

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        screen.blit(fps_text, (500, 500))
        # camera.render(screen)
        pygame.display.update()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--logLevel",
        type=str,
        default="WARNING",
        metavar="",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the detail of the log events (default: %(default)s)",
    )

    parser.add_argument(
        "--logFile",
        type=str,
        default="",
        metavar="",
        help="The file in which the log should be saved. "
        "Attention this will be overwritten. "
        "By default, no log file is created.",
    )

    args = parser.parse_args()

    if args.logFile != "":
        logging.basicConfig(
            level=args.logLevel,
            format="%(asctime)s %(name)s %(levelname)s:%(message)s",
            datefmt="%H:%M:%S",
            filename=args.logFile,
            filemode="w+",
        )
    else:
        logging.basicConfig(
            level=args.logLevel,
            format="%(asctime)s %(name)s %(levelname)s:%(message)s",
            datefmt="%H:%M:%S",
        )

    main()
