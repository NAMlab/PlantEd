#!/usr/bin/env python

import asyncio
import json
import logging

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from client.growth_percentage import GrowthPercent
from client.water import Water
from fba.dynamic_model import DynamicModel
from gameobjects.plant import Plant

logger = logging.getLogger(__name__)


class Server:
    """
    A server that provides all necessary data for the user interface.
    """

    def __init__(self):
        self.clients = set()
        self.websocket = None
        self.plant: Plant
        self.model: DynamicModel

    def start(self, plant: Plant, model: DynamicModel):
        """
        Method to start the server.
        """
        self.plant = plant
        self.model = model
        asyncio.run(self.__start())

    async def __start(self):
        async with websockets.serve(self.main_handler,
                                    "localhost",
                                    4000,
                                    ping_interval=10,
                                    ping_timeout=30, ):
            await asyncio.Future()  # run forever

    async def register(self, ws: WebSocketServerProtocol):
        self.clients.add(ws)
        logger.info(f"{ws.remote_address} connected.")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logger.info(f"{ws.remote_address} disconnected.")

    async def send_growth(self, ws: WebSocketServerProtocol):

        message = json.dumps({
            "leaf_percent": self.plant.organs[0].percentage,
            "stem_percent": self.plant.organs[1].percentage,
            "root_percent": self.plant.organs[2].percentage,
            "starch_percent": self.plant.organ_starch.percentage,
        })
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
        logger.info("Handler ready.")
        await self.register(ws)
        try:
            while True:
                request = await ws.recv()
                logger.info(f"Received {request}")

                request_decoded = json.loads(request)
                try:
                    command = request_decoded["event"]
                except KeyError as e:
                    logger.error("Recived Message could not be decoded"
                                 f"\n {e}")
                    # ToDo send error message back
                    continue

                match command:
                    case "GROWTH":
                        logger.debug("Received command identified as request of growth values.")
                        await self.send_growth(ws)
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
                    case _:
                        logger.error("Received command could not be identified")

        finally:
            await self.unregister(ws)
