from __future__ import annotations
import importlib.resources

import json
from typing import Union

import pandas as pd
from PlantEd import data
from PlantEd.client.SimWeatherSmall import WeatherSimulatorMinimal
from PlantEd.server.environment.grid import MetaboliteGrid
from PlantEd.server.environment.weather import WeatherSimulator, WeatherState


class Environment:
    water_grid: MetaboliteGrid = MetaboliteGrid()
    nitrate_grid: MetaboliteGrid = MetaboliteGrid()

    weather_data = importlib.resources.files(data) / "weather"
    df_weather_spring: pd.DataFrame = pd.read_csv(
        (weather_data / "cleaned_weather_spring.csv").open()
    )

    weather: Union[WeatherSimulator, WeatherSimulatorMinimal] = WeatherSimulator(
        data=df_weather_spring
    )
    time_in_s: int = 0

    def __str__(self):
        string = f"Water Grid:\n{self.water_grid}\n----------\nNitrate Grid\n{self.nitrate_grid}\n----------\nWeather\n{self.weather}"
        return string

    def simulate(self, time_in_s):
        if time_in_s <= 0:
            return

        start_time = self.time_in_s
        self.time_in_s += time_in_s
        end_time = self.time_in_s

        seconds_missing_for_full_h = 3600 - self.time_in_s % 3600
        state_hour = int(start_time // 3600)

        weather_state: WeatherState = self.weather.get_weather_state(state_hour)
        self.water_grid.rain_linke_increase(
            time_in_s=seconds_missing_for_full_h, rain=weather_state.precipitation
        )

        state_hour = state_hour + 1
        full_hours = int(end_time // 3600)

        for hour in range(state_hour + 1, state_hour + full_hours + 1, 1):
            weather_state = self.weather.get_weather_state(hour)
            self.water_grid.rain_linke_increase(
                time_in_s=3600, rain=weather_state.precipitation
            )

        residual_seconds = (time_in_s - seconds_missing_for_full_h) % 3600

        if residual_seconds == 0:
            return

        weather_state = self.weather.get_weather_state(end_time // 3600)
        self.water_grid.rain_linke_increase(
            time_in_s=residual_seconds, rain=weather_state.precipitation
        )

    def to_dict(self):
        dic = {}

        dic["water_grid"] = self.water_grid.to_dict()
        dic["nitrate_grid"] = self.nitrate_grid.to_dict()
        dic["weather"] = self.weather.to_dict()
        dic["time_in_s"] = self.time_in_s

        return dic

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, dic: dict) -> Environment:
        env = Environment()

        env.water_grid = MetaboliteGrid.from_dict(dic["water_grid"])
        env.nitrate_grid = MetaboliteGrid.from_dict(dic["nitrate_grid"])
        env.weather = WeatherSimulator.from_dict(dic["weather"])
        env.time_in_s = dic["time_in_s"]

        return env

    @classmethod
    def from_json(cls, string: str) -> Environment:
        dic = json.loads(string)

        return Environment.from_dict(dic=dic)
