import importlib.resources
import pandas as pd
import pygame
import numpy as np
import random

from numpy import ndarray
from pygame.locals import Rect

from PlantEd import data
from PlantEd.server.plant.plant import Plant as server_plant
from PlantEd.gameobjects.plant import Plant
from PlantEd.gameobjects.water_reservoir import Water_Grid
from PlantEd.utils.gametime import GameTime
from PlantEd.utils.particle import StillParticles
from PlantEd.utils.animation import Animation
from PlantEd import config
from PlantEd.data import assets
from PlantEd.utils.spline import Beziere

SUN_POS_SPLINE_RES: int = 10000


class Environment:
    """
    Handle sunlight, shadows , rain, and weather (temperature, humidity, precipitation)
    Draw background, soil, sky and sun

    Ideally the environment should handle nitrate, co2 and photon too
    """
    def __init__(
        self,
        plant: Plant,
        server_plant: server_plant,
        water_grid: Water_Grid,
        gametime: GameTime,
    ):
        self.plant = plant
        self.server_plant = server_plant
        self.water_grid = water_grid
        self.gametime = gametime

        self.s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.sun_pos_spline: list[tuple[float, float]] = Beziere(
            [(-100, 800), (960, -200), (2020, 800)], res=SUN_POS_SPLINE_RES
        ).points_to_draw

        self.sunpos: tuple[float, float] = (0, 0)
        self.rain_rate: int = 0

        self.rain_animation = Animation(
            images=[
                assets.img(
                    "gif_rain/frame_{index}_delay-0.05s.png".format(index=i)
                )
                for i in range(0, 21)
            ],
            duration=10,
            pos=(480, 0),
            running=False
        )

        self.shadow_map: ndarray

        # fixed for spring currently
        self.weather_data = importlib.resources.files(data) / "weather"
        df_weather_spring: pd.DataFrame = pd.read_csv((
                self.weather_data / "cleaned_weather_spring.csv"
        ).open())
        self.weather_simulator = WeatherSimulator(df_weather_spring)
        self.simulated_weather: list[list[int, int, float, float]] = self.weather_simulator.simulate(
            start_temp=df_weather_spring["temp 2m avg"][0],
            start_hum=df_weather_spring["humidity"][0],
            start_precip=df_weather_spring["precipitation"][0]
        )

        self.temperature: int = 0
        self.humidity: int = 0
        self.precipitation: float = 0

        self.sun: pygame.Surface = assets.img("sun/sun.PNG", (256, 256))
        self.cloud: pygame.Surface = assets.img("clouds/cloud_0.PNG", (402, 230))
        self.cloud_dark: pygame.Surface = assets.img("clouds/cloud_dark_0.PNG", (402, 230))
        self.nitrate: StillParticles = StillParticles(
            max_particles=10,
            spawn_box=Rect(0, 950, 1920, 300),
            boundary_box=Rect(0, 950, 1920, 300),
            color=config.BLACK,
            images=[assets.img("nitrogen.PNG", (20, 20))],
            speed=[0, 0],
            callback=self.server_plant.nitrate.get_nitrate_percentage,
            active=True,
            size=4,
            factor=100,
            once=True,
        )

    def update(self, dt):
        self.rain_animation.update(dt)
        self.update_weather()
        self.nitrate.update(dt)

        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            self.sunpos = self.sun_pos_spline[(int(day_time * SUN_POS_SPLINE_RES) - 1)]
            self.plant.organs[1].sunpos = self.sunpos

    def calc_shadowmap(
        self, leaves, sun_dir=(0.5, 1), resolution=10, max_shadow=5
    ):
        """
        Return: a grid (ndarray) of integers that represent shadow across the screen,
                resolution (int) to reduce calculation time
                max_shadow (int) to limits shadow thickness
        Reduced resolution to save performance
        """
        width: int = config.SCREEN_WIDTH
        height: int = config.SCREEN_HEIGHT

        res_width: int = int(width / resolution)
        res_height: int = int(height / resolution)

        shadow_map: np.ndarray = np.zeros((res_width, res_height))

        sun_dir_x: float = sun_dir[0]

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
            for i in range(shadow_map.shape[0]):
                for j in range(shadow_map.shape[1] - 20):
                    # delta_x for angle
                    delta_x = (j * resolution - bottom_left[1]) * sun_dir_x
                    if (
                            i * resolution > bottom_left[0] + delta_x
                            and i * resolution < bottom_right[0] + delta_x
                            and j * resolution > bottom_left[1]
                    ):
                        shadow_map[i, j] += (
                            1 if shadow_map[i, j] < max_shadow else max_shadow
                        )

        self.shadow_map = shadow_map
        return shadow_map, resolution, max_shadow

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
            color = self.get_color_mixed(config.BACKGROUND_ORANGE, config.BACKGROUND_BLUE, sun_intensity)
        else:
            color = self.get_color_mixed(config.BACKGROUND_ORANGE, config.BLACK, abs(sun_intensity))
        self.s.fill(color)
        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            offset_sunpos = (
                self.sunpos[0] - self.sun.get_width() / 2,
                self.sunpos[1] - self.sun.get_height() / 2,
            )
            self.s.blit(self.sun, offset_sunpos)
        screen.blit(self.s, (0, 0))

    def get_color_mixed(self, color0, color1, grad):
        """
        Return a linear mix of two colors based on grad which ranges values 0..1
        """
        # clamp
        grad = 0 if grad < 0 else 1 if grad > 1 else grad
        return (
            int(color0[0] * (1 - grad) + color1[0] * grad),
            int(color0[1] * (1 - grad) + color1[1] * grad),
            int(color0[2] * (1 - grad) + color1[2] * grad),
        )

    def draw_foreground(self, screen):
        screen.blit(assets.img("soil.PNG"), (0, -140))
        self.nitrate.draw(screen)
        self.rain_animation.draw(screen)

    def update_weather(self):
        """
        Update the current values for temperature, humidity and precipitation
        Handle the rain effect and respecting rain rate to fill the ground with water
        Temperature and humidity are represented in UI and affect transpiration
        """
        days, hours, minutes = self.get_day_time()
        (
            self.temperature,
            self.humidity,
            self.precipitation,
            hour,
        ) = self.simulated_weather[int(int(days) * 24 + int(hours))]
        if self.precipitation > 0:
            self.rain_animation.running = True
            self.rain_rate = self.precipitation * 10
            self.water_grid.activate_rain(self.rain_rate)
        else:
            self.rain_animation.running = False
            self.water_grid.deactivate_rain()

    def get_day_time(self) -> (int, float, float):
        """
        Return the current amount of days, hours and minutes since start of the level
        """
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        min = hour / 60
        days = int(ticks / day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def get_sun_intensity(self):
        """
        Return the sine value for current ticks. value: -1 .. 1
        -1 represents night, 0 dusk and dawn, 1 noon
        Todo check if copy of get_day_time_t
        """
        return (
            np.sin((2 * np.pi) * ((self.gametime.get_time() / (1000 * 60 * 60 * 24)) - (8 / 24)))
        )  # get time since start, convert to 0..1, 6 min interval

    def get_day_time_t(self):
        """
        Return the sine value for current ticks. value: -1 .. 1
        -1 represents night, 0 dusk and dawn, 1 noon
        """
        return (
                ((self.gametime.get_time() / (1000 * 60 * 60 * 24)) + 0.5 - 0.333)
                % 1
        ) * 2 - 1


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
        if not seed:
            seed = random.randint(0, 100)
        self.seed = seed

        self.temp_min = data["temp 2m avg"].min()
        self.temp_max = data["temp 2m avg"].max()
        self.temp_step: float = (self.temp_max - self.temp_min) / temp_bins
        self.hum_step: float = 100 / hum_bins
        self.precip_step: float = 0.1
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
            start_temp: float,
            start_hum: float,
            start_precip: float,
            start_hour: int = 0,
            start_day: int = 0,
            num_days: int = 30,
    ) -> list[list[int, int, float, float]]:
        """
        Return a list of states that include temperature, humidity and precipitation for each hour
        If the initial state is not contained in the list, it triggers an error

        Args:
            initial state: start_temp, start_hum, start_precip
            start_day: first day of the simulation
            start_hour: first hour of the simulation
        """
        random.seed(self.seed)

        simulated_hours: list = []

        curr_temp_bin = int((start_temp - self.temp_min) / self.temp_step)
        curr_hum_bin = int(start_hum / self.hum_step)
        curr_precip_bin = int(start_precip / self.precip_step)
        curr_state: tuple = (curr_temp_bin, curr_hum_bin, curr_precip_bin)

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
                        day + (hour / 24)
                    ]
                )
                # f"Temperature: {curr_temp}°C",
                # f"Humidity: {curr_hum}%",
                # f"Precipitation: {curr_precip} mm/h")

                next_state_probs = self.transitions.get(curr_state, {})
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
