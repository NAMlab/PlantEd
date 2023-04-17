#!/usr/bin/env python

# WS client example

import asyncio
import json
import logging

import websockets

from PlantEd.client.leaf import Leaf
from PlantEd.client import GrowthPercent, GrowthRates, Water

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
        logger.info("Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(self.url)

    def growth(self):
        return self.loop.run_until_complete(self.__get_growth_percent())

    async def __get_growth_percent(self):
        await self.websocket.send('{"get_growth_percent": "null"}')
        logger.info("Send event GROWTH")

        data = await self.websocket.recv()
        logger.info(f"Received {data}")

        return data["get_growth_percent"]

    def growth_rate(self, growth_percent: GrowthPercent) -> GrowthRates:
        return self.loop.run_until_complete(
            self.__growth_rate(growth_percent=growth_percent)
        )

    async def __growth_rate(
        self, growth_percent: GrowthPercent
    ) -> GrowthRates:
        if growth_percent.starch < 0:
            growth_percent.starch = 0

        message_dict = {"growth_rate": {"GrowthPercent": growth_percent.to_json()}}

        logger.info(
            "Sending Request for growth rates." f"Payload is :\n" f"{message_dict}"
        )

        message_str = json.dumps(message_dict)
        await self.websocket.send(message_str)
        logger.info("Send event growth_rate")

        answer = await self.websocket.recv()
        logger.info(f"Received {answer}")

        answer = json.loads(answer)
        growth_rates = GrowthRates.from_json(answer["growth_rate"])

        return growth_rates

    def open_stomata(self):
        self.loop.run_until_complete(self.__open_stomata())

    async def __open_stomata(self):
        logger.debug("Sending request for open_stomata")

        message = '{"open_stomata": "null"}'

        await self.websocket.send(message)

    def close_stomata(self):
        self.loop.run_until_complete(self.__close_stomata())

    async def __close_stomata(self):
        logger.debug("Sending request for close_stomata")

        message = '{"close_stomata": "null"}'

        await self.websocket.send(message)

    def deactivate_starch_resource(self):
        self.loop.run_until_complete(self.__deactivate_starch_resource())

    async def __deactivate_starch_resource(self):
        logger.debug("Sending request to deactivate_starch_resource")

        message = '{"deactivate_starch_resource": "null"}'

        await self.websocket.send(message)

    def activate_starch_resource(self, percentage: float):
        self.loop.run_until_complete(
            self.__activate_starch_resource(percentage=percentage)
        )

    async def __activate_starch_resource(self, percentage: float):
        logger.debug("Sending request to activate_starch_resource")

        message = {"activate_starch_resource": percentage}
        message = json.dumps(message)

        await self.websocket.send(message)

    def get_water_pool(self) -> Water:
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """
        return self.loop.run_until_complete(self.__get_water_pool())

    async def __get_water_pool(self) -> Water:
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """

        logger.debug("Sending request for water_pool")

        message = '{"get_water_pool": "null"}'

        await self.websocket.send(message)
        logger.debug("Waiting for answer")

        answer = await self.websocket.recv()
        logger.debug(f"Received {answer}")

        answer = json.loads(answer)
        water: Water = Water.from_json(answer["get_water_pool"])
        logger.debug(f"Decoded answer to {water}")

        return water

    def get_nitrate_percentage(self) -> float:
        """
        Method to retrieve the level of the nitrate pool as a decimal number.
        (NitratePool/ MaxNitratePool).

        Returns: Nitrates percentages as a string in JSON format.

        """
        return self.loop.run_until_complete(self.__get_nitrate_percentage())

    async def __get_nitrate_percentage(self) -> float:
        """
        Method to retrieve the level of the nitrate pool as a decimal number.
        (NitratePool/ MaxNitratePool).

        Returns: Nitrates percentages as a string in JSON format.

        """
        logger.debug("Sending request for nitrate_percentage")

        message = '{"get_nitrate_percentage": "null"}'
        await self.websocket.send(message)
        logger.debug("Waiting for answer")

        answer = await self.websocket.recv()
        logger.debug(f"Received {answer}")

        answer = json.loads(answer)
        answer = answer["get_nitrate_percentage"]

        return float(answer)

    def increase_nitrate(self):
        """
        Method that realizes the increase of the nitrate pool
        through the store.

        """
        return self.loop.run_until_complete(self.__increase_nitrate())

    async def __increase_nitrate(self):
        logger.debug("Sending request for nitrate increase.")

        message = '{"increase_nitrate": "null"}'
        await self.websocket.send(message)

    def get_nitrate_pool(self) -> int:
        """
        Method to request the NitratePool.
        Returns: The available nitrates.

        """
        return self.loop.run_until_complete(self.__get_nitrate_pool())

    async def __get_nitrate_pool(self) -> int:
        logger.debug("Requesting the nitrate pool.")

        message = '{"get_nitrate_pool": "null"}'
        await self.websocket.send(message)

        logger.debug("Waiting for answer")
        answer = await self.websocket.recv()
        logger.debug(f"Received {answer}")

        answer = json.loads(answer)
        answer = answer["get_nitrate_pool"]

        return int(answer)

    def get_actual_water_drain(self) -> float:
        """
        Method that requests the actual Water drain.

        Returns: The Water drain as int.

        """
        return self.loop.run_until_complete(self.__get_actual_water_drain())

    async def __get_actual_water_drain(self) -> float:
        logger.debug("Requesting the water drain value.")

        message = '{"get_actual_water_drain": "null"}'
        await self.websocket.send(message)

        logger.debug("Waiting for answer")
        answer = await self.websocket.recv()
        logger.debug(f"Received {answer}")

        answer = json.loads(answer)
        answer = answer["get_actual_water_drain"]

        return float(answer)

    def create_leaf(self, leaf: Leaf):
        self.loop.run_until_complete(self.__create_leaf(leaf=leaf))

    async def __create_leaf(self, leaf: Leaf):
        logger.debug("Request for the creation of a new leaf.")

        data = leaf.strip2server_version()
        message = {"create_leaf": data.to_json()}
        await self.websocket.send(message)
