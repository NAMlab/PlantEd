import asyncio
import json
import os
import random
import time
from datetime import datetime
from typing import List

import numpy as np
import pygame
import websockets
from pygame.locals import *

from PlantEd import config
from PlantEd.client.analysis import scoring
from PlantEd.client.camera import Camera
from PlantEd.client.utils.icon_handler import IconHandler
from PlantEd.client.utils.scores_handler import ScoreList
from PlantEd.constants import MAX_WATER_PER_CELL, ROOT_COST, BRANCH_COST, \
    FLOWER_COST, LEAF_COST
from PlantEd.data.assets import AssetHandler
from PlantEd.data.sound_control import SoundControl
from PlantEd.client.gameobjects.bee import Hive
from PlantEd.client.gameobjects.bug import Bug
from PlantEd.client.utils.grid import Grid
from PlantEd.client.gameobjects.level_card import Card
from PlantEd.client.gameobjects.plant import Plant
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
from PlantEd.client.utils.animation import Animation
from PlantEd.client.utils.button import Button, Slider, Textbox
from PlantEd.client.utils.gametime import GameTime
from PlantEd.client.utils.narrator import Narrator
from PlantEd.client.utils.particle import ParticleSystem, ParticleExplosion
from PlantEd.client.weather import Environment
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
        self.icon_handler = IconHandler((0, 50))
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

        self.label_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
            )

        center_w, center_h = config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2

        self.music_slider = Slider(
            (config.SCREEN_WIDTH / 2 - 150 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["music_volume"] * 100,
            active=True,
            )
        self.narator_slider = Slider(
            (config.SCREEN_WIDTH / 2 - 0 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["narator_volume"] * 100,
            active=True,
            )
        self.sfx_slider = Slider(
            (config.SCREEN_WIDTH / 2 + 150 - 25, 350, 15, 200),
            self.asset_handler.FONT,
            (50, 20),
            percent=self.options["sfx_volume"] * 100,
            active=True,
            )

        self.random = Button(
            500,
            100,
            50,
            50,
            [self.set_random_name, self.icon_handler.randomize_image],
            button_color=config.LIGHT_GRAY,
            image=self.asset_handler.img("re.PNG", (50, 50)),
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx,
            )

        self.textbox = Textbox(
            130,
            100,
            350,
            50,
            self.asset_handler.BIGGER_FONT,
            self.options.get("name") if self.options.get("name") else "Player",
            background_color=config.LIGHT_GRAY,
            textcolor=config.WHITE,
            highlight_color=config.WHITE,
            )

        self.back = Button(
            center_w - 100,
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

        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add([self.back, self.random])
        self.init_labels()

    def return_to_menu(self):
        config.write_options(self.get_options())
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

        pygame.draw.rect(self.label_surface, config.WHITE, (config.SCREEN_WIDTH / 2 - 300, 220, 600, 430),
                         border_radius=3, width=1)
        self.label_surface.blit(self.music_label,
                                (config.SCREEN_WIDTH / 2 - self.music_label.get_width() / 2 - 150, 300))
        self.label_surface.blit(self.narator_label,
                                (config.SCREEN_WIDTH / 2 - self.narator_label.get_width() / 2 - 0, 300))
        self.label_surface.blit(self.sfx_label, (config.SCREEN_WIDTH / 2 - self.sfx_label.get_width() / 2 + 150, 300))

        self.label_surface.blit(
            self.asset_handler.img("plant_growth_pod/plant_growth_10.PNG"), (1300, 400)
            )

    def set_random_name(self):
        name = config.randomize_name()
        options = config.load_options()
        options["name"] = name
        config.write_options(options)
        self.textbox.update_text(name)

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
            self.textbox.handle_event(e)
            self.icon_handler.handle_event(e)
            # self.upload_score_button.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)

    def get_options(self):
        options = config.load_options()
        options["music_volume"] = self.music_slider.get_percentage() / 100
        options["sfx_volume"] = self.sfx_slider.get_percentage() / 100
        options["narator_volume"] = self.narator_slider.get_percentage() / 100
        return options

    def render(self, screen):
        screen.fill(config.BLACK)
        screen.blit(self.label_surface, (0, 0))
        self.music_slider.draw(screen)
        self.sfx_slider.draw(screen)
        self.narator_slider.draw(screen)
        self.button_sprites.draw(screen)
        self.textbox.draw(screen)
        self.icon_handler.draw(screen)


class DefaultGameScene(object):
    def __init__(self):
        # get name and date
        self.options = config.load_options()
        name = self.options.get("name") if self.options.get("name") is not None else "Player"
        task = asyncio.create_task(self.load_level())
        self.fps = None
        # self.server_game = Server_Game()
        since_epoch = time.time()
        self.asset_handler = AssetHandler.instance()
        self.path_to_logs = "../client/data/finished_games/{}{}".format(name, since_epoch)
        os.makedirs(self.path_to_logs)
        # self.log = Log(self.path_to_logs)  # can be turned off
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

        self.shop = Shop(
            rect=Rect(1700, 120, 200, 410),
            shop_items=[],
            water_grid=self.water_grid,
            nitrate_grid=self.nitrate_grid,
            plant=self.plant,
            post_hover_message=self.ui.hover.set_message,
            active=False,
            sound_control=self.sound_control
            )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("leaf_small.PNG", (64, 64)),
                callback=self.activate_add_leaf,
                buy=self.shop.buy,
                condition=self.plant.organs[1].has_free_spots,
                condition_not_met_message="Level up your stem to buy more leaves",
                post_hover_message=self.ui.hover.set_message,
                message="Leaves enable your plant to produce energy.",
                play_selected=self.sound_control.play_select_sfx,
                cost=LEAF_COST,
                cost_label=self.asset_handler.FONT.render(f"{LEAF_COST}", True, config.BLACK)
                )
            )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("root_lateral.PNG", (64, 64)),
                callback=self.shop.root_item.activate,
                buy=self.shop.buy,
                condition=self.plant.organs[2].check_can_add_root,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Roots are grown to improve water and nitrate intake.",
                play_selected=self.sound_control.play_select_sfx,
                cost=ROOT_COST,
                cost_label=self.asset_handler.FONT.render(f"{ROOT_COST}", True, config.BLACK)
                )
            )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("branch.PNG", (64, 64)),
                callback=self.plant.organs[1].activate_add_branch,
                buy=self.shop.buy,
                condition=self.plant.organs[1].has_free_spots,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Branches will provide more spots for leaves or flowers.",
                play_selected=self.sound_control.play_select_sfx,
                cost=BRANCH_COST,
                cost_label=self.asset_handler.FONT.render(f"{BRANCH_COST}", True, config.BLACK)
                )
            )

        self.shop.shop_items.append(
            Shop_Item(
                image=self.asset_handler.img("sunflowers/1.PNG", (64, 64)),
                callback=self.plant.organs[3].activate_add_flower,
                buy=self.shop.buy,
                condition=self.plant.organs[1].has_free_spots,
                condition_not_met_message="Level up any organ to get more green thumbs",
                post_hover_message=self.ui.hover.set_message,
                message="Flowers will enable you to start seed production.",
                play_selected=self.sound_control.play_select_sfx,
                cost=FLOWER_COST,
                cost_label=self.asset_handler.FONT.render(f"{FLOWER_COST}", True, config.BLACK)
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
        options = config.load_options()
        seed_mass = self.plant.organs[3].get_mass()
        score = options.get("score") if options.get("score") is not None else 0
        options["score"] = seed_mass if seed_mass > score else score
        config.write_options(options)
        task = asyncio.create_task(self.end_level(options["name"], options["icon_name"]))
        self.plant.save_image(self.path_to_logs)
        plant_dict = self.plant.to_dict()
        config.write_dict(plant_dict, self.path_to_logs + "/plant")
        self.manager.go_to(EndScene(self.path_to_logs))

    def handle_events(self, events: List[pygame.event.Event]):
        for e in events:
            self.ui.handle_event(e)
            if self.ui.pause or self.ui.infobox_manager.visible:
                continue

            if e.type == WIN:
                self.quit()

            self.shop.handle_event(e)
            self.floating_shop.handle_event(e)
            self.plant.handle_event(e)
            self.snail_spawner.handle_event(e)
            for bug in self.bugs:
                bug.handle_event(e)
            self.hive.handle_event(e)
            self.narrator.handle_event(e)
            self.camera.handle_event(e)

    def check_game_end(self, days):
        if days > config.MAX_DAYS:
            pygame.event.post(pygame.event.Event(WIN))

    async def end_level(self, player_name, icon_name):
        async with websockets.connect("ws://localhost:8765") as websocket:
            print(" --> End Level...")
            game_state = {
                "type": "end_level",
                "message": {
                    "player_name": player_name,
                    "icon_name": icon_name
                    }
                }
            await websocket.send(json.dumps(game_state))
            response = await websocket.recv()

    async def load_level(self):
        global request_running
        if not request_running:
            request_running = True
            async with websockets.connect("ws://localhost:8765") as websocket:
                print(" --> Send Load Level...")
                game_state = {
                    "type": "load_level",
                    "message": {
                        "player_name": self.options["name"],
                        "icon_name": self.options["icon_name"],
                        "level_name": "summer_low_nitrate",
                        "path_to_logs": self.path_to_logs,
                        }
                    }
                await websocket.send(json.dumps(game_state))
                response = await websocket.recv()
                print(response)
                request_running = False

    async def send_and_get_response(self):
        global request_running
        if not request_running:
            request_running = True
            async with websockets.connect("ws://localhost:8765") as websocket:
                delta_t = self.gametime.get_time() / 1000 - self.seconds_at_last_request
                self.seconds_at_last_request = self.gametime.get_time() / 1000
                print(" --> Sending request...")
                game_state = {
                    "type": "simulate",
                    "message": {
                        "delta_t": delta_t,
                        "growth_percentages": {
                            "leaf_percent": self.plant.organs[0].percentage,
                            "stem_percent": self.plant.organs[1].percentage,
                            "root_percent": self.plant.organs[2].percentage,
                            "seed_percent": 0,
                            "starch_percent": self.plant.organ_starch.percentage,
                            "stomata": self.plant.organs[0].stomata_open,
                            },
                        "shop_actions": {
                            "buy_watering_can": self.water_grid.pop_poured_cells(),
                            "buy_nitrate": self.nitrate_grid.pop_cells_to_add(),
                            "buy_leaf": self.plant.organs[0].pop_new_leaves(),
                            "buy_branch": self.plant.organs[1].pop_new_branches(),
                            "buy_root": self.plant.organs[2].pop_new_roots(),
                            "buy_seed": self.plant.organs[3].pop_new_flowers(),
                            }
                        }
                    }

                # print(f"REQUEST: {game_state}")

                await websocket.send(json.dumps(game_state))
                response = await websocket.recv()
                print(" --> Received response, updating state")
                dic = json.loads(response)

                # print(f"RESPONSE: {dic}")
                self.environment.precipitation = dic["environment"]["precipitation"]
                self.ui.humidity = dic["environment"]["humidity"]
                self.ui.temperature = dic["environment"]["temperature"]

                self.nitrate_grid.grid = np.asarray(dic["environment"]["nitrate_grid"])
                if not self.shop.watering_can.active:
                    self.water_grid.water_grid = np.asarray(dic["environment"]["water_grid"])

                # update plant
                self.plant.organs[0].update_masses(dic["plant"]["leafs_biomass"])
                self.plant.organs[1].update_masses(dic["plant"]["stems_biomass"])
                self.plant.organs[2].update_mass(dic["plant"]["roots_biomass"])
                self.plant.organs[3].update_masses(dic["plant"]["seeds_biomass"])
                self.plant.organ_starch.update_mass(dic["plant"]["starch_pool"])
                self.plant.organ_starch.max_pool = dic["plant"]["max_starch_pool"]
                self.plant.water_pool = dic["plant"]["water_pool"]
                self.plant.max_water_pool = dic["plant"]["max_water_pool"]

                # make simple root strucure from root_dict
                self.plant.organs[2].ls = DictToRoot().load_root_system(dic["plant"]["root"])

                self.ui.used_fluxes = dic["used_fluxes"]

                if dic is not None:
                    if not dic["running"]:
                        pygame.event.post(pygame.event.Event(WIN))
                request_running = False

    def update(self, dt):
        # self.client.update()
        # fps = 1/dt
        # self.fps = self.asset_handler.FONT.render(f"{fps}", True, config.WHITE)

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
            screen.blit(self.fps, (1200, 20))

        self.narrator.draw(screen)


class TitleScene(object):
    def __init__(self, manager=None):
        super(TitleScene, self).__init__()
        self.options = config.load_options()
        self.sound_control = SoundControl()
        self.asset_handler = AssetHandler.instance()
        self.icon_handler = IconHandler((0, 50))
        self.title = self.asset_handler.MENU_TITLE.render("PlantEd", True, config.WHITE)
        self.center_h = config.SCREEN_HEIGHT / 2 + 100
        self.center_w = config.SCREEN_WIDTH / 2
        score = self.options.get("score") if self.options.get("score") is not None else 0
        self.card_0 = Card(
            (self.center_w, self.center_h - 100),
            self.asset_handler.img("menu/gatersleben.JPG", (512, 512)),
            "Gatersleben",
            callback=manager.go_to,
            score=score,
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

        self.random = Button(
            500,
            100,
            50,
            50,
            [self.set_random_name, self.icon_handler.randomize_image],
            button_color=config.LIGHT_GRAY,
            image=self.asset_handler.img("re.PNG", (50, 50)),
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx,
            )

        self.button_sprites = pygame.sprite.Group()
        self.button_sprites.add(
            [
                self.quit_button,
                self.credit_button,
                self.options_button,
                self.scores_button,
                self.random,
                ]
            )

        self.textbox = Textbox(
            130,
            100,
            350,
            50,
            self.asset_handler.BIGGER_FONT,
            self.options.get("name") if self.options.get("name") else "Player",
            background_color=config.LIGHT_GRAY,
            textcolor=config.WHITE,
            highlight_color=config.WHITE,
            )

    def render(self, screen):
        temp_surface.fill((0, 0, 0))
        screen.fill(config.BLACK)
        temp_surface.blit(
            self.title, (self.center_w - self.title.get_width() / 2, 100)
            )
        self.card_0.draw(temp_surface)
        # self.card_1.draw(screen)
        # self.card_2.draw(screen)
        pygame.draw.line(temp_surface, config.WHITE, (100, 900), (1820, 900))

        self.textbox.draw(temp_surface)
        self.button_sprites.draw(temp_surface)
        self.icon_handler.draw(temp_surface)

        screen.blit(temp_surface, (0, 0))

    def update(self, dt):
        self.card_0.update(dt)
        # self.card_1.update(dt)
        # self.card_2.update(dt)
        self.textbox.update(dt)

    def set_random_name(self):
        name = config.randomize_name()
        options = config.load_options()
        options["name"] = name
        config.write_options(options)
        self.textbox.update_text(name)

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
            self.icon_handler.handle_event(e)
            if self.icon_handler.selected:
                pass
                # return
            self.card_0.handle_event(e)
            # self.card_1.handle_event(e)
            # self.card_2.handle_event(e)
            for button in self.button_sprites:
                button.handle_event(e)
            # self.watering_can.handle_event(e)
            self.textbox.handle_event(e)


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
                    spawn_box=pygame.Rect(position[0], position[1], 0, 0),
                    lifetime=2,
                    color=(int(255 * random.random()), int(255 * random.random()), int(255 * random.random())),
                    gravity=2,
                    vel=((random.random() - 0.5) * 500, (random.random() - 0.5) * 500),
                    spread=((random.random() - 0.5) * 500, (random.random() - 0.5) * 500),
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
            flower_score = self.asset_handler.BIGGER_FONT.render(
                "Flower {}: {:.2f} grams".format(i, float(flowers[i]["mass"])),
                True,
                config.WHITE)
            self.flower_score_list.append(flower_score)
            score_sum += flowers[i]["mass"]

        self.score_sum_label = self.asset_handler.BIGGER_FONT.render("{:.2f} grams".format(float(score_sum)), True,
                                                                     config.WHITE)
        self.title = self.asset_handler.MENU_TITLE.render("Finished", True, config.WHITE)

        self.plot_label = self.asset_handler.MENU_SUBTITLE.render("Simulation Data", True, config.WHITE)

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
        '''screen.blit(self.image, (
            config.SCREEN_WIDTH - self.image.get_width() - 20, config.SCREEN_HEIGHT / 2 - self.image.get_height() / 2))'''
        screen.blit(self.plot_label, (1570 - self.plot_label.get_width() / 2, 270))
        screen.blit(self.title, (config.SCREEN_WIDTH / 2 - self.title.get_width() / 2, 100))

    def return_to_menu(self):
        self.manager.go_to(TitleScene(self.manager))


class CustomScene(object):
    def __init__(self):
        self.asset_handler = AssetHandler.instance()
        super(CustomScene, self).__init__()
        self.score_handler = ScoreList((200, 200), 1000)

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
        self.icon_names = []
        self.datetimes = []

        self.winners = sorted(self.winners, key=lambda x: x["score"])

        for winner in reversed(self.winners):
            print("Add score")
            # print(winner["score"])
            score = winner["score"]
            name = winner["name"]
            icon_name = winner["icon_name"]
            date = datetime.utcfromtimestamp(winner["datetime_added"]).strftime(
                "%d/%m/%Y %H:%M"
                )
            self.score_handler.add_new_score(name, icon_name, score, date)

    def return_to_menu(self):
        # pygame.quit()
        # sys.exit()
        self.manager.go_to(TitleScene(self.manager))

        '''    def get_day_time(self, ticks):
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        min = hour / 60
        second = min / 60
        days = str(int(ticks / day))
        hours = str(int((ticks % day) / hour))
        minutes = str(int((ticks % hour) / min))
        return days + " Days " + hours + " Hours " + minutes + " Minutes"'''

    def render(self, screen):
        screen.fill(config.BLACK)
        self.score_handler.draw(screen)
        self.button_sprites.draw(screen)

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            self.score_handler.handle_event(e)
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

        # fps = str(int(timer.get_fps()))
        # fps_text = AssetHandler.instance().FONT.render(fps, False, (255, 255, 255))

        if pygame.event.get(QUIT):
            running = False
            break

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        # screen.blit(fps_text, (true_res[0]-500, 20))
        pygame.display.update()
        await asyncio.sleep(0)


def start():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
