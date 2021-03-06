import pygame
from utils.tool_tip import ToolTip

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet

pygame.init()

# ugly, no config -> see enums
SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# COLORS
WHITE = (255, 255, 255)
GRAY = (145, 145, 145)
WHITE_TRANSPARENT = (255, 255, 255, 128)
GREEN = (150, 168, 96)
BLACK = (0,0,0)
BLUE = (75, 75, 200)
SKY_BLUE = (169, 247, 252)
YELLOW = (255, 250, 94)

GAMESPEED = 4
GROWTH_TICK_RATE = 1000  # in ms

SMALL_FONT = pygame.font.SysFont('arial', 16)
FONT = pygame.font.SysFont('arial', 24)
TITLE_FONT = pygame.font.SysFont('arialblack', 24)
BIG_FONT = pygame.font.SysFont('arial', 28)
YELLOW_TRANSPARENT = (255,255,255,128)
PURPLE = (171, 36, 255)

PLANTNAME = 'GenEric'

# WEATHER
# shift should be -20.8 according to Nadines paper. But this seems easier to grasp for the player as it is wamrest 1 to 6 pm
summer = {"Min_T" : 15,
          "Max_T" : 30,
          "shift" : 10,
          "skew" : 3.2}

winter = {"Min_T" : -5,
          "Max_T" : 10,
          "shift" : 10,
          "skew" : 3.2}

# HUMIDITY
humidity = {"Min_H" : 0.4,
          "Max_H" : 1,
          "shift" : 10,
          "skew" : 3.2}

# provide season and x in hours to get temp or humidity
def get_y(x,dict):
    M = (dict["Min_T"] + dict["Max_T"]) / 2  # mean
    A = (dict["Max_T"] - dict["Min_T"]) / 2  # amplitude
    F = (2 * math.pi) / 24  # based on a 25 hour cycle
    P = dict["shift"]# shift
    d = dict["skew"]# skewness
    temp = M + A * math.sin(F*((x-P)+d*(math.sin(F*(x-P))/2)))
    #print(temp)
    return temp


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
tooltipps = [ToolTip(820, 150, 0, 0,
                     ["Welcome to PlantEd!", "> This is the first demo <", "Grow your seedling", "into a big plant.", " To WIN the game", "Reach plant level 20"],
                     FONT, TITLE_FONT, mass=0),
             ToolTip(340, 615, 0, 0, ["Your plant starts as a seed.", "Use your starch deposit", "to grow the roots"],
                     FONT,
                     mass=0, point=(-45, -20)),
             ToolTip(350, 920, 0, 0, ["Time can be controlled", "in 2 different speeds.", "You can also hide Tooltipps"],
                     FONT,
                     mass=0),
             ToolTip(370, 110, 0, 0,
                     ["These are your main 3 organs.", "Once your roots are big enough",
                      "your are able to grow a stem!", "Try to grow it to 4 gramms"], FONT, mass=0, point=(-40, 0)),
             ToolTip(450, 700, 0, 0,
                     ["Your sprout started stem and leaf development.", "Grow its mass further to increase nutrient intake.",],
                     FONT, mass=3, point=(50, 120)),
             ToolTip(830, 150, 0, 0, ["Seedling Stage", "Stem and leaf development", "are now available.", "Decide wich organs to grow.", "Larger roots will lead", "to faster nitrate and water intake.", "Larger leaves result in more", "light reaching the plant.", "A bigger Stem will provide", "more spots to grow leaves."],
                     FONT, TITLE_FONT, mass=5),
             ToolTip(350, 60, 0, 0,
                     ["For every level up", "you will get one Green Thumb", "to buy upgrades."],
                     FONT,
                     mass=5, point=(-50, 0)),
             ToolTip(310, 490, 0, 0, ["The green and white dots indicate", "what you plant is producing."],
                     FONT, mass=6,
                     point=(-50, 20)),
             ToolTip(1090, 70, 0, 0,
                     ["Name your plant", "by clicking on the box.", "It saves automatically so", "don't be nasty please."],
                     FONT,
                     mass=7, point=(-50, -20)),
             ToolTip(900, 300, 0, 0, ["50 gramms!"], FONT, mass=50),
             ToolTip(900, 300, 0, 0, ["100 gramms!"], FONT, mass=100)]

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
# change to seed and chances --> endless
day = 1000*60*6
e = [{"type": CLOUD,
      "start_time": 1000 * 60},
    {"type": RAIN,
      "start_time": day /5},
    {"type": SUN,
      "start_time": day * 2},
    {"type": CLOUD,
      "start_time": day * 4},
    {"type": RAIN,
      "start_time": day * 5},
    {"type": SUN,
      "start_time": day * 6},
    {"type": RAIN,
      "start_time": day * 9},
    {"type": CLOUD,
      "start_time": day * 11},
    {"type": SUN,
      "start_time": day * 15},
    {"type": CLOUD,
      "start_time": day * 16},
    {"type": RAIN,
      "start_time": day * 17 + day*0.5},
    {"type": SUN,
      "start_time": day * 18},
    {"type": CLOUD,
      "start_time": day * 25},
    {"type": SUN,
      "start_time": day * 27},
    {"type": CLOUD,
      "start_time": day * 30},
    {"type": RAIN,
      "start_time": day * 33},
    {"type": SUN,
      "start_time": day * 35},
    {"type": CLOUD,
      "start_time": day * 40},
    {"type": SUN,
      "start_time": day * 45},
    {"type": HAWK,
      "start_time": day * 8},
    {"type": HAWK,
      "start_time": day * 12},
    {"type": HAWK,
      "start_time": day * 18},
    {"type": HAWK,
      "start_time": day * 25},
    {"type": HAWK,
      "start_time": day * 30},
    {"type": HAWK,
      "start_time": day * 35},
    ]
