import logging
import threading
import time
import unittest
from unittest import TestCase

import websockets

from PlantEd.fba.dynamic_model import DynamicModel
from PlantEd.server.server import Server, ServerContainer
from PlantEd.utils.gametime import GameTime

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

class TestServer(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        if self._testMethodName == "test_start":
            return

        self.server = ServerContainer(only_local= True)

        self.server.start()

        self.port = self.server.port

    def tearDown(self):

        if self._testMethodName != "test_start":
            self.server.stop()

    def test_start(self):
        logger.info("Run tests for the creation and start of the server.")

        server: ServerContainer = ServerContainer()

        logger.debug("Server successfully created.")

        self.assertIsInstance(server, ServerContainer)

        logger.debug("Starting the server.")

        server.start()

        logger.debug("Server started")

        server.stop()

    async def test_connect(self):
        self.fail()

    def test_send_growth(self):
        self.fail()

    def test_calc_send_growth_rate(self):
        self.fail()

    async def test_open_stomata(self):
        self.fail()

    async def test_close_stomata(self):
        self.fail()

    async def test_deactivate_starch_resource(self):
        self.fail()

    async def test_activate_starch_resource(self):
        self.fail()

    async def test_get_water_pool(self):
        self.fail()

    async def test_get_nitrate_pool(self):
        self.fail()

    def test_main_handler(self):
        self.fail()
