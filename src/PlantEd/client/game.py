import asyncio
import json
import os
import random
import sys
import time
from datetime import datetime
from typing import List

import numpy as np
import pandas
import pygame
import websockets
from pygame.locals import *

from PlantEd import config
from PlantEd.client.analysis import scoring
from PlantEd.client.analysis.logger import Log
from PlantEd.client.camera import Camera
from PlantEd.client.client import Client
from PlantEd.constants import MAX_NITRATE_PER_CELL, MAX_WATER_PER_CELL, Vmax, Km, ROOT_COST, BRANCH_COST, \
    FLOWER_COST, LEAF_COST, MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT
from PlantEd.data.assets import AssetHandler
from PlantEd.data.sound_control import SoundControl
from PlantEd.client.gameobjects.bee import Hive
from PlantEd.client.gameobjects.bug import Bug
from PlantEd.client.utils.grid import Grid
from PlantEd.client.gameobjects.level_card import Card
from PlantEd.client.gameobjects.plant import Plant, Root
from PlantEd.client.gameobjects.shop import (
    Shop,
    Shop_Item,
    FloatingShopItem,
    FloatingShop,
)
from PlantEd.client.gameobjects.snail import SnailSpawner
from PlantEd.client.gameobjects.tree import Tree
from PlantEd.client.gameobjects.water_reservoir import Water_Grid, Base_water
from PlantEd.client.ui import UI
from PlantEd.client.utils import plot
from PlantEd.client.utils.animation import Animation
from PlantEd.client.utils.button import Button, Slider, ToggleButton, Textbox
from PlantEd.client.utils.gametime import GameTime
from PlantEd.client.utils.narrator import Narrator
from PlantEd.client.utils.particle import ParticleSystem, ParticleExplosion
from PlantEd.client.weather import Environment
from PlantEd.server.game import Game as Server_Game
from PlantEd.server.lsystem import DictToRoot

true_res = (
    1920,
    1080,
)  # (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))

temp_surface = pygame.Surface((1920, 2160), pygame.SRCALPHA)
GROWTH = 26
WIN = pygame.USEREVENT + 1

# stupid, change dynamically
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
plant_pos = (
    SCREEN_WIDTH - SCREEN_WIDTH / 4,
    SCREEN_HEIGHT - SCREEN_HEIGHT / 5,
)


