import logging
import multiprocessing
import threading
import time
import unittest
from multiprocessing import Event, Manager
from typing import Optional
from unittest import TestCase

import websockets
from websockets.legacy.server import WebSocketServerProtocol

from PlantEd.client.client import Client
from PlantEd.fba.dynamic_model import DynamicModel
from PlantEd.server.server import Server, ServerContainer
from PlantEd.utils.gametime import GameTime

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class TestServer(TestCase):
    def setUp(self) -> None:
        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: Manager = multiprocessing.Manager()
        port: Optional[int] = self.manager.Value(Optional[int], None)
        ip_address: Optional[str] = self.manager.Value(Optional[str], None)
        self.ready: Event = multiprocessing.Event()
        
        self.server = Server(
            shutdown_signal=self.shutdown_signal,
            ready=self.ready,
            only_local=True,
            port=port,
            ip_adress=ip_address,
        )
        
        self.thread = threading.Thread(target=self.server.start)
        self.thread.start()
        self.ready.wait()

    def tearDown(self):
        self.shutdown_signal.set()
        self.thread.join()

    def test_start(self):
        # runs start due to setUp
        self.assertIsInstance(self.server, Server)

    def test_port(self):
        self.assertIsInstance(self.server.port, int)

    def test_ip_address(self):
        self.assertIsInstance(self.server.ip_address, str)
        self.assertNotEquals(self.server.ip_address,"")

    def test_open_connection(self):
        client = Client(port= self.server.port)

        self.assertEqual(1, len(self.server.clients))

        thing = self.server.clients.pop() # remove single client
        self.server.clients.add(thing) # add it back
        self.assertIsInstance(thing, WebSocketServerProtocol)

        client_2 = Client(port=self.server.port)

        self.assertEqual(2, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

    def test_close_connection(self):
        client_1 = Client(port= self.server.port)
        client_2 = Client(port=self.server.port)
        time.sleep(0)

        self.assertEqual(2, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

        client_1.stop()
        time.sleep(0)

        self.assertEqual(1, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

        client_2.stop()
        time.sleep(0)

        self.assertEqual(0, len(self.server.clients))

    def test_get_growth_percent(self):
        self.fail()

    def test_calc_send_growth_rate(self):
        self.fail()

    def test_open_stomata(self):
        self.fail()

    def test_close_stomata(self):
        self.fail()

    def test_deactivate_starch_resource(self):
        self.fail()

    def test_activate_starch_resource(self):
        self.fail()

    def test_get_water_pool(self):
        self.fail()

    def test_get_nitrate_pool(self):
        self.fail()

    def test_create_leaf(self):
        self.fail()

    def test_stop_water_intake(self):
        self.fail()

    def test_enable_water_intake(self):
        self.fail()

    def test_set_water_pool(self):
        self.fail()

    def test_update(self):
        self.fail()

    def test_get_environment(self):
        self.fail()

    def test_create_new_first_letter(self):
        self.fail()

    def test_add2grid(self):
        self.fail()

    def test_main_handler(self):
        self.fail()
