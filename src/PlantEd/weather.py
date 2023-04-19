import importlib.resources

import pandas as pd
import pygame
from pygame.locals import Rect

from PlantEd import data, config, server
from PlantEd.utils.particle import StillParticles
from PlantEd.utils.animation import Animation
import numpy as np
import random
from PlantEd import config
from PlantEd.data import assets
from PlantEd.utils.spline import Beziere

SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

color = (0, 0, 0)
orange = (137, 77, 0)
blue = (118, 231, 255)

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Environment can be altered by 4 different events: Sun, Rain, Cloud, Wind
# altering: Temp, H2O, N, Photon_level
# caused by: time
# draw: background, clouds, sun, moon, wind, birds, rain
# gust = [pygame.transform.scale(pygame.image.load("../assets/wind/gust_{}.png".format(i)),(960,540)) for i in range(0,5)]
rain_sound = assets.sfx("rain/rain_sound.mp3")
rain_sound.set_volume(0.05)


class Environment:
    def __init__(
        self,
        plant,
        server_plant: server.Plant,
        water_grid,
        nitrate,
        water,
        gametime,
    ):
        self.s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.water_grid = water_grid
        self.gametime = gametime
        self.background = assets.img("soil.PNG").convert_alpha()
        self.sun_pos_spline = Beziere(
            [(-100, 800), (960, -200), (2020, 800)], res=10000
        ).points_to_draw
        self.sunpos = (0, 0)
        self.rain_rate = 0.0003
        self.plant = plant
        self.server_plant = server_plant
        self.wind_force = (0, 0)
        self.wind_duration = 0  # at 60fps
        rain_images = [
            assets.img(
                "gif_rain/frame_{index}_delay-0.05s.png".format(index=i)
            )
            for i in range(0, 21)
        ]
        self.animations = [Animation(rain_images, 10, (480, 0), running=False)]
        self.shadow_map = None

        # fixed for spring currently
        self.weather_data = importlib.resources.files(data) / "weather"
        weather_spring = (
            self.weather_data / "cleaned_weather_spring.csv"
        ).open()

        df_weather_spring = pd.read_csv(weather_spring)
        self.weather_simulator = WeatherSimulator(df_weather_spring)
        start_temp = df_weather_spring["temp 2m avg"][0]
        start_hum = df_weather_spring["humidity"][0]
        start_precip = df_weather_spring["precipitation"][0]
        self.simulated_weather = self.weather_simulator.simulate(
            start_temp, start_hum, start_precip
        )
        '''import matplotlib.pyplot as plt

        temp = [row[0] for row in self.simulated_weather]
        hum = [row[1] for row in self.simulated_weather]
        preci = [row[2] for row in self.simulated_weather]
        time = [row[3] for row in self.simulated_weather]
        # plt.plot(time, preci)
        """plt.xticks(np.arange(30, step=1))
        for i in(np.arange(30)):
            plt.axvline(i)"""
        fig, axs = plt.subplots(3)
        fig.suptitle("spring")
        axs[0].plot(time, temp)
        axs[1].plot(time, hum)
        axs[2].plot(time, preci)

        # plt.plot(temp)
        # plt.plot(preci)
        plt.xlabel = "days"
        plt.savefig("src/PlantEd/data/weather/" + "spring" + ".svg")'''

        self.temperature = 0
        self.humidity = 0
        self.precipitation = 0

        # init drop sprites
        # drops = [pygame.transform.scale(assets.img("rain/raindrop{}.png".format(i)), (16, 16)) for i in range(0, 3)]
        # splash = [pygame.transform.scale(assets.img("rain/raindrop_splash{}.png".format(i)), (16, 16)) for i in range(0, 4)]
        self.sun = assets.img("sun/sun.PNG", (256, 256))
        self.cloud = assets.img("clouds/cloud_0.PNG", (402, 230))
        self.cloud_dark = assets.img("clouds/cloud_dark_0.PNG", (402, 230))
        self.nitrate = StillParticles(
            10,
            spawn_box=Rect(0, 950, 1920, 300),
            boundary_box=Rect(0, 950, 1920, 300),
            color=(0, 0, 0),
            images=[assets.img("nitrogen.PNG", (20, 20))],
            speed=[0, 0],
            # ToDo callback really needed scales only the particles?
            callback=self.server_plant.nitrate.get_nitrate_percentage,
            active=True,
            size=4,
            factor=100,
            once=True,
        )

    def update(self, dt):
        # self.sun_pos_spline.update(dt)
        for animation in self.animations:
            animation.update(dt)
        self.update_weather()
        # self.rain.update(dt)
        self.nitrate.update(dt)

        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            self.sunpos = self.sun_pos_spline[(int(day_time * 10000) - 1)]
            self.plant.organs[1].sunpos = self.sunpos

    def calc_shadowmap(
        self, leaves, sun_dir=(0.5, 1), resolution=10, max_shadow=5
    ):
        width = config.SCREEN_WIDTH
        height = config.SCREEN_HEIGHT

        res_width = int(width / resolution)
        res_height = int(height / resolution)

        map = np.zeros((res_width, res_height))

        sun_dir_x = sun_dir[0]
        # sun_dir_y = sun_dir[1]

        # calc below shadows
        for leaf in leaves:
            bottom_left = (
                leaf["x"] - leaf["offset_x"],
                leaf["y"] - leaf["offset_y"] + leaf["image"].get_height(),
            )
            bottom_right = (
                bottom_left[0] + leaf["image"].get_width(),
                bottom_left[1],
            )
            # check x below
            for i in range(map.shape[0]):
                for j in range(map.shape[1] - 20):
                    # delta_x for angle
                    delta_x = (j * resolution - bottom_left[1]) * sun_dir_x

                    if (
                        i * resolution > bottom_left[0] + delta_x
                        and i * resolution < bottom_right[0] + delta_x
                        and j * resolution > bottom_left[1]
                    ):
                        # print(bottom_right,
                        # bottom_left, i * resolution, j * resolution)
                        map[i, j] += (
                            1 if map[i, j] < max_shadow else max_shadow
                        )

        self.shadow_map = map
        return map, resolution, max_shadow

    def draw_shadows(self, screen):
        self.s.fill((0, 0, 0, 0))
        if self.shadow_map is not None:
            # self.s.fill((0, 0, 0, 0))

            # draw polygon for each shadow
            # vs make polygon from all outer points

            for (x, y), value in np.ndenumerate(self.shadow_map):
                if self.shadow_map[x, y] > 0:
                    pygame.draw.circle(
                        self.s,
                        config.GREY_TRANSPARENT,
                        (x * 10, y * 10),
                        1 + self.shadow_map[x, y],
                    )
                else:
                    pass
            screen.blit(self.s, (0, 0))

    def draw_background(self, screen):
        self.s.fill((0, 0, 0, 0))
        sun_intensity = self.get_sun_intensity()

        if sun_intensity > 0:
            color = self.get_color(orange, blue, sun_intensity)
        else:
            color = self.get_color(orange, (0, 0, 0), abs(sun_intensity))
        self.s.fill(color)
        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            offset_sunpos = (
                self.sunpos[0] - self.sun.get_width() / 2,
                self.sunpos[1] - self.sun.get_height() / 2,
            )
            self.s.blit(self.sun, offset_sunpos)
        screen.blit(self.s, (0, 0))

    def get_color(self, color0, color1, grad):
        return (
            int(color0[0] * (1 - grad) + color1[0] * grad),
            int(color0[1] * (1 - grad) + color1[1] * grad),
            int(color0[2] * (1 - grad) + color1[2] * grad),
        )

    def draw_foreground(self, screen):
        screen.blit(self.background, (0, -140))
        self.nitrate.draw(screen)
        for animation in self.animations:
            animation.draw(screen)

    def update_weather(self):
        days, hours, minutes = self.get_day_time()
        (
            self.temperature,
            self.humidity,
            self.precipitation,
            hour,
        ) = self.simulated_weather[int(int(days) * 24 + int(hours))]
        if self.precipitation > 0:
            self.animations[0].running = True
            self.rain_rate = self.precipitation * 10
            self.water_grid.activate_rain(self.rain_rate)
        else:
            self.animations[0].running = False
            self.water_grid.deactivate_rain()

    def get_day_time(self) -> (int, float, float):
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        min = hour / 60
        days = int(ticks / day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def get_sun_intensity(self):
        return -(
            np.sin(
                np.pi / 2
                - np.pi / 5
                + (
                    (self.gametime.get_time() / (1000 * 60 * 60 * 24))
                    * np.pi
                    * 2
                )
            )
        )  # get time since start, convert to 0..1, 6 min interval

    def get_day_time_t(self):
        return (
            ((self.gametime.get_time() / (1000 * 60 * 60 * 24)) + 0.5 - 0.333)
            % 1
        ) * 2 - 1


class WeatherSimulator:
    def __init__(
        self, data, temp_bins=50, hum_bins=50, precip_bins=100, seed=15
    ):
        if not seed:
            seed = random.randint(0, 100)
        self.seed = seed

        self.temp_min = data["temp 2m avg"].min()
        self.temp_max = data["temp 2m avg"].max()
        self.temp_step = (self.temp_max - self.temp_min) / temp_bins
        self.hum_step = 100 / hum_bins
        self.precip_step = 0.1
        self.precip_bins = precip_bins

        # Calculate transition probabilities
        self.transitions = {}
        for i in range(len(data) - 1):
            curr_temp = data["temp 2m avg"][i]
            curr_hum = data["humidity"][i]
            curr_precip = data["precipitation"][i]
            next_temp = data["temp 2m avg"][i + 1]
            next_hum = data["humidity"][i + 1]
            next_precip = data["precipitation"][i + 1]

            # print(i, curr_temp, curr_hum, curr_precip, next_temp,
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

    def simulate(
        self,
        start_temp,
        start_hum,
        start_precip,
        start_hour=0,
        start_day=0,
        num_days=30,
    ):
        random.seed(self.seed)

        simulated_hours = []

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
                simulated_hours.append(
                    [
                        int(curr_temp),
                        int(curr_hum),
                        curr_precip,
                        day + (hour / 24),
                    ]
                )
                # print(f"Day {day}, Hour {hour}:",
                # f"Temperature: {curr_temp}°C",
                # f"Humidity: {curr_hum}%",
                # f"Precipitation: {curr_precip} mm/h")

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

        return simulated_hours
