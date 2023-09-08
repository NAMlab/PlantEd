#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import multiprocessing
import threading
from asyncio import Future
from multiprocessing import Event
from pathlib import Path
from typing import Callable, Literal

import websockets

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.client.update import UpdateInfo
from PlantEd.client.water import Water
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.nitrate import Nitrate
from PlantEd.server.plant.plant import Plant

logger = logging.getLogger(__name__)


class Client:
    """
    A client that serves as an interface between the UI and the server.
    At the same time, it can also serve as an interface for software
    that is designed to play the game without the UI.

    """

    def __init__(self, port: int = 4000):
        self.url = f"ws://localhost:{port}"
        logger.debug(f"Connecting to server {self.url}")

        self.__future: asyncio.Future = None
        self.loop: asyncio.AbstractEventLoop = None
        self.expected_receive: dict[str, Future] = dict()
        ready: multiprocessing.Event = multiprocessing.Event()

        thread = threading.Thread(
            target=asyncio.run, daemon=True, args=(self.__start(ready=ready),)
        )
        self.thread: threading.Thread = thread
        self.thread.start()
        self.lock = asyncio.Lock()
        ready.wait()

        logger.info("Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(self.url)

    async def __start(self, ready: Event):
        self.loop = asyncio.get_running_loop()
        self.__future = self.loop.create_future()

        connect = self.__connect()

        await self.loop.create_task(connect, name="Connect")
        self.loop.create_task(self.__receive_handler(), name="receive_handler")
        ready.set()

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
                try:
                    future = self.expected_receive[id_string]
                except KeyError as e:
                    logger.error(
                        f"Task {id_string} was not found. All expected are {self.expected_receive.keys()}",
                        exc_info=e,
                    )
                    continue

                logger.debug(
                    f"Setting future for {id_string} as done with result {payload}"
                )
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

        task = self.__receive_growth_rate(future=future_received, callback=callback)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __receive_growth_rate(
        self, future: Future, callback: Callable[[Plant], None]
    ):
        await future
        logger.debug(
            "Results of the growth calculation obtained. "
            "Create Plant object and invoke callback."
        )

        plant = Plant.from_json(future.result())

        logger.debug("Plants object created. Execute callback.")

        callback(plant)
        logger.debug("Callback executed.")

    async def __request_growth_rate(self, growth_percent: GrowthPercent):
        if growth_percent.starch < 0:
            growth_percent.starch = 0

        message_dict = {"growth_rate": {"GrowthPercent": growth_percent.to_json()}}

        logger.info(f"Sending Request for growth rates. Payload is : {message_dict}")

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

        task = self.__receive_get_water_pool(future=future_received, callback=callback)
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

        task = self.__increase_nitrate(µmol_nitrate=µmol_nitrate)
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

        task = self.__receive_nitrate_pool(future=future_received, callback=callback)
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
            self.__create_leaf(leaf=leaf), self.loop
        )
        result = future.result()
        return result

    async def __create_leaf(self, leaf: Leaf):
        logger.debug("Request for the creation of a new leaf.")

        message = json.dumps({"create_leaf": leaf.to_dict()})
        await self.websocket.send(message)

    def update(self, update_info: UpdateInfo):
        task = self.__update(update_info=update_info)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __update(self, update_info: UpdateInfo):
        logger.debug("Request update.")

        message = {"update": update_info.to_json()}
        await self.websocket.send(message)

    def get_environment(self, callback: Callable[[Environment], None]):
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """

        future_received = self.loop.create_future()

        self.expected_receive["get_environment"] = future_received

        task = self.__get_environment(future=future_received, callback=callback)
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __get_environment(
        self, future: Future, callback: Callable[[Environment], None]
    ):
        logger.debug("Sending request for environment")

        message = '{"get_environment": "null"}'

        await self.websocket.send(message)

        await future
        payload = future.result()
        logger.debug(f"Received following as answer for environment request: {payload}")

        env = Environment.from_json(payload)

        callback(env)

    def create_new_first_letter(
        self,
        dir,
        pos,
        mass,
        dist,
    ):
        task = self.__create_new_first_letter(
            dir=dir,
            pos=pos,
            mass=mass,
            dist=dist,
        )
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __create_new_first_letter(
        self,
        dir,
        pos,
        mass,
        dist,
    ):
        logger.debug("Sending request for new first letter of root system")
        message = json.dumps(
            {
                "create_new_first_letter": {
                    "dir": dir,
                    "pos": pos,
                    "mass": mass,
                    "dist": dist,
                }
            }
        )

        await self.websocket.send(message)

    def add2grid(
        self,
        amount: float,
        x: int,
        y: int,
        grid: Literal["nitrate", "water"],
    ):
        """
        The method allows access to both grids on the server. It thus enables the use of add2grid of the
        MetaboliteGrid objects of the server-side environment.

        Args:
            amount: Quantity in micromol to be added to the celle of the grid.
            x: X position within the grid.
            y: Y position within the grid.
            grid: The grid to be used. Possible here are 'nitrate' or 'water'.

        Returns:

        """
        task = self.__add2grid(
            amount=amount,
            x=x,
            y=y,
            grid=grid,
        )
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __add2grid(
        self,
        amount,
        x,
        y,
        grid,
    ):
        logger.debug("Sending request to add2grid")
        message = json.dumps(
            {"add2grid": {"amount": amount, "x": x, "y": y, "grid": grid}}
        )

        await self.websocket.send(message)

    def load_level(self):
        lock = threading.Lock()
        lock.acquire()

        task = self.__load_level(lock=lock)
        asyncio.run_coroutine_threadsafe(task, self.loop)
        lock.acquire()

    async def __load_level(self, lock: threading.Lock):
        future_received = self.loop.create_future()
        self.expected_receive["load_level"] = future_received

        await self.websocket.send('{"load_level": "null"}')

        await future_received
        lock.release()
