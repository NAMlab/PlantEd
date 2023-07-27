#!/usr/bin/env python

import asyncio
import concurrent.futures
import json
import logging
import multiprocessing
import signal
import socket
from multiprocessing import Manager, Event
from typing import Optional

import websockets
from websockets.legacy.server import WebSocketServerProtocol, WebSocketServer

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.client.update import UpdateInfo
from PlantEd.client.water import Water
from PlantEd.fba.dynamic_model import DynamicModel
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.nitrate import Nitrate

logger = logging.getLogger(__name__)

class ServerContainer:
    def __init__(self, sock: Optional[socket.socket] = None, only_local=True):
        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: Manager = multiprocessing.Manager()
        self.__port: Optional[int] = self.manager.Value(Optional[int], None)
        self.__ip_address: Optional[str] = self.manager.Value(Optional[str], None)
        self.__ready: Event = multiprocessing.Event()

        process = multiprocessing.Process(
            target=start_server,
            kwargs={
                "shutdown_signal": self.shutdown_signal,
                "ready": self.__ready,
                "sock": sock,
                "only_local": only_local,
                "port": self.__port,
                "ip_adress": self.__ip_address,
            }
        )

        self.process = process

    @property
    def port(self):
        return self.__port.value

    @property
    def ip_address(self):
        return self.__ip_address.value

    def start(self):
        """
        Method to start the server.
        """

        logger.info("Starting the server.")
        self.process.start()

        # wait till server is up
        logger.info("Waiting for the server to be fully started.")
        self.__ready.wait()
        logger.info("Server is ready")

    def stop(self):
        """
        Method to shut down the local server.
        Does not need to run inside the same thread or process as the server.
        """
        self.shutdown_signal.set()

        self.process.join()
        logger.debug("Process closed")

def start_server(
        shutdown_signal: Event,
        ready: Event,
        sock: Optional[socket.socket] = None,
        only_local=True,
        port: Optional[int] = None,
        ip_adress: Optional[int] = None,
):

    server = Server(
        shutdown_signal = shutdown_signal,
        ready= ready,
        sock= sock,
        only_local= only_local,
        port = port,
        ip_adress= ip_adress,
    )
    server.start()


