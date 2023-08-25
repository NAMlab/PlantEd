from unittest import TestCase

from PlantEd.client.SimWeatherSmall import WeatherSimulatorMinimal
from PlantEd.server.environment.weather_state import WeatherState


class TestWeatherSimulatorMinimal(TestCase):
    def test_create(self):
        w_sim = WeatherSimulatorMinimal()
        self.assertIsInstance(w_sim, WeatherSimulatorMinimal)
        self.assertEqual(w_sim.state, {})
        self.assertEqual(w_sim.latest_hour, 0)

    def test_get_weather_state(self):
        w_sim = WeatherSimulatorMinimal()

        with self.assertRaises(KeyError):
            w_sim.get_weather_state(5)

        weather_state = WeatherState(
            temperature= 20,
            humidity= 30,
            precipitation= 176,
        )
        w_sim.state = {5: weather_state}

        self.assertEqual(w_sim.get_weather_state(5), weather_state)

    def test_get_latest_weather_state(self):
        w_sim = WeatherSimulatorMinimal()

        with self.assertRaises(KeyError):
            w_sim.get_latest_weather_state()

        weather_state = WeatherState(
            temperature=20,
            humidity=30,
            precipitation=176,
        )
        w_sim.state[0] = weather_state

        self.assertEqual(w_sim.get_latest_weather_state(), weather_state)

        weather_state = WeatherState(
            temperature=8,
            humidity=17,
            precipitation=348,
        )
        w_sim.state[1] = weather_state
        w_sim.latest_hour = 1

        self.assertEqual(w_sim.get_latest_weather_state(), weather_state)

    def test_to_dict(self):
        w_sim = WeatherSimulatorMinimal()

        weather_state = WeatherState(
            temperature=20,
            humidity=30,
            precipitation=176,
        )
        w_sim.state = {0: weather_state}

        weather_state = WeatherState(
            temperature=8,
            humidity=17,
            precipitation=348,
        )
        w_sim.state[1] = weather_state
        w_sim.latest_hour = 1

        dic = w_sim.to_dict()
        expected = {'states': {0: {'temperature': 20, 'humidity': 30, 'precipitation': 176}, 1: {'temperature': 8, 'humidity': 17, 'precipitation': 348}}, 'latest_hour': 1}

        self.assertEqual(dic, expected)

    def test_from_dict(self):
        w_sim = WeatherSimulatorMinimal()

        weather_state = WeatherState(
            temperature=20,
            humidity=30,
            precipitation=176,
        )
        w_sim.state = {0: weather_state}

        weather_state = WeatherState(
            temperature=8,
            humidity=17,
            precipitation=348,
        )
        w_sim.state[1] = weather_state
        w_sim.latest_hour = 1

        dic = w_sim.to_dict()
        restored = WeatherSimulatorMinimal.from_dict(dic)

        self.assertEqual(w_sim, restored)