class OptionsScene:
    def __init__(self):
        self.options = config.load_options()
        self.sound_control = SoundControl()
        self.asset_handler = AssetHandler.instance()
        self.option_label = self.asset_handler.MENU_TITLE.render(
            "Options", True, config.WHITE
        )
        self.sound_label = self.asset_handler.MENU_SUBTITLE.render(
            "Sound", True, config.WHITE
        )
        self.music_label = self.asset_handler.BIGGER_FONT.render(
            "Music", True, config.WHITE
        )
        self.sfx_label = self.asset_handler.BIGGER_FONT.render(
            "SFX", True, config.WHITE
        )
        self.narator_label = self.asset_handler.BIGGER_FONT.render(
            "Narator", True, config.WHITE
        )
        self.network_label = self.asset_handler.MENU_SUBTITLE.render(
            "Network", True, config.WHITE
        )
        self.upload_score_label = self.asset_handler.BIGGER_FONT.render(
            "Upload Score", True, config.WHITE
        )
        self.name_label = self.asset_handler.MENU_SUBTITLE.render(
            "Name", True, config.WHITE
        )

        self.label_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )

        center_w, center_h = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2

        self.music_slider = Slider(
            (center_w - 475, 450, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["music_volume"] * 100,
            active=True,
        )
        self.sfx_slider = Slider(
            (center_w - 325, 450, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["sfx_volume"] * 100,
            active=True,
        )
        self.narator_slider = Slider(
            (center_w - 175, 450, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["narator_volume"] * 100,
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
            self.asset_handler.BIGGER_FONT,
            "BACK",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
        )
        self.apply = Button(
            center_w + 50,
            930,
            200,
            50,
            [self.return_to_menu],
            self.asset_handler.BIGGER_FONT,
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
            self.asset_handler.BIGGER_FONT,
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
            self.sfx_label,
            (center_w - 300 - self.sfx_label.get_width() / 2, 400),
        )
        self.label_surface.blit(
            self.narator_label,
            (center_w - 150 - self.narator_label.get_width() / 2, 400),
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
            self.asset_handler.img("plant_growth_pod/plant_growth_10.PNG"), (1300, 400)
        )

    def update(self, dt):
        self.textbox.update(dt)

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                if e.key == K_ESCAPE:
                    self.manager.go_to(TitleScene(self.manager))
            self.music_slider.handle_event(e)
            self.sfx_slider.handle_event(e)
            self.narator_slider.handle_event(e)
            # self.upload_score_button.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)
            self.textbox.handle_event(e)

    def get_options(self):
        options = {
            "music_volume": self.music_slider.get_percentage() / 100,
            "sfx_volume": self.sfx_slider.get_percentage() / 100,
            "narator_volume": self.narator_slider.get_percentage() / 100,
            "upload_score": self.upload_score_button.button_down,
            "name": self.textbox.text,
        }
        return options

    def render(self, screen):
        screen.fill(config.BLACK)
        screen.blit(self.label_surface, (0, 0))
        self.music_slider.draw(screen)
        self.sfx_slider.draw(screen)
        self.narator_slider.draw(screen)
        self.button_sprites.draw(screen)
        self.textbox.draw(screen)


class DefaultGameScene(object):
    def __init__(self):
        # get name and date
        name = config.load_options()["name"]
        task = asyncio.create_task(self.load_level())
        self.fps = None
        # self.server_game = Server_Game()
        since_epoch = time.time()
        self.asset_handler = AssetHandler.instance()
        self.path_to_logs = "./data/finished_games/{}{}".format(name, since_epoch)
        os.makedirs(self.path_to_logs)
        self.log = Log(self.path_to_logs)  # can be turned off
        pygame.mixer.set_reserved(2)
        self.sound_control = SoundControl()
        self.sound_control.play_music()
        self.sound_control.play_start_sfx()
        pygame.mouse.set_visible(True)

        self.camera = Camera(offset_y=0)
        self.gametime = GameTime.instance()
        self.gametime.reset()
        self.seconds_at_last_request = 0

        self.water_grid = Water_Grid(pos=(0, 900), max_water_cell=MAX_WATER_PER_CELL)
        self.nitrate_grid = Grid()
        self.plant = Plant(
            pos=(
                config.SCREEN_WIDTH / 2,
                config.SCREEN_HEIGHT - config.SCREEN_HEIGHT / 5,
            ),
            camera=self.camera,
            water_grid_pos=self.water_grid.pos,
            water_grid_shape=self.water_grid.get_shape(),
            sound_control=self.sound_control
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
            water_grid=self.water_grid,
        )

        self.narrator = Narrator(self.environment)

        self.ui = UI(
            plant=self.plant,
            narrator=self.narrator,
            camera=self.camera,
            sound_control=self.sound_control,
            quit=self.quit
        )
        self.hive = Hive((1500, 600),
                         10,
                         self.plant,
                         self.camera,
                         10,
                         self.sound_control.play_hive_clicked_sfx,
                         self.sound_control.play_bee_sfx)
        self.bugs = []
        for i in range(0, 10):
            self.bugs.append(
                Bug(
                    pos=(
                        190 * random.randint(0, 10),
                        900 + random.randint(0, 200),
                    ),
                    bounding_rect=pygame.Rect(0, 900, config.SCREEN_WIDTH, 240),
                    images=[self.asset_handler.img("bug_purple/bug_purple_{}.png".format(i)) for i in range(0, 3)],
                    camera=self.camera,
                    play_clicked=self.sound_control.play_bug_sfx
                )
            )

        self.tree = Tree(
            (1300, 100),
            [
                (self.asset_handler.img("tree/{index}.PNG".format(index=i), (800, 800)))
                for i in range(0, 4)
            ],
            self.environment,
        )

        self.snail_spawner = SnailSpawner(
            images_left=[self.asset_handler.img("snail/0.png")],
            images_right=[self.asset_handler.img("snail/4.png")],
            skull_image=self.asset_handler.img("skull.png", (64, 64)),
            camera=self.camera,
            callback=self.plant.eat_stem,
            nom_label=self.asset_handler.FONT.render("NOM NOM", True, (0, 0, 0)),
            bounds=pygame.Rect(0, 870, 1920, 20),
            max_amount=2,
            speed=1,
            snails=[],
            snail_clicked=self.sound_control.play_snail_sfx
        )

        # shop items are to be defined by the level
        add_leaf_item = Shop_Item(
            image=self.asset_handler.img("leaf_small.PNG", (64, 64)),
            callback=self.activate_add_leaf,
            condition=self.plant.organs[1].check_can_add_leaf,
            condition_not_met_message="Level up your stem to buy more leaves",
            post_hover_message=self.ui.hover.set_message,
            message="Leaves enable your plant to produce energy.",
            play_selected=self.sound_control.play_select_sfx,
            cost=LEAF_COST
        )

        self.shop = Shop(
            rect=Rect(1700, 120, 200, 450),
            shop_items=[add_leaf_item],
            water_grid=self.water_grid,
            nitrate_grid=self.nitrate_grid,
            plant=self.plant,
            post_hover_message=self.ui.hover.set_message,
            active=False,
            sound_control=self.sound_control
        )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("root_lateral.PNG", (64, 64)),
                callback=self.shop.root_item.activate,
                condition=self.plant.organs[2].check_can_add_root,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Roots are grown to improve water and nitrate intake.",
                play_selected=self.sound_control.play_select_sfx,
                cost=ROOT_COST
            )
        )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("branch.PNG", (64, 64)),
                callback=self.plant.organs[1].activate_add_branch,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Branches will provide more spots for leaves or flowers.",
                play_selected=self.sound_control.play_select_sfx,
                cost=BRANCH_COST
            )
        )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("sunflowers/1.PNG", (64, 64)),
                callback=self.plant.organs[3].activate_add_flower,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Flowers will enable you to start seed production.",
                play_selected=self.sound_control.play_select_sfx,
                cost=FLOWER_COST
            )
        )

        self.shop.add_shop_item(["watering", "blue_grain", "spraycan"])
        self.shop.spraycan.callbacks.append(self.snail_spawner.spray_snails)
        self.shop.spraycan.callbacks.append(self.hive.spray_bees)

        self.floating_shop = FloatingShop(self.camera, (0, 0))
        add_leaf_item_floating = FloatingShopItem(
            pos=(0, 0),
            callback=self.activate_add_leaf,
            image=self.asset_handler.img("leaf_small.PNG", (64, 64)),
            cost=LEAF_COST,
            plant=self.plant,
            play_buy_sfx=self.sound_control.play_buy_sfx,
        )
        add_branch_item_floating = FloatingShopItem(
            pos=(0, 0),
            callback=self.plant.organs[1].activate_add_branch,
            image=self.asset_handler.img("branch.PNG", (64, 64)),
            cost=BRANCH_COST,
            plant=self.plant,
            play_buy_sfx=self.sound_control.play_buy_sfx
        )
        add_flower_item_floating = FloatingShopItem(
            pos=(0, 0),
            callback=self.plant.organs[3].activate_add_flower,
            image=self.asset_handler.img("sunflowers/1.PNG", (64, 64)),
            cost=FLOWER_COST,
            plant=self.plant,
            play_buy_sfx=self.sound_control.play_buy_sfx
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
        self.log.close_model_file()
        self.plant.save_image(self.path_to_logs)
        plant_dict = self.plant.to_dict()
        config.write_dict(plant_dict, self.path_to_logs + "/plant")
        self.manager.go_to(EndScene(self.path_to_logs))

    def handle_events(self, events: List[pygame.event.Event]):
        for e in events:
            self.ui.handle_event(e)
            if self.ui.pause:
                continue
            if e.type == GROWTH:
                delta_t = 1
                growth_percentages = {
                    "leaf_percent": 1,
                    "stem_percent": 0,
                    "root_percent": 1,
                    "seed_percent": 0,
                    "starch_percent": -10,
                    "stomata": False,
                }
                # response = self.server_game.update(delta_t=delta_t, growth_percentages=growth_percentages)
                # print(response)
                '''if self.shop.watering_can.pouring:
                    for i in range(len(self.water_grid.poured_cells)):
                        amount = self.water_grid.poured_cells[i]
                        if amount > 0:
                            self.client.add2grid(amount, i, 0, "water")
                    self.water_grid.poured_cells.fill(0)'''

                '''ticks = self.gametime.get_time()
                self.log.append_model_row(
                    ticks=ticks,
                    timeframe=delta_time_in_h * 3600,
                    leaf_mass=self.plant.organs[0].get_mass(),
                    stem_mass=self.plant.organs[1].get_mass(),
                    root_mass=self.plant.organs[2].get_mass(),
                    seed_mass=self.plant.organs[3].get_mass(),
                    leaf_percentage=growth_percent.leaf,
                    stem_percentage=growth_percent.stem,
                    root_percentage=growth_percent.root,
                    starch_percentage=growth_percent.starch,
                    seed_percentage=flower_percent,
                    water_intake=self.server_plant.water.water_intake,
                    water_pool_plant=self.server_plant.water.water_pool,
                    water_available_env_abs=0,#self.server_environment.water_grid.available_absolute(self.server_plant.root),
                    nitrate_intake=self.server_plant.nitrate.nitrate_intake,
                    nitrate_pool_plant=self.server_plant.nitrate.nitrate_pool,
                    nitrate_available_env_abs=0,#self.server_environment.nitrate_grid.available_absolute(self.server_plant.root),
                    nitrate_available_env_michalis_menten=self.server_environment.nitrate_grid.available_relative_mm(
                        time_seconds=delta_time_in_h * 3600,
                        g_root=self.server_plant.root_biomass,
                        v_max=Vmax,
                        k_m=Km,
                        roots=self.server_plant.root),
                    starch_intake=self.server_plant.starch_pool.starch_in,
                    starch_out=self.server_plant.starch_pool.starch_out,
                    starch_pool=self.server_plant.starch_pool.available_starch_pool,

                    photon_intake=self.server_plant.photon,
                    co2_intake=self.server_plant.co2,

                    temperature=0,#latest_weather_state.temperature,
                    humidity=0,#latest_weather_state.humidity,
                    precipitation=0,#latest_weather_state.precipitation,
                )'''

            if e.type == WIN:
                self.plant.save_image(self.path_to_logs)
                plant_dict = self.plant.to_dict()
                config.write_dict(plant_dict, self.path_to_logs + "/plant")
                self.manager.go_to(EndScene(self.path_to_logs))

            self.shop.handle_event(e)
            self.floating_shop.handle_event(e)

            self.plant.handle_event(e)
            self.snail_spawner.handle_event(e)
            for bug in self.bugs:
                bug.handle_event(e)
            self.hive.handle_event(e)
            self.narrator.handle_event(e)
            self.camera.handle_event(e)

    def update_plant(self, response):
        pass
        #print(response)

    def check_game_end(self, days):
        if days > config.MAX_DAYS:
            pygame.event.post(pygame.event.Event(WIN))

    async def load_level(self):
        global request_running
        if not request_running:
            request_running = True
            async with websockets.connect("ws://localhost:8765") as websocket:
                print(" --> Send Load Level...")
                game_state = {
                    "reset": True,
                }
                await websocket.send(json.dumps(game_state))
                response = await websocket.recv()
                request_running = False


    async def send_and_get_response(self):
        global request_running
        if not request_running:
            request_running = True
            async with websockets.connect("ws://localhost:8765") as websocket:
                delta_t = self.gametime.get_time()/1000 - self.seconds_at_last_request
                self.seconds_at_last_request = self.gametime.get_time()/1000
                print(" --> Sending request...")
                game_state = {
                    "delta_t": delta_t,
                    "growth_percentages": {
                        "leaf_percent": self.plant.organs[0].percentage,
                        "stem_percent": self.plant.organs[1].percentage,
                        "root_percent": self.plant.organs[2].percentage,
                        "seed_percent": self.plant.organs[3].percentage,
                        "starch_percent": self.plant.organ_starch.percentage,
                        "stomata": self.plant.organs[0].stomata_open,
                    },
                    "increase_water_grid": self.water_grid.pop_poured_cells(),
                    "increase_nitrate_grid": self.nitrate_grid.pop_cells_to_add(),
                    "buy_new_root": self.plant.organs[2].pop_new_root(),
                }
                await websocket.send(json.dumps(game_state))
                response = await websocket.recv()
                print(" --> Received response, updating state")
                dic = json.loads(response)
                #print(dic)

                self.environment.precipitation = dic["environment"]["precipitation"]
                self.ui.humidity = dic["environment"]["humidity"]
                self.ui.temperature = dic["environment"]["temperature"]

                self.nitrate_grid.grid = np.asarray(dic["environment"]["nitrate_grid"])
                if not self.shop.watering_can.active:
                    self.water_grid.water_grid = np.asarray(dic["environment"]["water_grid"])

                # update plant
                self.plant.organs[0].update_masses(dic["plant"]["leaf_biomass"])
                self.plant.organs[1].update_mass(dic["plant"]["stem_biomass"])
                self.plant.organs[2].update_mass(dic["plant"]["root_biomass"])
                self.plant.organs[3].update_masses(dic["plant"]["seed_biomass"])
                self.plant.organ_starch.update_mass(dic["plant"]["starch_pool"])
                self.plant.organ_starch.max_pool = dic["plant"]["max_starch_pool"]
                self.plant.water_pool = dic["plant"]["water_pool"]
                self.plant.max_water_pool = dic["plant"]["max_water_pool"]

                # make simple root strucure from root_dict
                self.plant.organs[2].ls = DictToRoot().load_root_system(dic["plant"]["root"])

                request_running = False

    def update(self, dt):
        # self.client.update()
        #fps = 1/dt
        #self.fps = self.asset_handler.FONT.render(f"{fps}", True, config.WHITE)

        task = asyncio.create_task(self.send_and_get_response())

        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        days = int(ticks / day)
        hours = (ticks % day) / hour
        self.check_game_end(days)
        if 8 < hours < 20:
            if self.ui.active_preset["type"] == "night":
                preset = {
                    "type": "night",
                    "leaf_slider": self.plant.organs[0].percentage,
                    "stem_slider": self.plant.organs[1].percentage,
                    "root_slider": self.plant.organs[2].percentage,
                    "starch_slider": self.plant.organ_starch.percentage,
                }
                self.ui.switch_preset(preset)

            (
                shadow_map,
                resolution,
                max_shadow,
            ) = self.environment.calc_shadowmap(
                self.plant.organs[0].leaves,
                sun_dir=(((-(20 / 12) * hours) + 23.33), 1),
            )
            self.plant.organs[0].shadow_map = shadow_map
            self.plant.organs[0].shadow_resolution = resolution
            self.plant.organs[0].max_shadow = max_shadow
        else:
            if self.ui.active_preset["type"] == "day":
                preset = {
                    "type": "day",
                    "leaf_slider": self.plant.organs[0].percentage,
                    "stem_slider": self.plant.organs[1].percentage,
                    "root_slider": self.plant.organs[2].percentage,
                    "starch_slider": self.plant.organ_starch.percentage,
                }
                self.ui.switch_preset(preset)
            self.environment.shadow_map = None
            self.plant.organs[0].shadow_map = None
        self.water_grid.set_root_grid(self.plant.organs[2].get_root_grid())

        self.water_grid.update(dt)
        self.snail_spawner.update(dt)
        for bug in self.bugs:
            bug.update(dt)
        self.hive.update(dt)
        self.tree.update(dt)
        self.camera.update(dt)
        self.environment.update(dt)
        self.shop.update(dt)
        self.floating_shop.update(dt)
        self.ui.update(dt)
        self.narrator.update(dt)
        self.plant.update(dt)

        if self.plant.seedling.max < self.plant.get_biomass():
            self.shop.active = True

    def render(self, screen):
        screen.fill((0, 0, 0))
        temp_surface.fill((0, 0, 0))
        if self.ui.pause:
            self.ui.draw(screen)
            return



        self.environment.draw_background(temp_surface)
        self.hive.draw(temp_surface)
        self.tree.draw(temp_surface)
        self.environment.draw_foreground(temp_surface)
        self.snail_spawner.draw(temp_surface)
        for bug in self.bugs:
            bug.draw(temp_surface)

        self.plant.draw(temp_surface)
        self.environment.draw_shadows(temp_surface)

        self.water_grid.draw(temp_surface)
        self.nitrate_grid.draw(temp_surface)
        self.floating_shop.draw(temp_surface)

        screen.blit(temp_surface, (0, self.camera.offset_y))
        self.shop.draw(screen)
        self.ui.draw(screen)
        if self.fps:
            screen.blit(self.fps, (1200,20))

        self.narrator.draw(screen)


class TitleScene(object):
    def __init__(self, manager=None):
        super(TitleScene, self).__init__()
        self.sound_control = SoundControl()
        self.asset_handler = AssetHandler.instance()
        self.title = self.asset_handler.MENU_TITLE.render("PlantEd", True, config.WHITE)
        self.center_h = config.SCREEN_HEIGHT / 2 + 100
        self.center_w = config.SCREEN_WIDTH / 2
        self.card_0 = Card(
            (self.center_w, self.center_h - 100),
            self.asset_handler.img("menu/gatersleben.JPG", (512, 512)),
            "Gatersleben",
            callback=manager.go_to,
            callback_var=DefaultGameScene,
            keywords="Beginner, Medium Temperatures",
            play_select_sfx=self.sound_control.play_select_sfx
        )

        self.credit_button = Button(
            self.center_w - 450,
            930,
            200,
            50,
            [self.go_to_credtis],
            self.asset_handler.BIGGER_FONT,
            "CREDTIS",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
        )
        self.options_button = Button(
            self.center_w - 200,
            930,
            200,
            50,
            [self.go_to_options],
            self.asset_handler.BIGGER_FONT,
            "OPTIONS",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
        )
        self.scores_button = Button(
            self.center_w + 50,
            930,
            200,
            50,
            [self.go_to_scores],
            self.asset_handler.BIGGER_FONT,
            "SCORES",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
        )
        self.quit_button = Button(
            self.center_w + 300,
            930,
            200,
            50,
            [self.quit],
            self.asset_handler.BIGGER_FONT,
            "QUIT",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
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
        screen.fill(config.BLACK)
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
        pygame.event.post(pygame.event.Event(QUIT))

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


class EndScene(object):
    def __init__(self, path_to_logs):
        self.path_to_logs = path_to_logs
        self.asset_handler = AssetHandler.instance()
        super(EndScene, self).__init__()
        self.camera = Camera(offset_y=-50)
        self.sound_control = SoundControl()
        dict_plant = config.load_dict(path_to_logs + "/plant.json")
        self.plant_object: Plant = Plant.from_dict(dict_plant, self.camera)
        positions = []
        for flower in self.plant_object.organs[3].flowers:
            positions.append((flower["x"], flower["y"] + self.camera.offset_y))

        systems = []
        for position in positions:
            systems.append(
                ParticleSystem(
                    max_particles=50,
                    spawn_box=(position[0], position[1], 0, 0),
                    lifetime=10,
                    color=(int(255 * random.random()), int(255 * random.random()), int(255 * random.random())),
                    apply_gravity=2,
                    speed=[(random.random() - 0.5) * 20, -80 * random.random()],
                    spread=[50, 30],
                    active=False,
                    size_over_lifetime=True,
                    size=10,
                    once=True,
                )
            )
        self.explosion: ParticleExplosion = ParticleExplosion(
            systems=systems,
            interval=0.5,
            play_explosion_sound=self.sound_control.play_pop_seed_sfx,
        )
        self.explosion.start()

        images = Animation.generate_counter(
            start_number=1000,
            end_number=2000,
            resolution=10,
            font=self.asset_handler.BIGGER_FONT
        )

        explosion_duration = 0.5 * len(self.plant_object.organs[3].flowers)

        self.score_animation = Animation(
            images=images,
            duration=explosion_duration,
            pos=(400, 400),
            running=True,
            once=True
        )

        self.score_header_label = self.asset_handler.MENU_SUBTITLE.render("Score", True, config.WHITE)
        self.flower_score_list = []
        score_sum = 0
        for i in range(len(self.plant_object.organs[3].flowers)):
            flowers = self.plant_object.organs[3].flowers
            flower_score = self.asset_handler.BIGGER_FONT.render("Flower {}: {:.2f} grams".format(i, float(flowers[i]["mass"])),
                                                     True,
                                                     config.WHITE)
            self.flower_score_list.append(flower_score)
            score_sum += flowers[i]["mass"]

        self.score_sum_label = self.asset_handler.BIGGER_FONT.render("{:.2f} grams".format(float(score_sum)), True, config.WHITE)
        self.title = self.asset_handler.MENU_TITLE.render("Finished", True, config.WHITE)

        self.plot_label = self.asset_handler.MENU_SUBTITLE.render("Simulation Data", True, config.WHITE)

        '''
        Prepare plots
        - Mass (Organs)
        - Pools (Water, Nitrate, starch)
        - Environment (Photon, Humidity, Precipitation, Temperature)
        - Special (Transpiration, APS lol)
        '''

        df = pandas.read_csv(path_to_logs + "/model_logs.csv")
        self.image = plot.generate_png_from_vec([df.leaf_mass, df.stem_mass, df.root_mass, df.seed_mass],
                                                name_list=["Leaf", "Stem", "Root", "Seed"],
                                                colors=[config.hex_color_to_float(config.GREEN),
                                                        config.hex_color_to_float(config.WHITE),
                                                        config.hex_color_to_float(config.RED),
                                                        config.hex_color_to_float(config.YELLOW)],
                                                ticks=df.ticks,
                                                xlabel="Time",
                                                ylabel="Organ Mass",
                                                path_to_logs=path_to_logs,
                                                filename="PLOT.png")

        self.button_sprites = pygame.sprite.Group()
        self.back = Button(
            config.SCREEN_WIDTH / 2 - 150,
            930,
            300,
            50,
            [self.sound_control.play_toggle_sfx, self.return_to_menu],
            self.asset_handler.BIGGER_FONT,
            "Upload Simulation",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
        )
        self.button_sprites.add(self.back)

    def update(self, dt):
        self.explosion.update(dt)
        # self.score_animation.update(dt)

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN:
                pass
            for button in self.button_sprites:
                button.handle_event(e)

    def upload_data(self):
        options = config.load_options()
        scoring.upload_score(
            options["name"], self.plant_object.organs[3].get_mass(), self.path_to_logs
        )

    def render(self, screen):
        screen.fill((0, 0, 0, 0))
        temp_surface.fill((0, 0, 0))
        self.plant_object.draw(temp_surface)
        screen.blit(temp_surface, (0, self.camera.offset_y))
        self.button_sprites.draw(screen)
        self.explosion.draw(screen)
        # self.score_animation.draw(screen)

        distance = 0
        width = 0
        if self.flower_score_list:
            distance = self.flower_score_list[0].get_height() + 20
            width = self.flower_score_list[0].get_width()
        for i in range(len(self.flower_score_list)):
            screen.blit(self.flower_score_list[i], (500 - width, 380 + (distance * i)))
        pygame.draw.line(screen, config.WHITE, (150, 380 + (distance * len(self.flower_score_list))),
                         (550, 380 + (distance * len(self.flower_score_list))))
        screen.blit(self.score_sum_label,
                    (500 - self.score_sum_label.get_width(), 400 + (distance * len(self.flower_score_list))))
        screen.blit(self.score_header_label, (350 - self.score_header_label.get_width() / 2, 270))
        pygame.draw.rect(screen, config.WHITE, (100, 360, 500, int((len(self.flower_score_list) + 2) * distance)), 1, 1)
        screen.blit(self.image, (
            config.SCREEN_WIDTH - self.image.get_width() - 20, config.SCREEN_HEIGHT / 2 - self.image.get_height() / 2))
        screen.blit(self.plot_label, (1570 - self.plot_label.get_width() / 2, 270))
        screen.blit(self.title, (config.SCREEN_WIDTH / 2 - self.title.get_width() / 2, 100))

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))


