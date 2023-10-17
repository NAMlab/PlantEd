#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import multiprocessing
import threading
from asyncio import Future, InvalidStateError
from multiprocessing.synchronize import Event
from typing import Callable, Literal, Optional

import websockets

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.plant import Plant
from websockets.exceptions import ConnectionClosedOK

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

        self.__future: Optional[asyncio.Future] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.expected_receive: dict[str, Future] = dict()
        ready: Event = multiprocessing.Event()

        thread = threading.Thread(
            target=asyncio.run, daemon=True, args=(self.__start(ready=ready),)
        )
        self.thread: threading.Thread = thread
        self.thread.start()
        self.lock = asyncio.Lock()
        self.flush_lock = threading.Semaphore(value=0)
        ready.wait()

        logger.info("Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(
            self.url, logger=logging.getLogger(__name__ + ".websocket")
        )

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
        asyncio.run_coroutine_threadsafe(self.__stop_client(), self.loop)

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
            try:
                answer = await self.websocket.recv()
            except ConnectionClosedOK:
                logger.info(
                    "The server has been terminated and has closed the"
                    " connection. The client will now be stopped."
                )
                await self.__stop_client()
                break

            logger.info(f"Received {answer}")

            data: dict = json.loads(answer)

            for id_string, payload in data.items():
                try:
                    future = self.expected_receive[id_string]
                except KeyError as e:
                    logger.error(
                        f"Task {id_string} was not found. "
                        f"All expected are {self.expected_receive.keys()}",
                        exc_info=e,
                    )
                    continue

                logger.debug(
                    f"Setting future for {id_string} "
                    f"as done with result {payload}"
                )
                try:
                    future.set_result(payload)
                except InvalidStateError:
                    logger.exception(
                        msg=f"Since no one is waiting skipped: {answer}.",
                        exc_info=True,
                    )
                    continue

    def growth_rate(
        self,
        growth_percent: GrowthPercent,
        callback: Callable[[Plant], None],
    ):
        task = self.__request_growth_rate(growth_percent=growth_percent)

        assert self.loop is not None
        future_received = self.loop.create_future()

        self.expected_receive["growth_rate"] = future_received

        assert self.loop is not None
        asyncio.run_coroutine_threadsafe(task, self.loop)

        task = self.__receive_growth_rate(
            future=future_received, callback=callback
        )

        assert self.loop is not None
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
        message_dict = {
            "growth_rate": {"GrowthPercent": growth_percent.to_dict()}
        }

        logger.info(
            f"Sending Request for growth rates. Payload is : {message_dict}"
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
        task = self.__close_stomata()
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __close_stomata(self):
        logger.debug("Sending request for close_stomata")

        message = '{"close_stomata": "null"}'

        await self.websocket.send(message)

    def create_leaf(self, leaf: Leaf):
        assert self.loop is not None
        future = asyncio.run_coroutine_threadsafe(
            self.__create_leaf(leaf=leaf), self.loop
        )
        result = future.result()
        return result

    async def __create_leaf(self, leaf: Leaf):
        logger.debug("Request for the creation of a new leaf.")

        message = json.dumps({"create_leaf": leaf.to_dict()})
        await self.websocket.send(message)

    def get_environment(self, callback: Callable[[Environment], None]):
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: A WaterPool object.
        """

        assert self.loop is not None
        future_received = self.loop.create_future()

        self.expected_receive["get_environment"] = future_received

        task = self.__get_environment(
            future=future_received, callback=callback
        )

        assert self.loop is not None
        asyncio.run_coroutine_threadsafe(task, self.loop)

    async def __get_environment(
        self, future: Future, callback: Callable[[Environment], None]
    ):
        logger.debug("Sending request for environment")

        message = '{"get_environment": "null"}'

        await self.websocket.send(message)

        await future
        payload = future.result()
        logger.debug(
            f"Received following as answer for environment request: {payload}"
        )

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
        The method allows access to both grids on the server.
        It thus enables the use of add2grid of the MetaboliteGrid
        objects of the server-side environment.

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

        assert self.loop is not None
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
        assert self.loop is not None
        future_received = self.loop.create_future()
        self.expected_receive["load_level"] = future_received

        await self.websocket.send('{"load_level": "null"}')

        await future_received
        lock.release()

    def flush(self, timeout: Optional[float] = 0.015):
        """
        Method to force the execution of scheduled tasks.
        For this purpose, the calling thread is blocked
        until the specified timeout has been reached
        or until all tasks have been processed.

        Note:
            Setting the timeout parameters to None can lead to a deadlock
            if a task cannot be processed. This can happen for example
            if a response that is expected does not reach the client.

        Args:
            timeout (Optional[float]): The timeout time. If it is set to None,
             the thread is blocked until all tasks have been processed.

        """

        task = self.__flush(timeout=timeout)
        assert self.loop is not None
        asyncio.run_coroutine_threadsafe(task, self.loop)

        logger.debug(
            f"Forcing the execution of pending tasks."
            f" The calling thread will be blocked for the"
            f" next {timeout} seconds."
        )
        self.flush_lock.acquire()

    async def __flush(self, timeout: Optional[float] = 0.015):
        try:
            if timeout is not None:
                async with asyncio.timeout(timeout):
                    while len(asyncio.all_tasks(self.loop)) > 6:
                        await asyncio.sleep(0)
            else:
                while len(asyncio.all_tasks(self.loop)) > 6:
                    await asyncio.sleep(0)

        except TimeoutError:
            logger.warning(
                "Could not successfully execute all tasks until the timeout"
                f" ({timeout}) was reached. Calling thread will be released."
            )

        self.flush_lock.release()
