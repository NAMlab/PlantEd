import os
import time

import numpy as np
import pandas

from PlantEd.client.analysis import scoring
from PlantEd.client.analysis.logger import Log
from PlantEd.constants import MAX_DAYS, ROOT_COST, BRANCH_COST, LEAF_COST, FLOWER_COST, WATERING_CAN_COST, NITRATE_COST, \
    Vmax, Km
from PlantEd.server.plant import Plant
from PlantEd.server.dynamic_model import DynamicModel
from PlantEd.server.environment import Environment
import logging

logger = logging.getLogger("server")
logging.basicConfig(level=logging.ERROR)

# hot, low precipitation, fast water drain
scenarios = {
    "summer_low_nitrate": {
        "weather_seed": 0.23171800215059546,
        "nitrate_percent": 0.2,
        "photon_peak": 2000,
        "filename": "data/cleaned_weather_summer.csv",
        },
    "summer_high_nitrate": {
        "weather_seed": 0.23171800215059546,
        "nitrate_percent": 50,
        "photon_peak": 2000,
        "filename": "data/cleaned_weather_summer.csv",
        },
    "spring_low_nitrate": {
        "weather_seed": 15,
        "nitrate_percent": 2,
        "photon_peak": 1000,
        "filename": "data/cleaned_weather_spring.csv",
        },
    "spring_high_nitrate": {
        "weather_seed": 15,
        "nitrate_percent": 50,
        "photon_peak": 1000,
        "filename": "data/cleaned_weather_spring.csv",
        },
    "fall_low_nitrate": {
        "weather_seed": 0.9255162147978742,
        "nitrate_percent": 2,
        "photon_peak": 1000,
        "filename": "data/cleaned_weather_fall.csv",
        },
    "fall_high_nitrate": {
        "weather_seed": 0.9255162147978742,
        "nitrate_percent": 50,
        "photon_peak": 1000,
        "filename": "data/cleaned_weather_fall.csv",
        }
    }


