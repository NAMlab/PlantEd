import asyncio
from multiprocessing import Process

from PlantEd.server import server
from PlantEd.client import game


if __name__ == "__main__":
    server_process = Process(target=server.start)
    server_process.start()

    game.start()
    server_process.join()