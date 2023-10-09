from unittest import TestCase
from importlib import resources

import pandas as pd

from PlantEd import data
from PlantEd.client.SimWeatherSmall import WeatherSimulatorMinimal
from PlantEd.server.environment.weather import WeatherSimulator
from PlantEd.server.environment.weather_state import WeatherState


class TestWeatherSimulator(TestCase):
    def test_init(self):
        with resources.files(data) / "weather" as weather_data:
            df_weather_spring: pd.DataFrame = pd.read_csv(
                (weather_data / "cleaned_weather_spring.csv")
            )

        w_sim = WeatherSimulator(df_weather_spring)
        self.assertIsInstance(w_sim, WeatherSimulator)

    def test_simulate(self):
        with resources.files(data) / "weather" as weather_data:
            df_weather_spring: pd.DataFrame = pd.read_csv(
                (weather_data / "cleaned_weather_spring.csv")
            )

        w_sim = WeatherSimulator(df_weather_spring)

        w_sim.simulate(end_hour=3)
        expected_dict = {
            "states": {
                0: {
                    "temperature": 1.72,
                    "humidity": 61.0,
                    "precipitation": 0.0,
                },
                1: {
                    "temperature": 1.1563999999999997,
                    "humidity": 60.0,
                    "precipitation": 0.0,
                },
                2: {
                    "temperature": 1.1563999999999997,
                    "humidity": 64.0,
                    "precipitation": 0.0,
                },
                3: {
                    "temperature": 0.2740000000000009,
                    "humidity": 66.0,
                    "precipitation": 0.0,
                },
            },
            "latest_hour": 3,
        }
        expected = WeatherSimulatorMinimal.from_dict(expected_dict)

        self.assertEqual(expected, w_sim)

    def test_get_weather_state(self):
        with resources.files(data) / "weather" as weather_data:
            df_weather_spring: pd.DataFrame = pd.read_csv(
                (weather_data / "cleaned_weather_spring.csv")
            )

        w_sim = WeatherSimulator(df_weather_spring)

        state = w_sim.get_weather_state(0)
        expected_state = WeatherState(
            temperature=1.72, humidity=61, precipitation=0
        )
        self.assertEqual(expected_state, state)

        state = w_sim.get_weather_state(6)
        expected_state = WeatherState(
            temperature=2.0388, humidity=60, precipitation=0
        )
        self.assertEqual(expected_state, state)

    def test_get_latest_weather_state(self):
        with resources.files(data) / "weather" as weather_data:
            df_weather_spring: pd.DataFrame = pd.read_csv(
                (weather_data / "cleaned_weather_spring.csv")
            )

        w_sim = WeatherSimulator(df_weather_spring)

        state = w_sim.get_latest_weather_state()
        expected_state = WeatherState(
            temperature=1.72, humidity=61, precipitation=0
        )
        self.assertEqual(expected_state, state)

        w_sim.simulate(6)
        state = w_sim.get_latest_weather_state()
        expected_state = WeatherState(
            temperature=2.0388, humidity=60, precipitation=0
        )

        self.assertEqual(expected_state, state)