class Game:
    def __init__(self, player_name, icon_name, level_name="spring_high_nitrate", start_time=0, resolution=3600,
                 green_thumbs=25):
        since_epoch = time.time()
        self.path_to_logs = "./data/finished_games/{}{}".format(player_name, since_epoch)
        os.makedirs(self.path_to_logs)
        self.log = Log(self.path_to_logs)  # can be turned off
        self.player_name = player_name
        self.icon_name = icon_name
        self.level_name = level_name
        self.time = start_time
        self.resolution = resolution
        self.green_thumbs = green_thumbs
        self.time_left_from_last_simulation = 0  # seconds
        self.plant = Plant(ground_grid_resolution=(20, 6))
        self.environment = Environment(start_time=self.time, scenario=scenarios[level_name])
        self.model = DynamicModel(self.environment, self.plant)
        self.running = True

    def check_game_end(self):
        if self.time / (60 * 60 * 24) >= MAX_DAYS:
            self.running = False

    def force_end_game(self, message) -> dict:
        self.log.close_model_file()
        #df = pandas.read_csv(self.path_to_logs + "/model_logs.csv")
        #plot.generate_big_plot(df, self.path_to_logs)
        scoring.upload_score(self.player_name, self.plant.seed_mass, self.path_to_logs, self.icon_name)
        return {"path_to_logs": self.path_to_logs}

    # dt in seconds
    def update(self, message) -> dict:
        if not self.running:
            self.log.close_model_file()
            return {}
            # create scores
            # close logs
            # upload data
        self.check_game_end()
        delta_t = message["delta_t"]
        growth_percentages = message["growth_percentages"]

        self.time += delta_t
        n_simulations = int((delta_t + self.time_left_from_last_simulation) / self.resolution)
        self.time_left_from_last_simulation = (delta_t + self.time_left_from_last_simulation) % self.resolution
        #print(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} and time_left: {self.time_left_from_last_simulation}")

        '''logger.debug(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} "
                     f"and time_left: {self.time_left_from_last_simulation}")'''

        actions = [(action, content) for action, content in message["shop_actions"].items() if content is not None]
        '''for action in actions:
            logger.debug(f"shop actions from client: {action}")'''

        for action, content in message["shop_actions"].items():
            if content is not None:
                match action:
                    case ("buy_watering_can"):
                        if self.green_thumbs - WATERING_CAN_COST >= 0:
                            self.environment.increase_water_grid(content)
                            self.green_thumbs -= WATERING_CAN_COST
                    case "buy_nitrate":
                        if self.green_thumbs - NITRATE_COST >= 0:
                            self.environment.increase_nitrate_grid(content)
                            self.green_thumbs -= NITRATE_COST
                    case "buy_root":
                        for target in content["directions"]:
                            if self.green_thumbs - ROOT_COST >= 0:
                                self.plant.create_new_root(target)
                                self.green_thumbs -= ROOT_COST
                    case "buy_branch":
                        for i in range(content):
                            if self.green_thumbs - BRANCH_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_branch()
                                    self.green_thumbs -= BRANCH_COST
                    case "buy_leaf":
                        for i in range(content):
                            if self.green_thumbs - LEAF_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_leaf()
                                    self.green_thumbs -= LEAF_COST
                    case "buy_seed":
                        for i in range(content):
                            if self.green_thumbs - FLOWER_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_seed()
                                    self.green_thumbs -= FLOWER_COST

        for i in range(n_simulations):
            self.plant.update(self.resolution)
            self.environment.update(self.resolution)

            '''print(f"Leaf Mass: {self.plant.leaf_mass}, L Mass to grow: {self.plant.get_leaf_mass_to_grow()}, Max: {self.plant.leaf_mass + self.plant.get_leaf_mass_to_grow()} \n"
                  f"Stem Mass: {self.plant.stem_mass}, S Mass to grow: {self.plant.get_stem_mass_to_grow()}, Max: {self.plant.stem_mass + self.plant.get_stem_mass_to_grow()}\n"
                  f"Root Mass: {self.plant.root_mass}, R Mass to grow: {self.plant.get_root_mass_to_grow()}, Max: {self.plant.root_mass + self.plant.get_root_mass_to_grow()}\n"
                  f"Flower Mass: {self.plant.seed_mass}, F Mass to grow: {self.plant.get_seed_mass_to_grow()}, Max: {self.plant.seed_mass + self.plant.get_seed_mass_to_grow()}\n"
                  f"Overall Biomass: {self.plant.get_total_plant_mass()}"
                  )'''

            # Todo check percentages, build seed percentage
            # min 0.1 percent for organs to grow
            percentages = {
                "leaf_percent": max(growth_percentages["leaf_percent"] if self.plant.get_leaf_mass_to_grow() > 0 else 0.1,0.1),
                "stem_percent": max(growth_percentages["stem_percent"] if self.plant.get_stem_mass_to_grow() > 0 else 0.1,0.1),
                "root_percent": max(growth_percentages["root_percent"] if self.plant.get_root_mass_to_grow() > 0 else 0.1,0.1),
                "seed_percent": len(self.plant.seeds) * 10 if self.plant.get_seed_mass_to_grow() > 0 else 0,
                "starch_percent": growth_percentages["starch_percent"],
                "stomata": growth_percentages["stomata"]
                }
            sum_percentages = sum(
                [value for key, value in percentages.items() if key != "starch_percent" and key != "stomata"]) + max(0, percentages["starch_percent"])
            if sum_percentages > 0:
                self.model.simulate(self.resolution, percentages)

        weather_state = self.environment.weather.get_weather_state(int(self.time / 3600))

        nitrate_available_mm = self.environment.nitrate_grid.available_relative_mm(delta_t, self.plant.root_mass, Vmax, Km,
                                                            self.plant.lsystem.root_grid)

        self.log.append_model_row(
            time=self.time,
            temperature=weather_state[0],
            sun_intensity=self.environment.get_sun_intensity(),
            humidity=weather_state[1],
            precipitation=weather_state[2],
            accessible_water=self.environment.water_grid.available_absolute(self.plant.lsystem.root_grid),
            accessible_nitrate=nitrate_available_mm,
            leaf_biomass=self.plant.leaf_mass,
            stem_biomass=self.plant.stem_mass,
            root_biomass=self.plant.root_mass,
            seed_biomass=self.plant.seed_mass,
            starch_pool=self.plant.starch_pool,
            max_starch_pool=self.plant.max_starch_pool,
            water_pool=self.plant.water_pool,
            max_water_pool=self.plant.max_water_pool,
            leaf_percent=growth_percentages["leaf_percent"],
            stem_percent=growth_percentages["stem_percent"],
            root_percent=growth_percentages["root_percent"],
            seed_percent=growth_percentages["seed_percent"],
            starch_percent=growth_percentages["starch_percent"],
            n_leaves=len(self.plant.leafs),
            n_stems=len(self.plant.branches),
            n_roots=len(self.plant.roots),
            n_seeds=len(self.plant.seeds),
            green_thumbs=self.green_thumbs,
            open_spots=growth_percentages["stomata"],
            action=actions,
            )

        if self.model.used_fluxes is not None:
            self.model.used_fluxes["nitrate_available"] = nitrate_available_mm

        game_state = {
            "running": self.running,
            "plant": self.plant.to_dict(),
            "environment": self.environment.to_dict(),
            "green_thumbs": self.green_thumbs,
            "used_fluxes": self.model.used_fluxes,
            "nitrate_available": nitrate_available_mm,
            "gametime": self.time
            }

        return game_state