class Server:
    """
    A server that provides all necessary data for the user interface.
    """

    def __init__(
            self,
            shutdown_signal: Event,
            ready: Event,
            sock: Optional[socket.socket] = None,
            only_local = True,
            port: Optional[int] = None,
            ip_adress: Optional[int] = None,
    ):
        self.shutdown_signal: Event = shutdown_signal
        self.ready: Event = ready
        self.clients = set()
        self.sock: Optional[socket.socket] = sock
        self.websocket: websockets.WebSocketServer = None
        self.environment : Environment = Environment()
        self.model: DynamicModel = DynamicModel(
            enviroment= self.environment,
        )

        self.__future: asyncio.Future = None
        self.loop: asyncio.AbstractEventLoop = None
        self.only_local = only_local

        self.__port: Optional[int] = port
        self.__ip_address: Optional[str] = ip_adress


    @property
    def port(self):
        return self.__port.value

    @property
    def ip_address(self):
        return self.__ip_address.value

    def start(self):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError as e:
            if "There is no current event loop in thread" in str(e):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        try:
            signal.signal(signal.SIGINT, lambda *args: self.shutdown_signal.set)
            signal.signal(signal.SIGTERM, lambda *args: self.shutdown_signal.set)
        except ValueError as e:
            if "signal only works in main thread of the main interpreter" == str(e):
                pass
            else:
                raise e

        loop.run_until_complete(self.__start_loop())

    async def __start_loop(self):
        """
        Internal function that creates the loop of the object, creates
        a future object that is used as a stop signal and starts the websocket.

        """
        self.loop = asyncio.get_running_loop()
        self.__future = self.loop.create_future()
        sock = self.sock

        if sock is None:

            if self.only_local is True:
                addr = ("localhost", 0)
            else:
                addr = ("", 0)

            if socket.has_dualstack_ipv6():
                sock: socket.socket = socket.create_server(addr, family=socket.AF_INET6, dualstack_ipv6=True)
            else:
                sock: socket.socket = socket.create_server(addr)

            self.sock = sock

        websocket: WebSocketServer

        async with websockets.serve(
            self.main_handler,
            sock = sock,
            ping_interval=10,
            ping_timeout=30,
        ) as websocket:
            self.websocket = websocket
            sock_name = sock.getsockname()

            self.__ip_address.value = sock_name[0]
            self.__port.value = sock_name[1]

            executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=1,
            )
            self.ready.set()
            await self.loop.run_in_executor(executor= executor, func = self.shutdown_signal.wait)

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

        """
        self.clients.remove(ws)
        logger.info(f"{ws.remote_address} disconnected.")

    def get_growth_percent(self) -> str:
        """
        Function that queries the server-side growth_percent.

        # ToDo needs to be the plant object complete
        Returns: A GrowthPercent object encoded in JSON.

        """

        message = self.model.percentages.to_json()
        logger.info(f"Sending {message}")
        return message

    def calc_send_growth_rate(self, growth_percent: GrowthPercent) -> str:
        """
        Function that calculates the growth per specified time step.

        Args:
            growth_percent: A GrowthPercent object that determines the
                distribution of starch within the plant.

        Returns: Returns a Plant object encoded in JSON.
        """

        logger.info(f"Calculating growth rates from {growth_percent}")

        if growth_percent.time_frame == 0:
            logger.debug("The passed TimeFrame is 0. Returning plant objects without simulation.")
            return self.model.plant.to_json()

        self.model.calc_growth_rate(new_growth_percentages= growth_percent, environment= self.environment)
        logger.info(f"Calculated growth rates: {self.model.growth_rates}")

        message = self.model.plant.to_json()

        # send growth_rates as json
        logger.info(f"Sending following answer for growth rates : {message}")

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

        water: Water = self.model.plant.water

        answer = water.to_json()

        logger.debug(f"Responding to a water request with {answer}")

        return answer

    def get_nitrate_pool(self) -> str:
        """
        Method to retrieve the Nitrate Pool form the Plant defined inside the
            DynamicModel.

        Returns: Nitrate object as a string in JSON format.

        """

        nitrate: Nitrate = self.model.plant.nitrate
        answer = nitrate.to_json()

        return answer

    def create_leaf(self, leaf: Leaf):
        self.model.plant.create_leaf(leaf)

    def stop_water_intake(self):
        self.model.stop_water_intake()

    def enable_water_intake(self):
        self.model.enable_water_intake()

    def set_water_pool(self, water: Water):
        water.transpiration = self.model.plant.water.transpiration

        self.model.plant.set_water(water)
        logger.debug(f"Water set to {self.model.plant.water}")



    def update(self, update_info: UpdateInfo):
        self.model.update(update_info=update_info)

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
                try:
                    match command:
                        case "growth_rate":
                            # ToDo ensure doing this as last step

                            logger.debug(
                                "Received command identified as calculation "
                                "of growth_rates."
                            )

                            growth_percent = GrowthPercent.from_json(
                                payload["GrowthPercent"]
                            )

                            response[
                                "growth_rate"
                            ] = self.calc_send_growth_rate(
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
                            amount = payload["increase_nitrate"]

                            self.model.increase_nitrate(amount=amount)

                        case "get_nitrate_pool":
                            logger.debug(
                                "Received command identified as get_nitrate_pool."
                            )

                            response[
                                "get_nitrate_pool"
                            ] = self.get_nitrate_pool()

                        case "create_leaf":
                            logger.debug(
                                "Received command identified as create_leaf."
                            )

                            leaf: Leaf = Leaf.from_json(payload["create_leaf"])

                            self.create_leaf(leaf=leaf)

                        case "stop_water_intake":
                            logger.debug(
                                "Received command identified as stop_water_intake."
                            )

                            self.stop_water_intake()

                        case "enable_water_intake":
                            logger.debug(
                                "Received command identified as enable_water_intake."
                            )

                            self.enable_water_intake()

                        case "set_water_pool":
                            logger.debug(
                                "Received command identified as set_water_pool."
                            )

                            water = Water.from_json(payload)

                            self.set_water_pool(water=water)

                        case "update":
                            logger.debug(
                                "Received command identified as update."
                            )

                            update_info = UpdateInfo.from_json(payload)

                            self.update(update_info=update_info)

                        case _:
                            logger.error(
                                f"Received command {command} could not "
                                f"be identified"
                            )

                            continue
                # ToDo change exception type
                except Exception:
                    logger.error(
                        msg=f"Unable to handle {command}, "
                        f"with payload {payload}",
                        exc_info=True,
                    )

            if response:
                response = json.dumps(response)
                await asyncio.gather(
                    *[client.send(response) for client in self.clients]
                )
