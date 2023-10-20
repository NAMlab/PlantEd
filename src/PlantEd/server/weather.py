from __future__ import annotations

import logging
import random
from collections import namedtuple
import pandas as pd

weather_state = namedtuple("state", ["temperature", "humidity", "precipitation"])


class WeatherSimulator:
    """
    Create a transition matrix between weather states.
    The amount of states can be controlled via bin. Reducing the amount,
    reduces size and increases performance

    Add up all transitions happening between states and normalize them at the end

    Args:
        data: a pandas Dataframe that contains recorded weather data
        temp_bins: the number of temperature states
        hum_bins: number of humidity states
        precip_bins: number of precipitation bins
        seed: fixed probabilites of random behaviour
    """

    def __init__(
            self,
            data: pd.DataFrame,
            temp_bins: int = 50,
            hum_bins: int = 50,
            precip_bins: int = 100,
            seed: float = 15
    ):
        super().__init__()
        if not seed:
            seed = random.randint(0, 100)
        self.seed = seed

        self.temp_min = data["temp 2m avg"].min()
        self.temp_max = data["temp 2m avg"].max()

        self.temp_step: float = (self.temp_max - self.temp_min) / temp_bins
        self.hum_step: float = 100 / hum_bins
        self.precip_step: float = 0.1
        self.precip_bins = precip_bins
        self.latest_hour: int = 0
        self.states: list[weather_state] = []

        # Calculate transition probabilities
        self.transitions = {}
        for i in range(len(data) - 1):
            curr_temp = data["temp 2m avg"][i]
            curr_hum = data["humidity"][i]
            curr_precip = data["precipitation"][i]
            next_temp = data["temp 2m avg"][i + 1]
            next_hum = data["humidity"][i + 1]
            next_precip = data["precipitation"][i + 1]

            # next_hum, next_precip, self.temp_step,
            # self.hum_step, self.precip_step, next_precip / self.precip_step)

            curr_temp_bin = int((curr_temp - self.temp_min) / self.temp_step)
            curr_hum_bin = int(curr_hum / self.hum_step)
            curr_precip_bin = int(curr_precip / self.precip_step)

            next_temp_bin = int((next_temp - self.temp_min) / self.temp_step)
            next_hum_bin = int(next_hum / self.hum_step)
            next_precip_bin = int(next_precip / self.precip_step)

            curr_state = (curr_temp_bin, curr_hum_bin, curr_precip_bin)
            next_state = (next_temp_bin, next_hum_bin, next_precip_bin)

            if curr_state not in self.transitions:
                self.transitions[curr_state] = {}

            if next_state not in self.transitions[curr_state]:
                self.transitions[curr_state][next_state] = 0

            self.transitions[curr_state][next_state] += 1

        # Normalize transition probabilities
        for curr_state in self.transitions:
            total_transitions = sum(self.transitions[curr_state].values())
            for next_state in self.transitions[curr_state]:
                self.transitions[curr_state][next_state] /= total_transitions

        # ini state
        start_temp = float(data["temp 2m avg"][0])
        start_hum = float(data["humidity"][0])
        start_precip = float(data["precipitation"][0])
        self.states.append(
            weather_state(
                start_temp,
                start_hum,
                start_precip
            )
        )

        self.curr_temp_bin = int((start_temp - self.temp_min) / self.temp_step)
        self.curr_hum_bin = int(start_hum / self.hum_step)
        self.curr_precip_bin = int(start_precip / self.precip_step)
        self.curr_state: tuple = (self.curr_temp_bin, self.curr_hum_bin, self.curr_precip_bin)

        self.simulate(24 * 45)

    def simulate(
            self,
            end_hour: int,
    ):
        """
        Computes the weather up to the specified hour.

        Args:
            end_hour: Last hour for which the weather is to be simulated.
                If not already done, the weather will also be simulated for all previous hours.
        """
        random.seed(self.seed)

        for hour in range(self.latest_hour + 1, end_hour + 1, 1):
            curr_temp = self.temp_min + self.curr_temp_bin * self.temp_step
            curr_hum = self.curr_hum_bin * self.hum_step
            curr_precip = self.curr_precip_bin * self.precip_step

            self.states.append(
                weather_state(
                    curr_temp,
                    curr_hum,
                    curr_precip
                )
            )

            next_state_probs = self.transitions.get(self.curr_state, {})
            next_state_probs = {
                k: v for k, v in next_state_probs.items() if v > 0
            }  # remove zero-probability states
            next_state = random.choices(
                list(next_state_probs.keys()),
                list(next_state_probs.values()),
            )[0]

            # Update current state
            self.curr_state = next_state
            self.curr_temp_bin, self.curr_hum_bin, self.curr_precip_bin = self.curr_state

    def get_weather_state(self, time: int) -> weather_state:
        if len(self.states) > time:
            return self.states[time]
        else:
            logging.error("Weather state does not exist")
            return self.states[0]
