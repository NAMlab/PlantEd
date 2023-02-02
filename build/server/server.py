#!/usr/bin/env python

import asyncio
import json
import logging

import websockets
from websockets.legacy.server import WebSocketServerProtocol


class Server:
    """
    A server that provides all necessary data for the user interface.
    """
    def __init__(self):
        self.clients = set()
        self.websocket = None
        self.plant = None

    def start(self, plant):
        """
        Method to start the server.
        """
        self.plant = plant
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
        logging.info(f"{ws.remote_address} connected.")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnected.")

    async def send_growth(self, ws: WebSocketServerProtocol):

        message = json.dumps({
            "leaf_percent": self.plant.organs[0].percentage,
            "stem_percent": self.plant.organs[1].percentage,
            "root_percent": self.plant.organs[2].percentage,
            "starch_percent": self.plant.organ_starch.percentage,
        })
        logging.info(f"Sending {message}")
        await asyncio.wait([client.send(message) for client in self.clients])

    async def main_handler(self, ws: WebSocketServerProtocol):
        """
        Method that accepts all requests to the server
        and passes them on to the responsible methods.
        """
        logging.info("Handler ready.")
        await self.register(ws)
        try:
            while True:
                request = await ws.recv()
                logging.info(f"Received {request}")
                if json.loads(request) == {"event": "GROWTH"}:
                    await self.send_growth(ws)

        finally:
            await self.unregister(ws)
