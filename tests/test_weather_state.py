from unittest import TestCase

from PlantEd.server.environment.weather_state import WeatherState


class TestWeatherState(TestCase):
    def test_init(self):
        w_state = WeatherState(
            temperatur= 20,
            humidity= 64,
            precipitation= 0,
        )

        self.assertIsInstance(w_state, WeatherState)

    def test_equal(self):
        w_state_1 = WeatherState(
            temperatur=20,
            humidity=64,
            precipitation=0,
        )

        w_state_2 = WeatherState(
            temperatur=20,
            humidity=64,
            precipitation=0,
        )

        self.assertEqual(w_state_1, w_state_2)
        w_state_2.temperatur = 21
        self.assertNotEqual(w_state_1, w_state_2)
        w_state_2.temperatur = 20
        self.assertEqual(w_state_1, w_state_2)
        w_state_2.humidity = 63
        self.assertNotEqual(w_state_1, w_state_2)
        w_state_2.humidity = 64
        self.assertEqual(w_state_1, w_state_2)
        w_state_2.precipitation = 50
        self.assertNotEqual(w_state_1, w_state_2)

    def test_to_dict(self):
        w_state = WeatherState(
            temperatur=20,
            humidity=64,
            precipitation=0,
        )

        self.assertEqual({'temperatur': 20, 'humidity': 64, 'precipitation': 0}, w_state.to_dict())

        w_state.humidity = 15
        w_state.temperatur = 75
        w_state.precipitation = 200
        self.assertEqual({'temperatur': 75, 'humidity': 15, 'precipitation': 200}, w_state.to_dict())

    def test_from_dict(self):
        dic = {'temperatur': 75, 'humidity': 15, 'precipitation': 200}

        recreated_weather_state = WeatherState.from_dict(dic)
        self.assertEqual(75, recreated_weather_state.temperatur)
        self.assertEqual(15, recreated_weather_state.humidity)
        self.assertEqual(200, recreated_weather_state.precipitation)