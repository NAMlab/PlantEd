from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate

from PlantEd.grid import MetaboliteGrid
from PlantEd.constants import MAX_WATER_PER_CELL, MAX_NITRATE_PER_CELL, PEAK_PHOTON, WATERING_CAN_AMOUNT, \
    NITRATE_FERTILIZE_AMOUNT
from PlantEd.server.weather import WeatherSimulator

fileDir = Path(__file__)
script_dir = fileDir.parent.parent


class Environment:
    def __init__(self, start_time, seed):
        self.time = start_time  # seconds
        self.water_grid: MetaboliteGrid = MetaboliteGrid(max_metabolite_cell=MAX_WATER_PER_CELL,
                                                         preset_fill_amount=MAX_WATER_PER_CELL / 20)
        self.nitrate_grid: MetaboliteGrid = MetaboliteGrid(max_metabolite_cell=MAX_NITRATE_PER_CELL,
                                                           preset_fill_amount=MAX_NITRATE_PER_CELL / 10)

        df_weather_spring: pd.DataFrame = pd.read_csv(script_dir / "data/cleaned_weather_spring.csv")
        self.weather: WeatherSimulator = WeatherSimulator(
            data=df_weather_spring,
            seed=seed
        )

    def update(self, delta_t):
        weather_state = self.weather.get_weather_state(int(self.time / 3600))
        self.water_grid.rain_like_increase(delta_t, weather_state.precipitation)
        for i in range(10):
            self.water_grid.trickle(delta_t/10)

        self.time += delta_t

    def increase_water_grid(self, increase_water_grid):
        cells_to_fill = increase_water_grid["cells"]
        for i in range(len(cells_to_fill)):
            self.water_grid.add2cell(cells_to_fill[i]*WATERING_CAN_AMOUNT, i, 0)

    def increase_nitrate_grid(self, increase_nitrate_grid):
        cells_to_fill = increase_nitrate_grid["cells"]
        for cell in cells_to_fill:
            self.nitrate_grid.add2cell(cell[2]*NITRATE_FERTILIZE_AMOUNT, cell[0], cell[1])

    def micromol_photon_per_square_meter(self, start, end):
        # maximum photon * 0..1 depending on time spent in sunlight
        return PEAK_PHOTON * self.get_sun_intensity_for_duration(
            start, end
        )

    def get_sun_intensity_for_duration(self, start, end):
        start = start / (3600 * 24)
        end = end / (3600 * 24)
        f = lambda x: np.sin((2 * np.pi) * ((x) - (8 / 24)))
        i = integrate.quad(f, start, end)
        return max(i[0] / (end - start), 0)

    def get_sun_intensity(self):
        """
        Return the sine value for current ticks. value: -1 .. 1
        -1 represents night, 0 dusk and dawn, 1 noon
        Todo check if copy of get_day_time_t
        """
        return (
            np.sin((2 * np.pi) * ((self.time / (60 * 60 * 24)) - (8 / 24)))
        )

    def to_dict(self) -> dict:
        weather_state = self.weather.get_weather_state(int(self.time / 3600))
        dic = {
            "time": self.time,
            "temperature": weather_state.temperature,
            "humidity": weather_state.humidity,
            "precipitation": weather_state.precipitation,
            "nitrate_grid": self.nitrate_grid.grid.tolist(),
            "water_grid": self.water_grid.grid.tolist(),
            "sun_intensity": self.get_sun_intensity()
            # "water_grid_size": self.water_grid.grid_size,
        }
        return dic
