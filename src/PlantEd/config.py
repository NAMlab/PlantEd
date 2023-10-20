import json
from pathlib import Path
import pygame

from PlantEd.data.assets import AssetHandler


# seconds per simulation
resolution = 360
# until end of game
MAX_DAYS = 35

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

PLANT_POS = (SCREEN_WIDTH / 2, SCREEN_HEIGHT - SCREEN_HEIGHT / 5)

# todo move somewhere else
# WATERING CAN AMOUNT
WATERING_CAN_AMOUNT = 3000000  # mikromol

# NITRATE RATE
NITRATE_FILL_CELL = 50    # mikromol

def hex_color_to_float(hex_color):
    float_color = [hex_color[0] / 255, hex_color[1] / 255, hex_color[2] / 255, hex_color[3] / 255]
    return float_color


def load_options():
    fileDir = Path(__file__).parent / "options.json"

    with open(fileDir) as convert_file:
        options = json.load(convert_file)
    return options


def load_tooltipps():
    fileDir = Path(__file__).parent / "tooltipps.json"

    with open(fileDir) as convert_file:
        tooltipps = json.load(convert_file)
    return tooltipps


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


'''def apply_volume(options):
    volume = options["effects"]
    for sound in assets._sound_library:
        sound.set_volume(volume)'''


FREE_SPOT = 00
BASE_SPOT = 10
LEAF_SPOT = 20
BRANCH_SPOT = 30
ROOT_SPOT = 40
FLOWER_SPOT = 50

###############################################################################
# SOUNDS
###############################################################################
START_PATH = "sound/start"
AMBIENCE_PATH = "sound/ambience"
MUSIC_PATH = "sound/music"
BEE_SFX_PATH = "sound/bee"
SNAIL_SFX_PATH = "sound/snail_clicked"
BUG_SFX_PATH = "sound/bug"
SELECT_SFX_PATH = "sound/select"
#CONFIRM_SFX_PATH = "sound/confirm"
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

###############################################################################
# COLORS
###############################################################################
WHITE = (255, 255, 255, 255)
DARK_WHITE = (180, 170, 148)
GRAY = (145, 145, 145)
LIGHT_GRAY = (50, 50, 50)
WHITE_TRANSPARENT = (255, 255, 255, 128)
WHITE_TRANSPARENT_LESS = (255, 255, 255, 180)
GREY_TRANSPARENT = (128, 128, 128, 128)
DARK_GREY_TRANSPARENT = (128, 128, 128, 180)
DARKER_GREY_TRANSPARENT = (128, 128, 128, 210)
RED_GRAY_TRANSPARENT = (161, 92, 92, 210)
RED_TRANSPARENT = (255, 0, 0, 210)
GREEN = (150, 168, 96, 255)
GREEN_DARK = (18, 110, 0, 255)
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
LIGHT_RED = (255, 193, 189)
ORANGE = (255, 111, 0)
YELLOW_TRANSPARENT = (255, 255, 255, 128)
PURPLE = (171, 36, 255)
BROWN = (161, 148, 120)
NITRATE_BROWN = (90, 40, 10)
