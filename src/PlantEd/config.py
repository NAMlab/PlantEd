import pygame
import math
import json
from data import assets
import os

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
# pygame.init()

# ugly, no config -> see enums
SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

SPRING = 10
SUMMER = 20
FALL = 30
WINTER = 40

MAX_DAYS = 27

current_dir = os.path.abspath(os.getcwd())
OPTIONS_PATH = "options.json"

# OPTIONS_PATH = OPTIONS_PATH.replace('/', os.sep).replace('\\', os.sep)

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# COLORS
WHITE = (255, 255, 255)
DARK_WHITE = (180, 170, 148)
GRAY = (145, 145, 145)
LIGHT_GRAY = (50, 50, 50)
WHITE_TRANSPARENT = (255, 255, 255, 128)
GREY_TRANSPARENT = (128, 128, 128, 128)
GREEN = (150, 168, 96)
TRANSPARENT = (0, 0, 0, 255)
BLACK = (0, 0, 0)
BLUE = (75, 75, 200)
DARK_BLUE = (10, 40, 190)
LIGHT_BLUE = (25, 30, 255)
SKY_BLUE = (169, 247, 252)
YELLOW = (255, 250, 94)
RED = (255, 0, 0)
RED_TRANSPARENT = (255, 0, 0, 128)
LIGHT_RED = (255, 193, 189)
ORANGE = (255, 111, 0)

GAMESPEED = 4
GROWTH_TICK_RATE = 1000  # in ms

SMALL_FONT = pygame.font.SysFont("timesnewroman", 16)
FONT = pygame.font.SysFont("timesnewroman", 24)
TITLE_FONT = pygame.font.SysFont("timesnewroman", 24)
BIG_FONT = pygame.font.SysFont("timesnewroman", 28)
BIGGER_FONT = pygame.font.SysFont("timesnewroman", 36)
MENU_TITLE = pygame.font.SysFont("timesnewroman", 72)
MENU_SUBTITLE = pygame.font.SysFont("timesnewroman", 56)
YELLOW_TRANSPARENT = (255, 255, 255, 128)
PURPLE = (171, 36, 255)
BROWN = (161, 148, 120)

PLANTNAME = "GenEric"
_OPTIONS = None

# WEATHER

spring = {"Min_T": 5, "Max_T": 20, "shift": 10, "skew": 3.2}

# shift should be -20.8 according to Nadines paper. But this seems easier to grasp for the player as it is wamrest 1 to 6 pm
summer = {"Min_T": 15, "Max_T": 30, "shift": 10, "skew": 3.2}

fall = {"Min_T": 1, "Max_T": 18, "shift": 10, "skew": 3.2}

winter = {"Min_T": -5, "Max_T": 10, "shift": 10, "skew": 3.2}

# HUMIDITY
humidity = {"Min_T": 0.4, "Max_T": 1, "shift": -20.8, "skew": 3.2}

water_concentration_at_temp = [
    0.269,
    0.288,
    0.309,
    0.33,
    0.353,
    0.378,
    0.403,
    0.431,
    0.459,
    0.49,
    0.522,
    0.556,
    0.592,
    0.63,
    0.67,
    0.713,
    0.757,
    0.804,
    0.854,
    0.906,
    0.961,
    1.018,
    1.079,
    1.143,
    1.21,
    1.28,
    1.354,
    1.432,
    1.513,
    1.598,
    1.687,
    1.781,
    1.879,
    1.981,
    2.089,
    2.201,
    2.318,
    2.441,
    2.569,
    2.703,
]


# provide season and x in hours to get temp or humidity
def get_y(x, dict):
    M = (dict["Min_T"] + dict["Max_T"]) / 2  # mean
    A = (dict["Max_T"] - dict["Min_T"]) / 2  # amplitude
    F = (2 * math.pi) / 24  # based on a 24 hour cycle
    P = dict["shift"]  # shift
    d = dict["skew"]  # skewness
    temp = M + A * math.sin(F * ((x - P) + d * (math.sin(F * (x - P)) / 2)))
    # print(temp)

    mean_temperature = (dict["Min_T"] + dict["Max_T"]) / 2
    amplitude = (dict["Max_T"] - dict["Min_T"]) / 2
    F = (2 * math.pi) / 24
    shift = dict["shift"]
    skew = dict["skew"]
    temp = mean_temperature + amplitude * math.sin(
        F * ((x - shift) + skew * (math.sin(F * (x - shift)) / 2))
    )
    return temp


def load_options(path):
    with open(path) as convert_file:
        options = json.load(convert_file)
    return options


def write_options(path, options):
    with open(path, "w") as convert_file:
        convert_file.write(json.dumps(options))


def apply_volume(options):
    volume = options["effects"]
    for sound in assets._sound_library:
        sound.set_volume(volume)


# PLANT

# ORGANS

# LEAF

# STEM

# ROOTS

# STARCH

# DYNAMIC MODEL


# this file should hold states of objects necessary for savegames
# GAMETIME

# SAVEGAME OBJECTS

# SHOPITEMS

# TOOLTIPPS
# ui setup --> move to ui_setup.py
# build complete ui in a separate class (watering can, tooltips, slider, ..)


def load_tooltipps(path):
    with open(path) as convert_file:
        tooltipps = json.load(convert_file)
    return tooltipps


def write_tooltipps(path, tooltipps):
    with open(path, "w") as convert_file:
        convert_file.write(json.dumps(tooltipps))


# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
# change to seed and chances --> endless
day = 1000 * 60 * 60 * 24
e = [
    {"type": CLOUD, "start_time": 1000 * 60},
    {"type": RAIN, "start_time": day / 5},
    {"type": SUN, "start_time": day * 2},
    {"type": CLOUD, "start_time": day * 4},
    {"type": RAIN, "start_time": day * 5},
    {"type": SUN, "start_time": day * 6},
    {"type": RAIN, "start_time": day * 9},
    {"type": CLOUD, "start_time": day * 11},
    {"type": SUN, "start_time": day * 15},
    {"type": CLOUD, "start_time": day * 16},
    {"type": RAIN, "start_time": day * 17 + day * 0.5},
    {"type": SUN, "start_time": day * 18},
    {"type": CLOUD, "start_time": day * 25},
    {"type": SUN, "start_time": day * 27},
    {"type": CLOUD, "start_time": day * 30},
    {"type": RAIN, "start_time": day * 33},
    {"type": SUN, "start_time": day * 35},
    {"type": CLOUD, "start_time": day * 40},
    {"type": SUN, "start_time": day * 45},
    {"type": HAWK, "start_time": day * 8},
    {"type": HAWK, "start_time": day * 12},
    {"type": HAWK, "start_time": day * 18},
    {"type": HAWK, "start_time": day * 25},
    {"type": HAWK, "start_time": day * 30},
    {"type": HAWK, "start_time": day * 35},
]
