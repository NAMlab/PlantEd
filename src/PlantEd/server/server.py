# Usage: python server.py <level>
import asyncio
import websockets
import json
from PlantEd.server.game import Game


class Server:
    def __init__(self):
        self.game = None

    def load_level(self, command) -> dict:
        self.game = Game(
            player_name=command["player_name"],
            level_name=command["level_name"],
        )
        print(f"Loading Game {self.game.level_name}")
        return {"running": self.game.running}

    def update(self, message) -> dict:
        # Update Plant, Environment, Water grid etc.
        game_state = self.game.update(message)
        return game_state

    async def respond(self, websocket):
        async for message in websocket:
            command = json.loads(message)
            response = {}
            if command["type"] == "simulate":
                response = self.update(command["message"])

            elif command["type"] == "load_level":
                response = self.load_level(command["message"])

            await websocket.send(json.dumps(response, indent=2))

    async def main(self, port):
        async with websockets.serve(self.respond, "localhost", port):
            await asyncio.Future()  # run forever


def start(port=8765):
    server = Server()
    asyncio.run(server.main(port))


if __name__ == "__main__":
    start()
