import logging
import multiprocessing
import os
import threading
import time
import unittest
from multiprocessing.managers import ValueProxy, SyncManager
from multiprocessing.synchronize import Event
from typing import Optional
from unittest import TestCase, skipIf
from unittest.mock import patch, PropertyMock

from PlantEd.client.client import Client
from PlantEd.client.growth_percentage import GrowthPercent
from PlantEd.constants import (
    START_LEAF_BIOMASS_GRAM,
    MAXIMUM_LEAF_BIOMASS_GRAM,
)
from PlantEd.server.fba.dynamic_model import DynamicModel
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.leaf import Leaf
from PlantEd.server.plant.plant import Plant
from PlantEd.server.server import Server

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)

# check if we are running on GitHub
IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"


class TestClient(TestCase):
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

        with patch.object(
            Leaf, "_Leaf__max_id", new_callable=PropertyMock
        ) as mock:
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

    def test_create(self):
        client: Client = Client(port=self.server.port)
        self.assertIsInstance(client, Client)

    def test_growth_rate(self):
        client: Client = Client(port=self.server.port)
        success: bool = False

        def call(plant: Plant):
            nonlocal success
            success = True
            self.assertIsInstance(plant, Plant)
            logging.debug(f"Test Result is {plant}")

        growth: GrowthPercent = GrowthPercent(
            leaf=0.2,
            stem=0.4,
            root=0.2,
            starch=0.1,
            flower=0.1,
            time_frame=60,
        )

        client.growth_rate(growth_percent=growth, callback=call)
        time.sleep(1)
        self.assertTrue(success)

    def test_open_stomata(self):
        client: Client = Client(port=self.server.port)

        self.assertFalse(self.server.model.plant.stomata_open)

        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")

        self.assertEqual(
            -1000,
            reaction.lower_bound,
        )
        self.assertEqual(
            0,
            reaction.upper_bound,
        )

        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")
        reaction.bounds = (0, 0)

        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")
        self.assertEqual(
            0,
            reaction.lower_bound,
        )
        self.assertEqual(
            0,
            reaction.upper_bound,
        )

        client.open_stomata()
        time.sleep(1)
        self.assertTrue(self.server.model.plant.stomata_open)
        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")

        self.assertEqual(
            -1000,
            reaction.lower_bound,
        )
        self.assertEqual(
            1000,
            reaction.upper_bound,
        )

    def test_close_stomata(self):
        client: Client = Client(port=self.server.port)

        self.server.model.plant.stomata_open = True
        self.assertTrue(self.server.model.plant.stomata_open)

        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")
        reaction.bounds = (0, 1000)
        self.assertEqual(
            0,
            reaction.lower_bound,
        )
        self.assertEqual(
            1000,
            reaction.upper_bound,
        )

        client.close_stomata()
        time.sleep(1)
        self.assertFalse(self.server.model.plant.stomata_open)
        reaction = self.server.model.model.reactions.get_by_id("CO2_tx_leaf")

        self.assertEqual(
            -1000,
            reaction.lower_bound,
        )
        self.assertEqual(
            0,
            reaction.upper_bound,
        )

    def test_load_level(self):
        client = Client(port=self.server.port)

        self.server.environment = "An edited environment"
        self.server.model = "An edited Model"

        client.load_level()

        self.assertIsInstance(self.server.environment, Environment)
        self.assertIsInstance(self.server.model, DynamicModel)

    def test_create_leaf(self):
        client = Client(port=self.server.port)

        leafs = self.server.model.plant.leafs

        default_leaf = Leaf.from_dict(
            {
                "id": 1,
                "mass": START_LEAF_BIOMASS_GRAM,
                "max_mass": MAXIMUM_LEAF_BIOMASS_GRAM,
            }
        )
        self.assertEqual({default_leaf}, leafs.leafs)

        leaf = Leaf(mass=5, max_mass=13)
        client.create_leaf(leaf=leaf)

        time.sleep(1)
        self.assertEqual({leaf, default_leaf}, leafs.leafs)

        leaf_2 = Leaf(mass=27, max_mass=100)
        client.create_leaf(leaf=leaf_2)

        time.sleep(1)
        self.assertEqual({leaf, default_leaf, leaf_2}, leafs.leafs)

    def test_short_time(self):
        # Requests one simulation per second for 30 minutes

        client = Client(port=self.server.port)
        success: bool
        times_run = 0

        def call(plant: Plant):
            nonlocal success
            nonlocal times_run
            success = True
            self.assertIsInstance(plant, Plant)
            logging.debug(f"Test Result is {plant}")
            times_run = times_run + 1

        for _ in range(0, 30):
            success = False
            growth: GrowthPercent = GrowthPercent(
                leaf=0.2,
                stem=0.4,
                root=0.2,
                starch=0.1,
                flower=0.1,
                time_frame=60,
            )
            client.growth_rate(growth_percent=growth, callback=call)
            time.sleep(1)
            self.assertTrue(success)

        self.assertEqual(30, times_run)

    @unittest.skip("")
    @skipIf(
        IN_GITHUB_ACTIONS,
        reason="The test runs for 30 minutes "
        "and therefore consumes a lot of runtime.",
    )
    def test_long_time(self):
        # Requests one simulation per second for 30 minutes

        client = Client(port=self.server.port)
        success: bool
        times_run = 0

        def call(plant: Plant):
            nonlocal success
            nonlocal times_run
            success = True
            self.assertIsInstance(plant, Plant)
            logging.debug(f"Test Result is {plant}")
            times_run = times_run + 1

        for _ in range(0, 60 * 30):
            success = False
            growth: GrowthPercent = GrowthPercent(
                leaf=0.2,
                stem=0.4,
                root=0.2,
                starch=0.1,
                flower=0.1,
                time_frame=60,
            )
            client.growth_rate(growth_percent=growth, callback=call)
            time.sleep(1)
            self.assertTrue(success)

        self.assertEqual(times_run, 30 * 60)
