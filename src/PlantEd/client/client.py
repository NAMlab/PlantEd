#!/usr/bin/env python
# -*- coding: utf-8 -*-

# WS client example

import asyncio
import json
import logging
import threading
from asyncio import Future
from pathlib import Path
from typing import Callable

import websockets

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.client.leaf import Leaf
from PlantEd.client.update import UpdateInfo
from PlantEd.client.water import Water
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.plant import Plant

logger = logging.getLogger(__name__)

class Client:
    """
    A client that serves as an interface between the UI and the server.
    At the same time, it can also serve as an interface for software
    that is designed to play the game without the UI.

    """

    def __init__(self, port:int = 4000):

        self.url = f"ws://localhost:{port}"

        self.__future: asyncio.Future = None
        self.loop: asyncio.AbstractEventLoop = None
        self.expected_receive: dict[str, Future] = dict()

        thread = threading.Thread(
            target=asyncio.run, daemon=True, args=(self.__start(),)
        )
        self.thread: threading.Thread = thread
        self.thread.start()
        self.lock = asyncio.Lock()

        logger.info("Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(self.url)

    async def __start(self):
        self.loop = asyncio.get_running_loop()
        self.__future = self.loop.create_future()

        connect = self.__connect()

        await self.loop.create_task(connect, name="Connect")
        self.loop.create_task(
            self.__receive_handler(), name="get_nitrate_pool"
        )
        await self.__future

    def stop(self):
        """
        Method to stop the client.
        Does not need to run inside the same thread or process as the server.
        """
        # self.__future.set_result("")
        asyncio.run_coroutine_threadsafe(self.__stop_client(), self.loop)

        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()
        logger.debug("Client thread closed")

    async def __stop_client(self):
        """
        Internal function that stops the websocket by assigning a result
        to the future object.

        """
        self.__future.set_result("")

    async def __receive_handler(self):
        while True:
            answer = await self.websocket.recv()

            logger.info(f"Received {answer}")

            data: dict = json.loads(answer)

            for id_string, payload in data.items():
                future = self.expected_receive[id_string]

                logger.debug(f"Setting future for {id_string} as done with result {payload}")
                future.set_result(payload)

    def growth_rate(
        self,
        growth_percent: GrowthPercent,
        callback: Callable[[Plant], None],
    ):
        task = self.__request_growth_rate(growth_percent=growth_percent)
        future_received = self.loop.create_future()

        self.expected_receive["growth_rate"] = future_received
        asyncio.run_coroutine_threadsafe(task, self.loop)

        task = self.__receive_growth_rate(
            future=future_received, callback=callback
        )
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __receive_growth_rate(
        self, future: Future, callback: Callable[[Plant], None]
    ):
        await future
        logger.debug("Results of the growth calculation obtained. "
                     "Create Plant object and invoke callback.")

        plant = Plant.from_json(future.result())

        logger.debug("Plants object created. Execute callback.")

        callback(plant)

        logger.debug("Callback executed.")

    async def __request_growth_rate(self, growth_percent: GrowthPercent):
        if growth_percent.starch < 0:
            growth_percent.starch = 0

        message_dict = {
            "growth_rate": {"GrowthPercent": growth_percent.to_json()}
        }

        logger.info(
            "Sending Request for growth rates."
            f"Payload is : "
            f"{message_dict}"
        )

        message_str = json.dumps(message_dict)

        await self.websocket.send(message_str)
        logger.info("Send event growth_rate")

    def open_stomata(self):
        task = self.__open_stomata()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __open_stomata(self):
        logger.debug("Sending request for open_stomata")

        message = '{"open_stomata": "null"}'

        await self.websocket.send(message)

    def close_stomata(self):
        task = self.__open_stomata()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __close_stomata(self):
        logger.debug("Sending request for close_stomata")

        message = '{"close_stomata": "null"}'

        await self.websocket.send(message)

    def deactivate_starch_resource(self):
        task = self.__deactivate_starch_resource()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __deactivate_starch_resource(self):
        logger.debug("Sending request to deactivate_starch_resource")

        message = '{"deactivate_starch_resource": "null"}'

        await self.websocket.send(message)

    def activate_starch_resource(self, percentage: float):
        task = self.__activate_starch_resource(percentage=percentage)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __activate_starch_resource(self, percentage: float):
        logger.debug("Sending request to activate_starch_resource")

        message = {"activate_starch_resource": percentage}
        message = json.dumps(message)

        await self.websocket.send(message)

    def set_water_pool(self, water: Water):
        """ """
        task = self.__set_water_pool(water=water)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __set_water_pool(self, water: Water):
        logger.debug(f"Sending request to set_water_pool with payload {water}")

        message = {"set_water_pool": water.to_json()}
        message = json.dumps(message)

        await self.websocket.send(message)

    def stop_water_intake(self):
        task = self.__stop_water_intake()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __stop_water_intake(self):
        logger.debug("Sending request to stop_water_intake")

        message = '{"stop_water_intake": "null"}'

        await self.websocket.send(message)

    def enable_water_intake(self):
        task = self.__enable_water_intake()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __enable_water_intake(self):
        logger.debug("Sending request to enable_water_intake")

        message = '{"enable_water_intake": "null"}'

        await self.websocket.send(message)

    def get_water_pool(self, callback: Callable[[Water], None]):
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """

        future_received = self.loop.create_future()

        self.expected_receive["get_water_pool"] = future_received

        task = self.__receive_get_water_pool(
            future=future_received, callback=callback
        )
        asyncio.run_coroutine_threadsafe(task, self.loop)

        task = self.__request_get_water_pool()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __receive_get_water_pool(
        self, future: Future, callback: Callable[[Water], None]
    ):
        await future

        water = Water.from_json(future.result())

        callback(water)

    async def __request_get_water_pool(self):
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """

        logger.debug("Sending request for water_pool")

        message = '{"get_water_pool": "null"}'

        await self.websocket.send(message)

    def increase_nitrate(self, µmol_nitrate: float):
        """
        Method that realizes the increase of the nitrate pool
        through the store.

        """

        task = self.__increase_nitrate(µmol_nitrate = µmol_nitrate)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __increase_nitrate(self, µmol_nitrate: float):
        logger.debug("Sending request for nitrate increase.")

        message = f'{{"increase_nitrate": "{µmol_nitrate}"}}'
        await self.websocket.send(message)

    def get_nitrate_pool(self, callback: Callable[[Nitrate], None]):
        """
        Method to request the NitratePool.
        Returns: The available nitrates.

        """
        future_received = self.loop.create_future()
        self.expected_receive["get_nitrate_pool"] = future_received

        task = self.__receive_nitrate_pool(
            future=future_received, callback=callback
        )
        asyncio.run_coroutine_threadsafe(task, self.loop)

        task = self.__request_nitrate_pool()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __request_nitrate_pool(self):
        logger.debug("Requesting the nitrate pool.")

        message = '{"get_nitrate_pool": "null"}'

        await self.websocket.send(message)

        return

    async def __receive_nitrate_pool(
        self, future: Future, callback: Callable[[Nitrate], None]
    ):
        await future

        nitrate = Nitrate.from_json(future.result())
        callback(nitrate)

    def create_leaf(self, leaf: Leaf):
        future = asyncio.run_coroutine_threadsafe(
            self.self.__create_leaf(leaf=leaf), self.loop
        )
        result = future.result()
        return result

    async def __create_leaf(self, leaf: Leaf):
        logger.debug("Request for the creation of a new leaf.")

        data = leaf.strip2server_version()
        message = {"create_leaf": data.to_json()}
        await self.websocket.send(message)

    def update(self, update_info: UpdateInfo):
        task = self.__update(update_info=update_info)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __update(self, update_info: UpdateInfo):
        logger.debug("Request update.")

        message = {"update": update_info.to_json()}
        await self.websocket.send(message)
