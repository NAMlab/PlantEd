import logging
import multiprocessing
import threading
import time
import unittest
from multiprocessing import Event, Manager
from typing import Optional
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

        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: Manager = multiprocessing.Manager()
        self.port: Optional[int] = self.manager.Value(Optional[int], None)
        self.ip_address: Optional[str] = self.manager.Value(Optional[str], None)
        self.ready: Event = multiprocessing.Event()

        self.server = Server(
            shutdown_signal=self.shutdown_signal,
            ready=self.ready,
            sock=None,
            only_local=True,
            port=self.port,
            ip_adress=self.ip_address,
        )

        self.thread = threading.Thread(target=self.server.start)
        self.thread.start()
        self.ready.wait()

    def tearDown(self):
        if self._testMethodName != "test_start":
            self.shutdown_signal.set()
            self.thread.join()

    async def test_connect(self):
        async with websockets.connect(f"ws://localhost:{self.port.value}") as _:
            msg = "Single connection results in multiple registered clients"
            self.assertEqual(1, len(self.server.clients), msg)

            # get single connection itself
            [connection] = self.server.clients
            host, port, *_ = connection.local_address

            self.assertEqual(self.port.value, port)
            self.assertIn(host, ["localhost", "127.0.0.1", "::1"])
            self.assertEqual(self.ip_address.value, host)

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
