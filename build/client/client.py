#!/usr/bin/env python

# WS client example

import asyncio
import json
import logging

import websockets

from client.growth_percentage import GrowthPercent
from client.growth_rates import GrowthRates


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
        logging.info(f"Connected to localhost")

    async def __connect(self):
        self.websocket = await websockets.connect(self.url)

    def growth(self):
        return self.loop.run_until_complete(self.__growth())

    async def __growth(self):
        await self.websocket.send("{\"event\": \"GROWTH\"}")
        logging.info(f"Send event GROWTH")

        data = await self.websocket.recv()
        logging.info(f"Received {data}")

        return data

    def growth_rate(self, data: GrowthPercent) -> GrowthRates:
        return self.loop.run_until_complete(self.__growth_rate(data = data))

    async def __growth_rate(self, data: GrowthPercent) -> GrowthRates:

        if data.starch < 0:
            data.starch = 0

        message = {"event": "growth_rate"}
        message["data"] = data.to_json()

        logging.info("Sending Request for growth rates."
                     f"Payload is :\n"
                     f"{message}")

        await self.websocket.send(json.dumps(message))
        logging.info(f"Send event growth_rate")

        data = await self.websocket.recv()
        logging.info(f"Received {data}")
        data = GrowthRates.from_json(data)

        return data
