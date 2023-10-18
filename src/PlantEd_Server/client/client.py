import asyncio
import multiprocessing
import threading
import time
from asyncio import Future

import websockets
import json

request_running = False


class Client:
    def __init__(self, port):
        self.url = f"ws://localhost:{port}"
        self.data = {}

    async def send_and_get_response(self):
        global request_running
        if not request_running:
            request_running = True
            print(" --> Sending request...")
            async with websockets.connect("ws://localhost:8765") as websocket:
                game_state = {
                    "delta_t": 360 * 1,
                    "growth_percentages": {
                        "leaf_percent": 1,
                        "stem_percent": 0,
                        "root_percent": 1,
                        "seed_percent": 0,
                        "starch_percent": -10,
                        "stomata": False,
                    }
                }
                await websocket.send(json.dumps(game_state))
                response = await websocket.recv()
                print(" --> Received response, updating state")
                #plant.state = plant.state + 1
                request_running = False

    '''async def send_and_get_response(self):
        global request_running
        if not request_running:
            async with websockets.connect("ws://localhost:8765") as websocket:
                request_running = True
                #print(" --> Sending request...")
                # get game state
                # send json
                # recv json
                # move data to gameloop update?

                game_state = {
                    "delta_t": 360 * 1,
                    "growth_percentages": {
                        "leaf_percent": 1,
                        "stem_percent": 0,
                        "root_percent": 1,
                        "seed_percent": 0,
                        "starch_percent": -10,
                        "stomata": False,
                    }
                }
                #print(json.dumps(game_state, indent=2))
                await websocket.send(json.dumps(game_state))
                # print("Response:")
                response = await websocket.recv()
                # print(response)
                #print(" --> Received response, updating state")
                request_running = False
                self.data = response'''
