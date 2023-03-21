import random
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys


class WeatherSimulator:
    def __init__(self, data, temp_bins=100, hum_bins=100, precip_bins=100):
        self.temp_min = data["temp 2m avg"].min()
        self.temp_max = data["temp 2m avg"].max()
        self.temp_step = (self.temp_max - self.temp_min) / temp_bins
        self.hum_step = 100 / hum_bins
        self.precip_step = 0.1
        self.precip_bins = precip_bins

        self.simulated_hours = []

        # Calculate transition probabilities
        self.transitions = {}
        for i in range(len(data) - 1):
            curr_temp = data["temp 2m avg"][i]
            curr_hum = data["humidity"][i]
            curr_precip = data["precipitation"][i]
            next_temp = data["temp 2m avg"][i + 1]
            next_hum = data["humidity"][i + 1]
            next_precip = data["precipitation"][i + 1]

            # print(i, curr_temp, curr_hum, curr_precip, next_temp, next_hum, next_precip, self.temp_step, self.hum_step, self.precip_step, next_precip / self.precip_step)

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

    def simulate(
        self,
        start_temp,
        start_hum,
        start_precip,
        start_hour,
        start_day,
        num_days,
        seed=None,
    ):
        if seed is not None:
            random.seed(seed)
        self.simulated_hours = []

        curr_temp_bin = int((start_temp - self.temp_min) / self.temp_step)
        curr_hum_bin = int(start_hum / self.hum_step)
        curr_precip_bin = int(start_precip / self.precip_step)
        curr_state = (curr_temp_bin, curr_hum_bin, curr_precip_bin)

        hour = start_hour
        day = start_day

        for _ in range(num_days):
            for i in range(24):
                curr_temp = self.temp_min + curr_temp_bin * self.temp_step
                curr_hum = curr_hum_bin * self.hum_step
                curr_precip = curr_precip_bin * self.precip_step

                self.simulated_hours.append(
                    [
                        int(curr_temp),
                        int(curr_hum),
                        int(curr_precip),
                        day + (hour / 24),
                    ]
                )
                # print(f"Day {day}, Hour {hour}:", f"Temperature: {curr_temp}°C", f"Humidity: {curr_hum}%", f"Precipitation: {curr_precip} mm/h")

                next_state_probs = self.transitions.get(curr_state, {})
                # print(next_state_probs)
                next_state_probs = {
                    k: v for k, v in next_state_probs.items() if v > 0
                }  # remove zero-probability states
                next_state = random.choices(
                    list(next_state_probs.keys()),
                    list(next_state_probs.values()),
                )[0]

                # Update current state
                curr_state = next_state
                curr_temp_bin, curr_hum_bin, curr_precip_bin = curr_state

                hour += 1
            hour = 0
            day += 1


spring = "cleaned_weather_spring"
summer = "cleaned_weather_summer"
fall = "cleaned_weather_fall"
seasons = [spring, summer, fall]


def main(seed=None):
    if not seed:
        seed = random.random()
    print(seed)
    for i in range(3):
        data = pd.read_csv(seasons[i] + ".csv").fillna(value=0)
        ws = WeatherSimulator(data)
        ws.simulate(12, 83, 0, 0, 0, 30, seed)
        temp = [row[0] for row in ws.simulated_hours]
        hum = [row[1] for row in ws.simulated_hours]
        preci = [row[2] for row in ws.simulated_hours]
        time = [row[3] for row in ws.simulated_hours]
        # plt.plot(time, preci)
        """plt.xticks(np.arange(30, step=1))
        for i in(np.arange(30)):
            plt.axvline(i)"""
        fig, axs = plt.subplots(3)
        fig.suptitle(seasons[i])
        axs[0].plot(time, temp)
        axs[1].plot(time, hum)
        axs[2].plot(time, preci)

        # plt.plot(temp)
        # plt.plot(preci)
        plt.xlabel = "days"
        plt.savefig(seasons[i] + ".svg")


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) > 0:
        main(args[0])
    else:
        main()
