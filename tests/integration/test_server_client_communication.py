import json
import multiprocessing
import time
import unittest
from multiprocessing import Process
import websockets

from PlantEd.server import server


class TestServerClientCommunication(unittest.TestCase):
    def test_server_client_interaction(self):
        # Test server-client interaction
        pass


class TestGameStateStructure(unittest.TestCase):
    def setUp(self):
        # start server
        # server.start()
        # request loadlevel
        self.load_level_structure_request = {
            "type": "load_level",
            "message": {
                "player_name": "player_name",
                "icon_name": "icon_name",
                "level_name": "summer_low_nitrate",
                }
            }
        self.load_level_structure_response = {
            "level loaded": str  # has to be == level_name
            }

        # request simulate
        # Define the expected structure of the game state dictionary
        self.simulation_step_structure_request = {
            "type": str,
            "message": {
                "delta_t": float,
                "growth_percentages": {
                    "leaf_percent": float,
                    "stem_percent": float,
                    "root_percent": float,
                    "seed_percent": int,
                    "starch_percent": float,
                    "stomata": bool,
                    },
                "shop_actions": {
                    "buy_watering_can": dict,
                    "buy_nitrate": dict,
                    "buy_leaf": int,
                    "buy_branch": int,
                    "buy_root": int,
                    "buy_seed": int,
                    }
                }
            }
        self.simulation_step_structure_response = {
            "running": bool,
            "plant": {
                "leafs_biomass": list[int, float],
                "stems_biomass": list[int, float],
                "roots_biomass": float,
                "seeds_biomass": list[int, float],
                "starch_pool": float,
                "max_starch_pool": float,
                "root": {
                    "root_grid": list,
                    "water_grid_pos": tuple[float, float],
                    "positions": list[tuple[float, float]],
                    "directions": list[tuple[float, float]],
                    "root_classes": list[list[dict]],
                    "first_letters": list[dict]
                    },
                "water_pool": float,
                "max_water_pool": float,
                "open_spots": int,
                },
            "environment": {
                "time": float,
                "temperature": float,
                "humidity": float,
                "precipitation": float,
                "nitrate_grid": list,
                "water_grid": list,
                "sun_intensity": float
                # "water_grid_size": self.water_grid.grid_size,
                },
            "green_thumbs": int,
            "used_fluxes": dict,
            "nitrate_available": float,
            "gametime": float
            }


class TestAsyncServerResponse(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Start the server in the background

        multiprocessing.freeze_support()
        multiprocessing.set_start_method('spawn')
        self.server_process = Process(target=server.start)
        self.server_process.start()
        time.sleep(1)

    async def asyncTearDown(self):
        # Stop the server after the test
        self.server_process.terminate()
        self.server_process.join()

    async def test_load_server_response_structure(self):
        async with websockets.connect('ws://localhost:8765') as websocket:
            # Send a request to the server
            request = {
                "type": "load_level",
                "message": {
                    "player_name": "player_name",
                    "icon_name": "icon_name",
                    "level_name": "summer_low_nitrate",
                    }
                }
            await websocket.send(json.dumps(request))

            # Receive the response from the server
            response_json = await websocket.recv()
            response = json.loads(response_json)

            # Define the expected structure of the response
            expected_structure = {
                "level loaded": str  # has to be == level_name
                }
            # Assert that the response structure matches the expected structure
            self.assertDictStructure(expected_structure, response)

    def assertDictStructure(self, expected_structure, dictionary):
        # Helper method to recursively validate the structure of a dictionary
        for key, value in expected_structure.items():
            self.assertIn(key, dictionary)
            if isinstance(value, dict):
                self.assertIsInstance(dictionary[key], dict)
                self.assertDictStructure(value, dictionary[key])
            else:
                self.assertIsInstance(dictionary[key], value)




if __name__ == '__main__':
    unittest.main()
