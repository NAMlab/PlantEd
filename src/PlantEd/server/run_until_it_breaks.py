# Script to run the server and prod it until it crashes
# Taken and adapted from https://github.com/NAMlab/PlantEd-AI/blob/main/src/planted_env.py
import csv
import sys
import os
import glob
import asyncio
import json
import websockets
import multiprocessing
import collections
import time
import random
from enum import Enum

import numpy as np

from PlantEd.server import server

Biomass = collections.namedtuple("Biomass", "leaf stem root seed")

# Action Space
Action = Enum('Action', [
    'GROW_LEAVES',
    'GROW_STEM',
    'GROW_ROOTS',
    'PRODUCE_STARCH',
    'OPEN_STOMATA',
    'CLOSE_STOMATA',
    'BUY_LEAF',
    'BUY_STEM',
    'BUY_ROOT',
    'BUY_SEED'
], start=0)  # start at 0 because the gym action space starts at 0


# @TODO add these next:
# 10 - watering can
# 11 - add fertilizer

class PlantEdEnv():
    metadata = {"render_modes": ["ansi"], "render_fps": 30}

    def __init__(self, instance_name="PlantEd_instance", port=8765):
        self.port = port
        self.instance_name = instance_name
        self.csv_file = None
        self.server_process = None
        self.running = False
        self.game_counter = 0  # add 1 at each reset --> to save all the logs

    def __del__(self):
        self.close()

    def close(self):
        if (self.csv_file):
            self.csv_file.close()
        if (self.server_process):
            self.server_process.terminate()
            print("Terminated server process, waiting 5 sec")
            time.sleep(5)
        self.running = False

    def reset(self, seed=None, options=None):
        if self.running:
            self.close()

        self.game_counter += 1
        self.init_csv_logger()

        self.server_process = multiprocessing.Process(target=self.start_server)
        self.server_process.start()
        print("Server process started, waiting 10 sec...")
        time.sleep(10)
        asyncio.run(self.load_level())

        self.running = True
        self.last_step_biomass = -1
        self.stomata = True
        self.last_observation = None

        observation, reward, terminated, truncated, info = self.step(2)
        return (observation, info)

    async def load_level(self):
        async with websockets.connect("ws://localhost:" + str(self.port)) as websocket:
            message = {
                "type": "load_level",
                "message": {
                    "player_name": "Planted-AI",
                    "level_name": "LEVEL_NAME",
                }
            }
            await websocket.send(json.dumps(message))
            response = await websocket.recv()
            print(response)

    def render(self):
        pass

    def start_server(self):
        sys.stdout = open("server.log", 'w')
        sys.stderr = open("server.err", 'w')
        server.start(self.port)

    def init_csv_logger(self):
        self.csv_file = open(self.instance_name + '_run' + str(self.game_counter) + '.csv', 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        self.csv_writer.writerow(
            ["time", "temperature", "sun_intensity", "humidity", "precipitation", "accessible_water",
             "accessible_nitrate",
             "leaf_biomass", "stem_biomass", "root_biomass", "seed_biomass", "starch_pool", "max_starch_pool",
             "water_pool", "max_water_pool",
             "leaf_percent", "stem_percent", "root_percent", "seed_percent", "starch_percent", "action",
             "reward"])

    def get_biomasses(self, res):
        leaf = sum([x[1] for x in res["plant"]["leafs_biomass"]])
        stem = sum([x[1] for x in res["plant"]["stems_biomass"]])
        root = res["plant"]["roots_biomass"]
        seed = sum([x[1] for x in res["plant"]["seeds_biomass"]])
        return (Biomass(leaf, stem, root, seed))

    def get_n_organs(self, res):
        return ([
            len(res["plant"]["leafs_biomass"]),
            len(res["plant"]["stems_biomass"]),
            len(res["plant"]["root"]["first_letters"]),
            len(res["plant"]["seeds_biomass"]),
        ])

    def step(self, action):
        return (asyncio.run(self._async_step(action)))

    async def _async_step(self, a):
        print("step. ", end="")
        action = Action(a)
        print(action.name)
        terminated = False
        truncated = False
        async with websockets.connect("ws://localhost:" + str(self.port)) as websocket:
            if action == Action.OPEN_STOMATA:
                self.stomata = True
            if action == Action.CLOSE_STOMATA:
                self.stomata = False
            message = {
                "type": "simulate",
                "message": {
                    "delta_t": 60 * 10,
                    "growth_percentages": {
                        "leaf_percent": 100 if action == Action.GROW_LEAVES else 0,
                        "stem_percent": 100 if action == Action.GROW_STEM else 0,
                        "root_percent": 100 if action == Action.GROW_ROOTS else 0,
                        "seed_percent": 0,
                        "starch_percent": 100 if action not in [Action.GROW_LEAVES, Action.GROW_STEM,
                                                                Action.GROW_ROOTS] else -100,
                        # make starch when manipulating stomata or new roots
                        "stomata": self.stomata,
                    },
                    "shop_actions": {
                        "buy_watering_can": None,
                        "buy_nitrate": None,
                        "buy_leaf": 1 if action == Action.BUY_LEAF else None,
                        "buy_branch": 1 if action == Action.BUY_STEM else None,
                        "buy_root": None,
                        # (random.gauss(0, 0.4), random.gauss(1, 0.3)) if action == Action.BUY_ROOT else None,
                        "buy_seed": 1 if action == Action.BUY_SEED else None
                    }
                }
            }
            try:
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                res = json.loads(response)

                terminated = not res["running"]
                root_grid = np.array(res["plant"]["root"]["root_grid"])
                nitrate_grid = np.array(res["environment"]["nitrate_grid"])
                water_grid = np.array(res["environment"]["water_grid"])

                biomasses = self.get_biomasses(res)

                res["environment"]["accessible_water"] = (root_grid * water_grid).sum()
                res["environment"]["accessible_nitrate"] = (root_grid * nitrate_grid).sum()

                observation = {
                    # Environment
                    "temperature": np.array([res["environment"]["temperature"]]).astype(np.float32),
                    "sun_intensity": np.array([res["environment"]["sun_intensity"]]).astype(np.float32),
                    "humidity": np.array([res["environment"]["humidity"]]).astype(np.float32),
                    "accessible_water": np.array([res["environment"]["accessible_water"]]).astype(np.float32),
                    "accessible_nitrate": np.array([res["environment"]["accessible_nitrate"]]).astype(np.float32),
                    "green_thumbs": np.array([res["green_thumbs"]]).astype(np.float32),

                    # Plant
                    "biomasses": np.array([
                        biomasses.leaf,
                        biomasses.stem,
                        biomasses.root,
                        biomasses.seed,
                    ]).astype(np.float32),
                    "n_organs": np.array(self.get_n_organs(res)).astype(np.float32),
                    "starch_pool": np.array([res["plant"]["starch_pool"]]).astype(np.float32),
                    "max_starch_pool": np.array([res["plant"]["max_starch_pool"]]).astype(np.float32),
                    "stomata_state": np.array([self.stomata])
                }
                self.last_observation = observation

                reward = self.calc_reward(biomasses)
                self.write_log_row(res, message["message"], biomasses, action, reward)
            except websockets.exceptions.ConnectionClosedError:
                print("SERVER CRASHED")
                # @TODO This is not optimal because it pretends that what the actor did had no influence at all.
                observation = self.last_observation
                reward = 0.0
                truncated = True

            return (observation, reward, terminated, truncated, {})

    def calc_reward(self, biomasses):
        total_biomass = biomasses.leaf + biomasses.stem + biomasses.root + biomasses.seed
        reward = 0 if self.last_step_biomass == -1 else (
                                                                    total_biomass - self.last_step_biomass) / self.last_step_biomass
        self.last_step_biomass = total_biomass
        return (reward)

    def write_log_row(self, res, game_state, biomasses, action, reward):
        self.csv_writer.writerow([
            res["environment"]["time"],
            res["environment"]["temperature"],
            res["environment"]["sun_intensity"],
            res["environment"]["humidity"],
            res["environment"]["precipitation"],
            res["environment"]["accessible_water"],
            res["environment"]["accessible_nitrate"],

            biomasses.leaf,
            biomasses.stem,
            biomasses.root,
            biomasses.seed,
            res["plant"]["starch_pool"],
            res["plant"]["max_starch_pool"],
            res["plant"]["water_pool"],
            res["plant"]["max_water_pool"],

            game_state["growth_percentages"]["leaf_percent"],
            game_state["growth_percentages"]["stem_percent"],
            game_state["growth_percentages"]["root_percent"],
            game_state["growth_percentages"]["seed_percent"],
            game_state["growth_percentages"]["starch_percent"],
            action.name,

            reward
        ])


if __name__ == "__main__":
    env = PlantEdEnv("CrashNBurn")
    env.reset()
    truncated = False
    while not truncated:
        observation, reward, terminated, truncated, info = env.step(Action(random.randint(0, 9)))
        if terminated:
            env.reset()
    env.close()
