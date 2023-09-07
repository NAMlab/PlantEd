import logging
import multiprocessing
import threading
import time
from multiprocessing import Event, Manager
from typing import Optional
from unittest import TestCase
from unittest.mock import patch, PropertyMock

from PlantEd.client.client import Client
from PlantEd.constants import START_LEAF_BIOMASS_GRAM
from PlantEd.server.fba.dynamic_model import DynamicModel
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.server import Server

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)


class TestClient(TestCase):
    def setUp(self) -> None:
        self.shutdown_signal: Event = multiprocessing.Event()
        self.manager: Manager = multiprocessing.Manager()
        port: Optional[int] = self.manager.Value(Optional[int], None)
        ip_address: Optional[str] = self.manager.Value(Optional[str], None)
        self.ready: Event = multiprocessing.Event()

        with patch.object(Leaf, "_Leaf__max_id", new_callable=PropertyMock) as mock:
            mock.return_value = 1
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

    def test_growth(self):
        self.fail()

    def test_growth_rate(self):
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

    def test_load_level(self):
        client = Client(port=self.server.port)

        self.server.environment = "An edited environment"
        self.server.model = "An edited Model"

        client.load_level()

        self.assertIsInstance(self.server.environment, Environment)
        self.assertIsInstance(self.server.model, DynamicModel)

    def test_create_leaf(self):
        client = Client(port= self.server.port)

        leafs = self.server.model.plant.leafs

        default_leaf = Leaf.from_dict({'id': 1, 'mass': START_LEAF_BIOMASS_GRAM, 'max_mass': START_LEAF_BIOMASS_GRAM * 5})
        self.assertEqual({default_leaf}, leafs.leafs)

        leaf = Leaf(mass=5, max_mass= 13)
        client.create_leaf(leaf= leaf)

        time.sleep(0)
        self.assertEqual({leaf,default_leaf}, leafs.leafs)

        leaf_2 = Leaf(mass=27, max_mass=100)
        client.create_leaf(leaf=leaf_2)

        time.sleep(0)
        self.assertEqual({leaf, default_leaf, leaf_2}, leafs.leafs)
