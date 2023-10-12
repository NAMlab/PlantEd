#!/usr/bin/env python

import asyncio
import concurrent.futures
import json
import logging
import multiprocessing
import signal
import socket
from multiprocessing.managers import ValueProxy, SyncManager
from multiprocessing.synchronize import Event
from typing import Optional

import websockets
from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import WebSocketServerProtocol, WebSocketServer

from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.server.fba.dynamic_model import DynamicModel
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf

logger = logging.getLogger(__name__)


class ServerContainer:
    def __init__(self, sock: Optional[socket.socket] = None, only_local=True):
        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: SyncManager = multiprocessing.Manager()
        self.__port: ValueProxy[Optional[int]] = self.manager.Value(
            Optional[int], None
        )
        self.__ip_address: ValueProxy[Optional[str]] = self.manager.Value(
            Optional[str], None
        )
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
            },
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
    port: Optional[ValueProxy[int]] = None,
    ip_adress: Optional[ValueProxy[str]] = None,
):
    server = Server(
        shutdown_signal=shutdown_signal,
        ready=ready,
        sock=sock,
        only_local=only_local,
        port=port,
        ip_adress=ip_adress,
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
        only_local=True,
        port: Optional[ValueProxy[int]] = None,
        ip_adress: Optional[ValueProxy[str]] = None,
    ):
        self.shutdown_signal: Event = shutdown_signal
        self.ready: Event = ready
        self.clients: set[WebSocketServerProtocol] = set()
        self.sock: Optional[socket.socket] = sock
        self.websocket: Optional[WebSocketServer] = None
        self.environment: Environment = Environment()
        self.model: DynamicModel = DynamicModel(
            enviroment=self.environment,
        )

        self.__future: Optional[asyncio.Future] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.only_local = only_local

        self.__port: Optional[ValueProxy[int]] = port
        self.__ip_address: Optional[ValueProxy[str]] = ip_adress

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
            signal.signal(
                signal.SIGINT, lambda *args: self.shutdown_signal.set
            )
            signal.signal(
                signal.SIGTERM, lambda *args: self.shutdown_signal.set
            )
        except ValueError as e:
            if (
                "signal only works in main thread of the main interpreter"
                == str(e)
            ):
                pass
            else:
                raise e

        loop.run_until_complete(self.__start_loop())

    async def __load_level(self):
        self.environment: Environment = Environment()
        self.model: DynamicModel = DynamicModel(
            enviroment=self.environment,
        )

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
                sock: socket.socket = socket.create_server(
                    addr, family=socket.AF_INET6, dualstack_ipv6=True
                )
            else:
                sock: socket.socket = socket.create_server(addr)

            self.sock = sock

        websocket: WebSocketServer

        async with websockets.serve(
            self.main_handler,
            sock=sock,
            logger=logging.getLogger(__name__ + ".websocket"),
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
            await self.loop.run_in_executor(
                executor=executor, func=self.shutdown_signal.wait
            )

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
            logger.debug(
                "The passed TimeFrame is 0."
                " Returning plant objects without simulation."
            )
            return self.model.plant.to_json()

        self.environment.simulate(time_in_s=growth_percent.time_frame)

        self.model.calc_growth_rate(
            new_growth_percentages=growth_percent, environment=self.environment
        )
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

    def create_leaf(self, leaf: Leaf):
        self.model.plant.leafs.new_leaf(leaf)

    def get_environment(self) -> str:
        return self.environment.to_json()

    def create_new_first_letter(
        self,
        dir,
        pos,
        mass,
        dist,
    ):
        self.model.plant.root.create_new_first_letter(
            dir=dir,
            pos=pos,
            mass=mass,
            dist=dist,
        )

    def add2grid(self, payload):
        amount = payload["amount"]
        x = payload["x"]
        y = payload["y"]

        match payload["grid"]:
            case "nitrate":
                self.environment.nitrate_grid.add2cell(
                    rate=amount,
                    x=x,
                    y=y,
                )

            case "water":
                self.environment.water_grid.add2cell(
                    rate=amount,
                    x=x,
                    y=y,
                )

            case _:
                logger.error("Unknown grid")

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
            except ConnectionClosed as e:
                self.close_connection(ws)
                logger.debug(
                    f"{ws.remote_address} unregistered. Closing Trace: {e}"
                )
                break

            logger.info(f"Received {str(request)}")

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

                        case "create_leaf":
                            logger.debug(
                                f"Received command identified as create_leaf."
                                f" Payload: {payload}"
                            )

                            leaf: Leaf = Leaf.from_dict(payload)

                            self.create_leaf(leaf=leaf)

                        case "get_environment":
                            logger.debug(
                                "Received command identified as "
                                "get_environment."
                            )

                            response[
                                "get_environment"
                            ] = self.get_environment()

                        case "create_new_first_letter":
                            logger.debug(
                                "Received command identified as "
                                "create_new_first_letter."
                            )

                            self.create_new_first_letter(
                                dir=payload["dir"],
                                pos=payload["pos"],
                                mass=payload["mass"],
                                dist=payload["dist"],
                            )

                        case "add2grid":
                            logger.debug(
                                "Received command identified as add2grid."
                            )
                            self.add2grid(payload=payload)

                        case "load_level":
                            logger.debug(
                                "Received command identified as load_level."
                            )
                            await self.__load_level()
                            response["load_level"] = "None"

                        case _:
                            logger.error(
                                f"Received command {command} could not "
                                f"be identified"
                            )

                            continue
                # ToDo change exception type
                except Exception:
                    logger.exception(
                        msg=f"Unable to handle {command}, "
                        f"with payload {payload}",
                        exc_info=True,
                    )

            if response:
                response_str = json.dumps(response)
                await asyncio.gather(
                    *[client.send(response_str) for client in self.clients]
                )
