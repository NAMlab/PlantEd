import asyncio
import multiprocessing
from multiprocessing import Process

from PlantEd.server import server

if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')
    server_process = Process(target=server.start)
    server_process.start()

    try:
        from PlantEd.client import game

        game.start()
    finally:
        server_process.terminate()
        server_process.join()
