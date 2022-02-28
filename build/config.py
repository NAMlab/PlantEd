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

GAMESPEED = 4
GROWTH_TICK_RATE = 1000  # in ms

FONT = pygame.font.SysFont('arial', 24)
TITLE_FONT = pygame.font.SysFont('arialblack', 24)

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
# ORGANS
# LEAF
# STEM
# ROOTS
# STARCH

# SHOPITEMS

# TOOLTIPPS
# ui setup --> move to ui_setup.py
# build complete ui in a separate class (watering can, tooltips, slider, ..)
tooltipps = [ToolTip(855, 150, 0, 0,
                     ["Welcome to PlantEd!", "> This is the first demo <", "Grow your seedling", "into a big plant.", " To WIN the game", "Reach plant level 20"],
                     FONT, TITLE_FONT, mass=0),
             ToolTip(655, 380, 0, 0, ["Your plant starts as a seed.", "Use your starch deposit", "to grow the roots"],
                     FONT,
                     mass=0, point=(-45, 30)),
             ToolTip(320, 900, 0, 0, ["Time can be controlled", "in 3 different speeds.", "You can also hide Tooltipps"],
                     FONT,
                     mass=0),
             ToolTip(370, 140, 0, 0,
                     ["These are your main 3 Organs.", "Select them for Details.", "Once your roots are big enough",
                      "your are able to grow a stem!", "Try to grow it to 2 gramms"], FONT, mass=0, point=(-40, 0)),
             ToolTip(880, 780, 0, 0,
                     ["Your sprout started stem and leaf development.", "Grow its mass further to increase nutrient intake.",],
                     FONT, mass=3, point=(50, 120)),
             ToolTip(855, 155, 0, 0, ["Seedling Stage", "Stem and Leaf development", "are now available.", "Decide wich organs to grow.", "Larger roots will lead", "to faster Nitrate and H2O intake.", "Larger leaves result in more", "light reaching the plant.", "A Bigger Stem will provide", "more spots to grow leaves."],
                     FONT, TITLE_FONT, mass=5),
             ToolTip(800, 240, 0, 0,
                     ["For every level up", "you will get one Green Thumb", "to buy upgrades."],
                     FONT,
                     mass=5, point=(-50, 20)),
             ToolTip(400, 400, 0, 0, ["The yellow dots indicate", "how much energy your plant", "produces with phtosynthesis."],
                     FONT, mass=6,
                     point=(-50, 20)),
             ToolTip(800, 45, 0, 0,
                     ["Name your plant", "by clicking on the box.", "It saves automatically so", "don't be nasty please."],
                     FONT,
                     mass=7, point=(-50, -20)),
             ToolTip(220, 100, 0, 0, ["Instead of growing organs", "Select the starch icon", "to activate starch production."],
                     FONT, mass=8,
                     point=(50, 20)),
             ToolTip(220, 100, 0, 0, ["Good Job!", "Remember to keep", "producing starch."],
                     FONT, mass=8,
                     point=(50, 20)),
             ToolTip(1100, 300, 0, 0, ["50 gramms!"], FONT, mass=50),
             ToolTip(1100, 300, 0, 0, ["100 gramms!"], FONT, mass=100)]

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
# change to seed and chances --> endless
day = 1000*60*6
e = [{"type": CLOUD,
      "start_time": 1000 * 60},
    {"type": RAIN,
      "start_time": day * 1},
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
