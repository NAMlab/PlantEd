from pathlib import Path

import pygame
import math
import json

import os

from PlantEd.data import assets

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
pygame.font.init()
pygame.mixer.init()

# ugly, no config -> see enums
SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

FREE_SPOT = 00
BASE_SPOT = 10
LEAF_SPOT = 20
BRANCH_SPOT = 30
ROOT_SPOT = 40
FLOWER_SPOT = 50

MAX_DAYS = 27

###############################################################################
# PATHS
###############################################################################
current_dir = os.path.abspath(os.getcwd())
OPTIONS_PATH = "options.json"

# ambience_volume
# music_volume
# sfx_volume
# naration_volume

START_PATH = "sound/start"
AMBIENCE_PATH = "sound/ambience"
MUSIC_PATH = "sound/music"
BEE_SFX_PATH = "sound/bee"
SNAIL_SFX_PATH = "sound/bee"
BUG_SFX_PATH = "sound/bug"
SELECT_SFX_PATH = "sound/select"
CONFIRM_SFX_PATH = "sound/confirm"
BUY_SFX_PATH = "sound/buy"
ALERT_SFX_PATH = "sound/alert"
ERROR_SFX_PATH = "sound/error"
TOGGLE_SFX_PATH = "sound/toggle"
LOOSE_SFX_PATH = "sound/loose"
ORGANS_SFX_PATH = "sound/select_organs"
HIVE_SFX_PATH = "sound/hive_clicked"
WATERING_CAN = "sound/watering_can"
LEVEL_UP = "sound/level_up"
SPRAYCAN = "sound/spraycan"
NITROGEN = "sound/nitrogen"
REWARD = "sound/reward"
POP_SEED = "sound/pop_seed"

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

###############################################################################
# COLORS
###############################################################################
WHITE = (255, 255, 255, 255)
DARK_WHITE = (180, 170, 148)
GRAY = (145, 145, 145)
LIGHT_GRAY = (50, 50, 50)
WHITE_TRANSPARENT = (255, 255, 255, 128)
GREY_TRANSPARENT = (128, 128, 128, 128)
DARK_GREY_TRANSPARENT = (128, 128, 128, 180)
DARKER_GREY_TRANSPARENT = (128, 128, 128, 210)
RED_GRAY_TRANSPARENT = (161, 92, 92, 210)
RED_TRANSPARENT = (255, 0, 0, 210)
GREEN = (150, 168, 96, 255)
TRANSPARENT = (0, 0, 0, 255)
BLACK = (0, 0, 0)
BLUE = (75, 75, 200)

BACKGROUND_ORANGE = (137, 77, 0)
BACKGROUND_BLUE = (118, 231, 255)

DARK_BLUE = (10, 40, 190)
LIGHT_BLUE = (25, 30, 255)
SKY_BLUE = (169, 247, 252)
YELLOW = (255, 250, 94, 255)
RED = (255, 0, 0, 255)
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
NITRATE_BROWN=(90, 40, 10)

PLANTNAME = "GenEric"
_OPTIONS = None

# WEATHER

spring = {"Min_T": 5, "Max_T": 20, "shift": 10, "skew": 3.2}

# shift should be -20.8 according to Nadines paper.
# But this seems easier to grasp for the player as it is wamrest 1 to 6 pm
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


def hex_color_to_float(hex_color):
    float_color = [hex_color[0]/255, hex_color[1]/255, hex_color[2]/255, hex_color[3]/255]
    return float_color

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


def load_options():
    fileDir = Path(__file__).parent / "options.json"

    with open(fileDir) as convert_file:
        options = json.load(convert_file)
    return options


def write_options(options):
    fileDir = Path(__file__).parent / "options.json"

    with open(fileDir, "w") as convert_file:
        convert_file.write(json.dumps(options))


def write_dict(dict, path):
    with open("{}.json".format(path), "w") as outfile:
        json.dump(dict, outfile)

def load_dict(path) -> dict:
    with open(path) as convert_file:
        plant_dict = json.load(convert_file)
    return plant_dict

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

# NITRATE RATE
NITRATE_FILL_CELL = 10000


# this file should hold states of objects necessary for savegames
# GAMETIME

# SAVEGAME OBJECTS

# SHOPITEMS

# TOOLTIPPS
# ui setup --> move to ui_setup.py
# build complete ui in a separate class (watering can, tooltips, slider, ..)


def load_tooltipps():
    fileDir = Path(__file__).parent / "tooltipps.json"

    with open(fileDir) as convert_file:
        tooltipps = json.load(convert_file)
    return tooltipps


def write_tooltipps(tooltipps):
    fileDir = Path(__file__).parent / "tooltipps.json"

    with open(fileDir, "w") as convert_file:
        convert_file.write(json.dumps(tooltipps))
