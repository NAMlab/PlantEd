import asyncio
import logging
import threading
import time
import unittest

import websockets

from fba.dynamic_model import DynamicModel
from server.server import Server

logging.basicConfig(
    level="DEBUG",
    format='%(asctime)s %(name)s %(levelname)s:%(message)s',
    datefmt='%H:%M:%S',
)

logger = logging.getLogger(__name__)


class TestServer(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.semaphore = threading.Lock()

    def setUp(self):

        self.semaphore.acquire()

        if self._testMethodName == "test_start":
            return

        model = DynamicModel(1)
        self.server = Server(model)

        self.server.start()

    def tearDown(self):
        if self._testMethodName != "test_start":
            self.server.stop()

        self.semaphore.release()

    def test_start(self):

        logger.info("Run test for the creation and start of the server.")

        model = DynamicModel(1)
        logger.debug("Dummy DynamicModell created.")

        server: Server = Server(model)

        logger.debug("Server successfully created.")

        self.assertIsInstance(server, Server)
        self.assertEqual(server.clients, set())
        self.assertEqual(server.websocket, None)
        self.assertEqual(server.model, model)

        logger.debug("Starting the server.")

        server.start()

        logger.debug("Server started")

        server.stop()

    async def test_connect(self):

        async with websockets.connect("ws://localhost:4000") as websocket:
            msg = "Single connection results in multiple registered clients"
            self.assertEqual(1, len(self.server.clients), msg)

            # get single connection itself
            [connection] = self.server.clients
            host, port, *_ = connection.local_address

            self.assertEqual(4000, port)
            self.assertIn(host, ["localhost", "127.0.0.1", "::1"])

    def test_unregister(self):
        self.fail()

    def test_send_growth(self):
        self.fail()

    def test_calc_send_growth_rate(self):
        self.fail()

    async def test_open_stomata(self):

        async with websockets.connect("ws://localhost:4000") as websocket:
            self.server.model.stomata_open = False
            CO2 = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")
            CO2.bounds = (0,0)

            self.assertEqual(False, self.server.model.stomata_open)
            self.assertEqual((0, 0), self.server.model.model.reactions.get_by_id("CO2_tx_leaf").bounds)


            msg = "{\"event\": \"open_stomata\"}"

            await websocket.send(msg)

            # server needs time to open stomata
            time.sleep(0.1)

            self.assertEqual(True, self.server.model.stomata_open)

            self.assertEqual((-1000, 1000), self.server.model.model.reactions.get_by_id("CO2_tx_leaf").bounds)

    async def test_close_stomata(self):

        async with websockets.connect("ws://localhost:4000") as websocket:
            self.server.model.stomata_open = True
            CO2 = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")
            CO2.bounds = (0, 1000)

            self.assertEqual(True, self.server.model.stomata_open)
            self.assertEqual((0, 1000), self.server.model.model.reactions.get_by_id("CO2_tx_leaf").bounds)

            msg = "{\"event\": \"close_stomata\"}"

            await websocket.send(msg)

            # server needs time to close stomata
            time.sleep(0.1)

            self.assertEqual(False, self.server.model.stomata_open)

            self.assertEqual((-1000, 0), self.server.model.model.reactions.get_by_id("CO2_tx_leaf").bounds)

    def test_deactivate_starch_resource(self):
        self.fail()

    def test_activate_starch_resource(self):
        self.fail()

    def test_get_water_pool(self):
        self.fail()

    def test_main_handler(self):
        self.fail()
