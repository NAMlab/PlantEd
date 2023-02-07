#!/usr/bin/env python

import asyncio
import json
import logging
import threading
from typing import Optional

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from client.growth_percentage import GrowthPercent
from client.water import Water
from fba.dynamic_model import DynamicModel

logger = logging.getLogger(__name__)


class Server:
    """
    A server that provides all necessary data for the user interface.
    """

    def __init__(self, model:DynamicModel):
        self.clients = set()
        self.websocket: websockets.WebSocketServer = None
        self.model: DynamicModel = model
        self.__future: asyncio.Future = None
        self.loop: asyncio.AbstractEventLoop = None

        thread = threading.Thread(
            target=asyncio.run,
            daemon=True,
            args=(self.__start(), )
        )
        self.thread: threading.Thread = thread

    def start(self):
        """
        Method to start the server.
        """

        logger.info("Starting the server.")
        self.thread.start()

    def kill(self):
        """
        Method to kill the server.
        """

        self.loop.stop()

        self.thread.join()

    def stop(self):
        """
        Method to shut down the local server.
        Does not need to run inside the same thread or process as the server.
        """
        # self.__future.set_result("")
        asyncio.run_coroutine_threadsafe(self.__stop_server(), self.loop)

        self.thread.join()
        logger.debug("Thread closed")

    async def __stop_server(self):
        self.__future.set_result("")

    async def __start(self):
        self.loop = asyncio.get_running_loop()
        self.__future = self.loop.create_future()

        async with websockets.serve(self.main_handler,
                                    "localhost",
                                    4000,
                                    ping_interval=10,
                                    ping_timeout=30,
                                        ) as websocket:
            self.websocket = websocket
            await self.__future


    async def open_connection(self, ws: WebSocketServerProtocol):
        self.clients.add(ws)
        logger.info(f"{ws.remote_address} connected.")

    async def close_connection(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logger.info(f"{ws.remote_address} disconnected.")

    async def send_growth_percent(self, ws: WebSocketServerProtocol):

        message = self.model.percentages.to_json()
        logger.info(f"Sending {message}")
        await asyncio.wait([client.send(message) for client in self.clients])

    async def calc_send_growth_rate(self, data):


        logger.info(f"Calculating growth rates from {data}")
        growth_percent: GrowthPercent = GrowthPercent.from_json(data)
        self.model.calc_growth_rate(leaf_percent=growth_percent.leaf,
                                    stem_percent=growth_percent.stem,
                                    root_percent=growth_percent.root,
                                    starch_percent=growth_percent.starch,
                                    flower_percent=growth_percent.flower,
                                    )

        growth_rates = self.model.get_rates()
        logger.info(f"Calculated growth rates: \n {growth_rates}")
        message = growth_rates.to_json()

        # send growth_rates as json
        logger.info(f"Sending following answer for growth rates. \n {message}")
        await asyncio.wait([client.send(message) for client in self.clients])

    async def open_stomata(self):
        logger.info("Opening stomata")
        self.model.open_stomata()

    async def close_stomata(self):
        logger.info("Closing stomata")
        self.model.close_stomata()

    async def deactivate_starch_resource(self):
        logger.info("Deactivating starch use")
        self.model.deactivate_starch_resource()

    async def activate_starch_resource(self):
        logger.info("Activating starch use")
        self.model.activate_starch_resource()

    async def get_water_pool(self):
        logger.info("Creating Water Object and sending it back")

        water = Water(
            water_pool=self.model.water_pool,
            max_water_pool=self.model.max_water_pool
        )

        answer = water.to_json()

        logger.debug(f"Responding to a water request with {answer}")

        await asyncio.wait([client.send(answer) for client in self.clients])

    async def main_handler(self, ws: WebSocketServerProtocol):
        """
        Method that accepts all requests to the server
        and passes them on to the responsible methods.
        """
        logger.debug(f"Connection from {ws.remote_address} established.")
        await self.open_connection(ws)
        logger.debug(f"{ws.remote_address} registered as client")

        while True:
            try:
                request = await ws.recv()
            except websockets.ConnectionClosedOK:
                await self.close_connection(ws)
                logger.debug(f"{ws.remote_address} unregistered.")
                break

            logger.info(f"Received {request}")

            request_decoded = json.loads(request)
            try:
                command = request_decoded["event"]
            except KeyError as e:
                logger.error("Received Message could not be decoded", exc_info= True)
                # ToDo send error message back
                continue

            match command:

                case "get_growth_percent":
                    logger.debug("Received command identified as request of growth_percent.")
                    await self.send_growth_percent(ws)

                case "growth_rate":
                    logger.debug("Received command identified as calculation of growth_rates.")

                    await self.calc_send_growth_rate(data=request_decoded["data"])
                case "open_stomata":
                    logger.debug("Received command identified as open_stomata.")

                    await self.open_stomata()

                case "close_stomata":
                    logger.debug("Received command identified as close_stomata.")

                    await self.close_stomata()

                case "deactivate_starch_resource":
                    logger.debug("Received command identified as deactivate_starch_resource.")

                    await self.deactivate_starch_resource()

                case "activate_starch_resource":
                    logger.debug("Received command identified as activate_starch_resource.")

                    await self.activate_starch_resource()

                case "get_water_pool":
                    logger.debug("Received command identified as get_water_pool.")

                    await self.get_water_pool()

                case "stop":
                    logger.debug("Received command identified as stop.")

                    # await self.__stop_server()

                case _:
                    logger.error("Received command could not be identified")

                    continue
