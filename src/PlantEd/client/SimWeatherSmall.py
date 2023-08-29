from __future__ import annotations

from typing import Dict

from PlantEd.server.environment.weather_state import WeatherState


class WeatherSimulatorMinimal:
    def __init__(self):
        self.latest_hour: int = 0
        self.state: Dict[int, WeatherState] = {}

    def __str__(self):
        return str(self.to_dict()["states"])

    def __eq__(self, other):
        if not isinstance(other, WeatherSimulatorMinimal):
            return False

        if self.latest_hour != other.latest_hour:
            return False

        for hour, state in self.state.items():
            try:
                other_state = other.get_weather_state(hour)
            except KeyError:
                return False

            if state != other_state:
                return False

        return True

    def get_weather_state(self, time: int) -> WeatherState:
        try:

            state: WeatherState = self.state[time]

            return state

        except KeyError as e:
            raise KeyError(f"Weather state for hour: {time} does not exist") from e

    def get_latest_weather_state(self):
        return self.state[self.latest_hour]

    def to_dict(self) -> dict:
        dic = {}
        all_states = {}
        for hour, state in self.state.items():
            all_states[hour] = state.to_dict()

        dic["states"] = all_states
        dic["latest_hour"] = self.latest_hour

        return dic

    @classmethod
    def from_dict(cls, dic: dict) -> WeatherSimulatorMinimal:
        w_sim = WeatherSimulatorMinimal()
        w_sim.latest_hour = int(dic["latest_hour"])
        states_as_dic = dic["states"]
        for hour, state in states_as_dic.items():
            w_sim.state[int(hour)] = WeatherState(
                temperature=state["temperature"],
                humidity=state["humidity"],
                precipitation=state["precipitation"]
            )
        return w_sim
