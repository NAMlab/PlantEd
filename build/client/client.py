#!/usr/bin/env python

# WS client example

import asyncio
import json
import logging

import websockets

from build.client.init import GrowthPercent
from build.client.init import GrowthRates
from client.water import Water

logger = logging.getLogger(__name__)


class Client():
    """
    A client that serves as an interface between the UI and the server.
    At the same time, it can also serve as an interface for software
    that is designed to play the game without the UI.

    """

    def __init__(self):
        self.url = "ws://localhost:4000"
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.__connect())
        logger.info(f"Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(self.url)

    def growth(self):
        return self.loop.run_until_complete(self.__growth())

    async def __growth(self):
        await self.websocket.send("{\"event\": \"GROWTH\"}")
        logger.info(f"Send event GROWTH")

        data = await self.websocket.recv()
        logger.info(f"Received {data}")

        return data

    def growth_rate(self, data: GrowthPercent) -> GrowthRates:
        return self.loop.run_until_complete(self.__growth_rate(data = data))

    async def __growth_rate(self, data: GrowthPercent) -> GrowthRates:

        if data.starch < 0:
            data.starch = 0

        message = {"event": "growth_rate"}
        message["data"] = data.to_json()

        logger.info("Sending Request for growth rates."
                     f"Payload is :\n"
                     f"{message}")

        message = json.dumps(message)
        await self.websocket.send(message)
        logger.info(f"Send event growth_rate")

        data = await self.websocket.recv()
        logger.info(f"Received {data}")
        data = GrowthRates.from_json(data)

        return data

    def open_stomata(self):
        self.loop.run_until_complete(self.__open_stomata())
    async def __open_stomata(self):
        logger.debug("Sending request for open_stomata")

        message = "{\"event\": \"open_stomata\"}"

        await self.websocket.send(message)

    def close_stomata(self):
        self.loop.run_until_complete(self.__open_stomata())
    async def __close_stomata(self):
        logger.debug("Sending request for close_stomata")


        message = "{\"event\": \"close_stomata\"}"

        await self.websocket.send(message)

    def deactivate_starch_resource(self):
        self.loop.run_until_complete(self.__deactivate_starch_resource())

    async def __deactivate_starch_resource(self):
        logger.debug("Sending request to deactivate_starch_resource")

        message = "{\"event\": \"deactivate_starch_resource\"}"

        await self.websocket.send(message)

    def activate_starch_resource(self):
        self.loop.run_until_complete(self.__activate_starch_resource())

    async def __activate_starch_resource(self):
        logger.debug("Sending request to activate_starch_resource")

        message = "{\"event\": \"activate_starch_resource\"}"

        await self.websocket.send(message)

    def get_water_pool(self) -> Water:
        return self.loop.run_until_complete(self.__get_water_pool())

    async def __get_water_pool(self) -> Water:
        logger.debug("Sending request for water_pool")

        message = "{\"event\": \"get_water_pool\"}"

        await self.websocket.send(message)
        logger.debug("Waiting for answer")

        answer = await self.websocket.recv()
        logger.debug(f"Recived {answer}")

        water: Water = Water.from_json(answer)
        logger.debug(f"Decoded answer to {water}")

        return water
