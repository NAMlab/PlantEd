# Usage: python server.py <level>
import asyncio
import websockets
import json
from PlantEd_Server.server.game import Game


def load_game(game_name):
    global game
    game = Game()
    print(f"Loading Game {game_name}")
    # Load environment, weather etc.


def update(delta_t=None, growth_percentages=None, increase_water_grid=None, increase_nitrate_grid=None, buy_new_root=None, reset=False):
    global game
    # Update Plant, Environment, Water grid etc.
    if reset:
        print("Resetting Level Gatersleben")
        game = Game()
        return
    game.update(delta_t, growth_percentages, increase_water_grid, increase_nitrate_grid, buy_new_root)


async def respond(websocket):
    global game
    async for message in websocket:
        update(**json.loads(message))
        response = {
            'plant': game.plant.to_dict(),
            'environment': game.environment.to_dict()
        }
        await websocket.send(json.dumps(response, indent=2))


async def main(port):
    async with websockets.serve(respond, "localhost", port):
        await asyncio.Future()  # run forever


def start(port=8765):
    load_game('Start Server')
    asyncio.run(main(port))


if __name__ == "__main__":
    start()

