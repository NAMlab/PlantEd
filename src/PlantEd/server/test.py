import asyncio
import json

import websockets
import pygame


class Plant:
    state = 0


request_running = False


async def send_and_get_response(plant):
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
                },
            }
            await websocket.send(json.dumps(game_state))
            response = await websocket.recv()
            print(" --> Received response, updating state")
            plant.state = plant.state + 1
            request_running = False


async def main():
    frame = 1
    plant = Plant()
    timer = pygame.time.Clock()
    print("Starting game loop...")
    while True:
        timer.tick(30)
        print(
            "Currently in frame " + str(frame) + ". Plant state = " + str(plant.state)
        )
        frame = frame + 1
        task = asyncio.create_task(send_and_get_response(plant))
        await asyncio.sleep(0)


asyncio.run(main())
