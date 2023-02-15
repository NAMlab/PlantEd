#!/usr/bin/env python

# WS client example

import asyncio
import json
import logging

import websockets

from client import GrowthPercent
from client import GrowthRates
from client.water import Water

logger = logging.getLogger(__name__)


class Client:
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
        await self.websocket.send("{\"event\": \"connect\"}")

    def growth(self):
        return self.loop.run_until_complete(self.__get_growth_percent())

    async def __get_growth_percent(self):
        await self.websocket.send("{\"get_growth_percent\": \"null\"}")
        logger.info(f"Send event GROWTH")

        data = await self.websocket.recv()
        logger.info(f"Received {data}")

        return data["get_growth_percent"]

    def growth_rate(self, growth_percent: GrowthPercent) -> GrowthRates:
        return self.loop.run_until_complete(self.__growth_rate(growth_percent = growth_percent))

    async def __growth_rate(self, growth_percent: GrowthPercent) -> GrowthRates:

        if growth_percent.starch < 0:
            growth_percent.starch = 0

        message = {"growth_rate": {"GrowthPercent": growth_percent.to_json()}}

        logger.info("Sending Request for growth rates."
                     f"Payload is :\n"
                     f"{message}")

        message = json.dumps(message)
        await self.websocket.send(message)
        logger.info(f"Send event growth_rate")

        growth_rates = await self.websocket.recv()
        logger.info(f"Received {growth_rates}")
        growth_rates = GrowthRates.from_json(growth_rates["growth_rate"])

        return growth_rates

    def open_stomata(self):
        self.loop.run_until_complete(self.__open_stomata())
    async def __open_stomata(self):
        logger.debug("Sending request for open_stomata")

        message = "{\"open_stomata\": \"null\"}"

        await self.websocket.send(message)

    def close_stomata(self):
        self.loop.run_until_complete(self.__open_stomata())
    async def __close_stomata(self):
        logger.debug("Sending request for close_stomata")


        message = "{\"close_stomata\": \"null\"}"

        await self.websocket.send(message)

    def deactivate_starch_resource(self):
        self.loop.run_until_complete(self.__deactivate_starch_resource())

    async def __deactivate_starch_resource(self):
        logger.debug("Sending request to deactivate_starch_resource")

        message = "{\"deactivate_starch_resource\": \"null\"}"

        await self.websocket.send(message)

    def activate_starch_resource(self, percentage: float):
        self.loop.run_until_complete(self.__activate_starch_resource(percentage = percentage))

    async def __activate_starch_resource(self, percentage: float):
        logger.debug("Sending request to activate_starch_resource")

        message = {"activate_starch_resource": percentage}
        message = json.dumps(message)

        await self.websocket.send(message)

    def get_water_pool(self) -> Water:
        return self.loop.run_until_complete(self.__get_water_pool())

    async def __get_water_pool(self) -> Water:
        logger.debug("Sending request for water_pool")

        message = "{\"get_water_pool\": \"null\"}"

        await self.websocket.send(message)
        logger.debug("Waiting for answer")

        answer = await self.websocket.recv()
        logger.debug(f"Recived {answer}")

        water: Water = Water.from_json(answer["get_water_pool"])
        logger.debug(f"Decoded answer to {water}")

        return water
