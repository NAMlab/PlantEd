import logging
import multiprocessing
import threading
import time
from multiprocessing.managers import ValueProxy, SyncManager
from multiprocessing.synchronize import Event
from typing import Optional
from unittest import TestCase, skip
from unittest.mock import patch, MagicMock, call

from websockets.legacy.server import WebSocketServerProtocol

from PlantEd.client.client import Client
from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.server import Server

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class TestServer(TestCase):
    def setUp(self) -> None:
        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: SyncManager = multiprocessing.Manager()
        port: ValueProxy[Optional[int]] = self.manager.Value(
            Optional[int], None
        )
        ip_address: ValueProxy[Optional[str]] = self.manager.Value(
            Optional[str], None
        )
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
        self.assertNotEquals(self.server.ip_address, "")

    def test_open_connection(self):
        client = Client(port=self.server.port)
        time.sleep(1)

        self.assertEqual(1, len(self.server.clients))

        thing = self.server.clients.pop()  # remove single client
        self.server.clients.add(thing)  # add it back
        self.assertIsInstance(thing, WebSocketServerProtocol)

        client_2 = Client(port=self.server.port)
        self.assertIsInstance(client_2, Client)
        time.sleep(1)

        self.assertEqual(2, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

    def test_close_connection(self):
        client_1 = Client(port=self.server.port)
        client_2 = Client(port=self.server.port)
        time.sleep(1)

        self.assertEqual(2, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

        client_1.stop()
        time.sleep(1)

        self.assertEqual(1, len(self.server.clients))
        for client in self.server.clients:
            self.assertIsInstance(client, WebSocketServerProtocol)

        client_2.stop()
        time.sleep(1)

        self.assertEqual(0, len(self.server.clients))

    @patch("PlantEd.server.environment.environment.Environment.simulate")
    @patch("PlantEd.server.fba.dynamic_model.DynamicModel.calc_growth_rate")
    def test_calc_send_growth_rate(
        self, calc_growth_rate: MagicMock, simulate: MagicMock
    ):
        growth_percent = GrowthPercent(
            leaf=0.1,
            stem=0.3,
            root=0.2,
            starch=0.1,
            flower=0.3,
            time_frame=400,
        )

        result = self.server.calc_send_growth_rate(growth_percent)

        self.assertEqual(1, simulate.call_count)
        self.assertEqual(
            call(time_in_s=growth_percent.time_frame), simulate.call_args
        )

        self.assertEqual(1, calc_growth_rate.call_count)
        self.assertEqual(
            call(
                new_growth_percentages=growth_percent,
                environment=self.server.environment,
            ),
            calc_growth_rate.call_args,
        )

        self.assertIsInstance(result, str)
        self.assertEqual(result, self.server.model.plant.to_json())

    @patch("PlantEd.server.fba.dynamic_model.DynamicModel.open_stomata")
    def test_open_stomata(self, open_stomata: MagicMock):
        self.server.open_stomata()
        self.assertEqual(1, open_stomata.call_count)
        self.assertEqual((), open_stomata.call_args)

    @patch("PlantEd.server.fba.dynamic_model.DynamicModel.close_stomata")
    def test_close_stomata(self, close_stomata: MagicMock):
        self.server.close_stomata()
        self.assertEqual(1, close_stomata.call_count)
        self.assertEqual((), close_stomata.call_args)

    def test_create_leaf(self):
        self.assertEqual(1, len(self.server.model.plant.leafs.leafs))
        self.assertEqual(self.server.model.plant.leafs.biomass, 0.1)
        self.assertEqual(self.server.model.plant.leafs.addable_leaf_biomass, 0)

        leaf = Leaf(mass=1, max_mass=2)
        self.server.create_leaf(leaf=leaf)

        self.assertEqual(2, len(self.server.model.plant.leafs.leafs))
        self.assertEqual(self.server.model.plant.leafs.biomass, 1.1)
        self.assertEqual(self.server.model.plant.leafs.addable_leaf_biomass, 1)

    def test_get_environment(self):
        env = self.server.get_environment()

        self.assertIsInstance(env, str)
        self.assertEqual(self.server.environment.to_json(), env)

    @patch("PlantEd.utils.LSystem.LSystem.create_new_first_letter")
    def test_create_new_first_letter(self, create_new_first_letter):
        # Only correct passing to LSystem is checked.

        self.server.create_new_first_letter(
            dir=5,
            pos=5,
            mass=50,
            dist=10,
        )

        create_new_first_letter.assert_called_with(
            dir=5, pos=5, mass=50, dist=10
        )

    def test_add2grid(self):
        dic: dict = {}
        dic["amount"] = 50
        dic["x"] = 1
        dic["y"] = 3
        dic["grid"] = "nitrate"

        # Nitrate add 50
        self.assertEqual(10, self.server.environment.nitrate_grid.grid[1, 3])

        self.server.add2grid(payload=dic)
        self.assertEqual(60, self.server.environment.nitrate_grid.grid[1, 3])

        # Water add 7
        dic["grid"] = "water"
        dic["amount"] = 7
        dic["x"] = 8
        dic["y"] = 5

        self.assertEqual(50000, self.server.environment.water_grid.grid[8, 5])

        self.server.add2grid(payload=dic)
        self.assertEqual(50007, self.server.environment.water_grid.grid[8, 5])

    @skip("The method of testing has yet to be defined.")
    def test_main_handler(self):
        self.fail()
