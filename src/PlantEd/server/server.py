#!/usr/bin/env python

import asyncio
import json
import logging
import threading

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.client.water import Water
from PlantEd.fba.dynamic_model import DynamicModel
from PlantEd.server.plant.leaf import Leaf

logger = logging.getLogger(__name__)


class Server:
    """
    A server that provides all necessary data for the user interface.
    """

    def __init__(self, model: DynamicModel):
        self.clients = set()
        self.websocket: websockets.WebSocketServer = None
        self.model: DynamicModel = model
        self.__future: asyncio.Future = None
        self.loop: asyncio.AbstractEventLoop = None

        thread = threading.Thread(
            target=asyncio.run, daemon=True, args=(self.__start(),)
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
        """
        Internal function that stops the websocket by assigning a result
        to the future object.

        """
        self.__future.set_result("")

    async def __start(self):
        """
        Internal function that creates the loop of the object, creates
        a future object that is used as a stop signal and starts the websocket.

        """
        self.loop = asyncio.get_running_loop()
        self.__future = self.loop.create_future()

        async with websockets.serve(
            self.main_handler,
            "localhost",
            4000,
            ping_interval=10,
            ping_timeout=30,
        ) as websocket:
            self.websocket = websocket
            await self.__future

    def open_connection(self, ws: WebSocketServerProtocol):
        """
        Function that registers a client.

        Args:
            ws: WebsocketServerProtocol, the new connection.

        """

        self.clients.add(ws)
        logger.info(f"{ws.remote_address} connected.")

    def close_connection(self, ws: WebSocketServerProtocol):
        """
        Function that logs off a client.

        Args:
            ws: WebsocketServerProtocol object, of the connection to be closed.

        Returns:

        """
        self.clients.remove(ws)
        logger.info(f"{ws.remote_address} disconnected.")

    def get_growth_percent(self) -> str:
        """
        Function that queries the server-side growth_percent.

        Returns: A GrowthPercent object encoded in JSON.

        """

        message = self.model.percentages.to_json()
        logger.info(f"Sending {message}")
        return message

    def calc_send_growth_rate(self, growth_percent: GrowthPercent) -> str:
        """
        Function that calculates the grams per specified time step.

        Args:
            growth_percent: A GrowthPercent object that determines the
                distribution of starch within the plant.

        Returns: Returns a GrowthRates object encoded in JSON that describes
            the grams in the specified time period.
        """

        logger.info(f"Calculating growth rates from {growth_percent}")

        growth_rates = self.model.calc_growth_rate(growth_percent)

        logger.info(f"Calculated growth rates: \n {growth_rates}")
        message = growth_rates.to_json()

        # send growth_rates as json
        logger.info(f"Sending following answer for growth rates. \n {message}")

        return message

    def open_stomata(self):
        """
        Method to open the stomas of the dynamic model.
        """

        logger.info("Opening stomata")
        self.model.open_stomata()

    def close_stomata(self):
        """
        Method to open the stomas of the dynamic model.

        """
        logger.info("Closing stomata")
        self.model.close_stomata()

    def deactivate_starch_resource(self):
        """

        Methode to disable the use of the starch pool.

        """
        logger.info("Deactivating starch use")
        self.model.deactivate_starch_resource()

    def activate_starch_resource(self):
        """
        Methode to enable the use of the starch pool.

        """
        logger.info("Activating starch use")
        self.model.activate_starch_resource()

    def get_water_pool(self) -> str:
        """
        Method to obtain the WaterPool defined in the DynamicModel.

        Returns: The WaterPool object encoded in JSON.

        """
        logger.info("Creating Water Object and sending it back")

        water = Water(
            water_pool=self.model.water_pool,
            max_water_pool=self.model.maximum_water_pool,
        )

        answer = water.to_json()

        logger.debug(f"Responding to a water request with {answer}")

        return answer

    def get_nitrate_pool(self) -> str:
        """
        Method to retrieve the Nitrate Pool form the Plant defined inside the
            DynamicModel.

        Returns: Nitrate object as a string in JSON format.

        """

        nitrate = self.model.plant.nitrate
        answer = nitrate.to_json()

        return answer

    def create_leaf(self, leaf: Leaf):
        self.plant.create_leaf(leaf)

    async def main_handler(self, ws: WebSocketServerProtocol):
        """
        Method that accepts all requests to the server
        and passes them on to the responsible methods.
        """
        logger.debug(f"Connection from {ws.remote_address} established.")
        self.open_connection(ws)
        logger.debug(f"{ws.remote_address} registered as client")

        while True:
            try:
                request = await ws.recv()
            except websockets.ConnectionClosedOK:
                self.close_connection(ws)
                logger.debug(f"{ws.remote_address} unregistered.")
                break

            logger.info(f"Received {request}")

            commands: dict = json.loads(request)
            response = {}

            for command, payload in commands.items():
                match command:

                    case "growth_rate":
                        logger.debug(
                            "Received command identified as calculation "
                            "of growth_rates."
                        )

                        growth_percent = GrowthPercent.from_json(
                            payload["GrowthPercent"]
                        )

                        response["growth_rate"] = self.calc_send_growth_rate(
                            growth_percent=growth_percent
                        )
                    case "open_stomata":
                        logger.debug(
                            "Received command identified as open_stomata."
                        )

                        self.open_stomata()

                    case "close_stomata":
                        logger.debug(
                            "Received command identified as close_stomata."
                        )

                        self.close_stomata()

                    case "deactivate_starch_resource":
                        logger.debug(
                            "Received command identified as "
                            "deactivate_starch_resource."
                        )

                        self.deactivate_starch_resource()

                    case "activate_starch_resource":
                        logger.debug(
                            "Received command identified as "
                            "activate_starch_resource."
                        )

                        self.activate_starch_resource()

                    case "get_water_pool":
                        logger.debug(
                            "Received command identified as get_water_pool."
                        )

                        response["get_water_pool"] = self.get_water_pool()

                    case "increase_nitrate":
                        logger.debug(
                            "Received command identified as increase_nitrate."
                        )
                        self.model.increase_nitrate(amount=5000)

                    case "get_nitrate_pool":
                        logger.debug(
                            "Received command identified as get_nitrate_pool."
                        )

                        response["get_nitrate_pool"] = self.get_nitrate_pool()

                    case "create_leaf":
                        logger.debug(
                            "Received command identified as create_leaf."
                        )

                        leaf: Leaf = Leaf.from_json(payload["create_leaf"])

                        self.create_leaf(leaf=leaf)

                    case _:
                        logger.error(
                            f"Received command {command} could not "
                            f"be identified"
                        )

                        continue

            if response:
                response = json.dumps(response)
                await asyncio.wait(
                    [client.send(response) for client in self.clients]
                )