class CustomScene(object):
    def __init__(self):
        self.asset_handler = AssetHandler.instance()
        super(CustomScene, self).__init__()
        self.text1 = self.asset_handler.MENU_TITLE.render(
            "Top Plants", True, (255, 255, 255)
        )
        # self.text3 = config.BIGGER_FONT.render('> press any key to restart <', True, (255,255,255))

        self.name_txt = self.asset_handler.BIGGER_FONT.render(
            "Name", True, (255, 255, 255)
        )
        self.score_txt = self.asset_handler.BIGGER_FONT.render(
            "Score", True, (255, 255, 255)
        )
        self.submit_txt = self.asset_handler.BIGGER_FONT.render(
            "Submit Date", True, (255, 255, 255)
        )

        self.button_sprites = pygame.sprite.Group()
        self.back = Button(
            860,
            930,
            200,
            50,
            [self.return_to_menu],
            self.asset_handler.BIGGER_FONT,
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

        for winner in reversed(self.winners):
            # print(winner["score"])
            score = winner["score"]
            score_label = self.asset_handler.BIGGER_FONT.render(
                "Seed Mass {:.5f} gramms".format(score), True, (255, 255, 255)
            )
            self.scores.append(score_label)
            name = self.asset_handler.BIGGER_FONT.render(
                winner["name"], True, (255, 255, 255)
            )
            self.names.append(name)
            datetime_added = self.asset_handler.BIGGER_FONT.render(
                datetime.utcfromtimestamp(winner["datetime_added"]).strftime(
                    "%d/%m/%Y %H:%M"
                ),
                True,
                (255, 255, 255),
            )
            self.datetimes.append(datetime_added)

    def return_to_menu(self):
        # pygame.quit()
        # sys.exit()
        self.manager.go_to(TitleScene(self.manager))

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
        screen.fill(config.BLACK)
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
        self.sound_control = SoundControl()
        self.asset_handler = AssetHandler.instance()
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
            self.asset_handler.BIGGER_FONT,
            "BACK",
            config.LIGHT_GRAY,
            config.WHITE,
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx
        )
        self.button_sprites.add(self.back)

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))

    def init_labels(self):
        self.label_surface.fill(config.BLACK)
        self.made_by_label = self.asset_handler.MENU_TITLE.render(
            "MADE BY", True, config.WHITE
        )
        self.daniel = self.asset_handler.MENU_SUBTITLE.render(
            "Daniel Koch", True, config.WHITE
        )
        self.jj = self.asset_handler.MENU_SUBTITLE.render(
            "Jedrzej J. Szymanski", True, config.WHITE
        )
        self.nadine = self.asset_handler.MENU_SUBTITLE.render(
            "Nadine Töpfer", True, config.WHITE
        )
        self.stefano = self.asset_handler.MENU_SUBTITLE.render(
            "Stefano A. Cruz", True, config.WHITE
        )
        self.pouneh = self.asset_handler.MENU_SUBTITLE.render(
            "Pouneh Pouramini", True, config.WHITE
        )
        self.jan = self.asset_handler.MENU_SUBTITLE.render(
            "Jan-Niklas Weder", True, config.WHITE
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
            self.jan, (self.center_w - self.jan.get_width() / 2, 480)
        )
        self.label_surface.blit(
            self.stefano, (self.center_w - self.stefano.get_width() / 2, 560)
        )
        self.label_surface.blit(
            self.pouneh, (self.center_w - self.pouneh.get_width() / 2, 640)
        )
        self.label_surface.blit(
            self.nadine, (self.center_w - self.nadine.get_width() / 2, 720)
        )
        self.label_surface.blit(
            self.jj, (self.center_w - self.jj.get_width() / 2, 800)
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


request_running = False


async def main():
    """

    Args:
        windowed: A boolean that determines whether the game starts
        fullscreen or windowed.
    """

    pygame.init()
    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)

    screen = pygame.display.set_mode(
        true_res, pygame.FULLSCREEN | pygame.NOFRAME | pygame.DOUBLEBUF, 16
    )

    timer = pygame.time.Clock()
    running = True
    # camera = Camera()
    manager = SceneMananger()

    while running:
        # dt = timer.tick(60) / 1000.0
        dt = timer.tick(30) / 1000.0

        #fps = str(int(timer.get_fps()))
        #fps_text = AssetHandler.instance().FONT.render(fps, False, (255, 255, 255))

        if pygame.event.get(QUIT):
            running = False
            break

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        #screen.blit(fps_text, (true_res[0]-500, 20))
        pygame.display.update()
        await asyncio.sleep(0)

def start():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())