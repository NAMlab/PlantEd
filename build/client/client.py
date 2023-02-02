#!/usr/bin/env python

# WS client example

import asyncio
import json
import logging

import websockets


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
        await self.websocket.send(json.dumps({
            "event": "GROWTH"
        }))
        logging.info(f"Send event GROWTH")

        data = await self.websocket.recv()
        logging.info(f"Received {data}")

        return data

