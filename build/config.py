import pygame
from tool_tip import ToolTip

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
#
pygame.init()

SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

GAMESPEED = 4
GROWTH_TICK_RATE = 1000  # in ms

FONT = pygame.font.SysFont('arial', 24)
TITLE_FONT = pygame.font.SysFont('arialblack', 24)


def get_time():
    return pygame.time.get_ticks()


class GameTime:
    def __init__(self):
        self.starttime = pygame.time.get_ticks()
        self.currenttime = self.starttime
        self.GAMESPEED = 1
        self.pause = False
        self.pause_start = 0
        self.timediff = 0  # used to add sped up or slowed time to the current time
        self.deltatime = self.starttime  # tmp time for states
        self.change_speed(1)

    def change_speed(self, factor=2):
        ticks = pygame.time.get_ticks()
        if self.pause:
            self.pause = False
            self.deltatime -= (ticks - self.pause_start)
        self.timediff += (ticks - self.deltatime) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = ticks  # set up
        self.GAMESPEED *= factor

    def set_speed(self, speed):
        ticks = pygame.time.get_ticks()
        if self.pause:
            self.pause = False
            self.timediff -= (ticks - self.pause_start)
        self.timediff += (ticks - self.deltatime) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = ticks  # set up
        self.GAMESPEED = speed

    def start_pause(self):
        self.GAMESPEED = 0
        self.pause = True
        self.pause_start = pygame.time.get_ticks()

    def play(self):
        self.set_speed(1)

    def faster(self):
        self.set_speed(10)

    def get_time(self):
        if self.pause:
            return self.pause_start - self.starttime + self.timediff + (
                    (pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)
        else:
            return pygame.time.get_ticks() - self.starttime + self.timediff + (
                    (pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)


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
tooltipps = [ToolTip(855, 150, 0, 0,
                     ["Welcome to PlantEd!", "> This is the first demo <", "Grow your seedling", "into a big plant."],
                     FONT, TITLE_FONT, mass=0),
             ToolTip(655, 380, 0, 0, ["Your plant starts as a seed.", "Use your starch deposit", "to grow the roots"],
                     FONT,
                     mass=0, point=(-45, 30)),
             ToolTip(270, 900, 0, 0, ["Time can be controlled", "in 3 different speeds."],
                     FONT,
                     mass=0, point=(-30, 120)),
             ToolTip(370, 140, 0, 0,
                     ["These are your main 3 Organs.", "Select them for Details.", "Once your roots are big enough",
                      "your are able to grow a stem!", "Try to grow it to 2 gramms"], FONT, mass=0, point=(-40, 0)),
             ToolTip(880, 780, 0, 0,
                     ["Your sprout started stem and leaf development.", "Grow its mass further to increase nutrient intake.",],
                     FONT, mass=2, point=(50, 120)),
             ToolTip(855, 155, 0, 0, ["Seedling Stage", "Stem and Leaf development", "are now available.", "Decide wich organs to grow.", "Larger roots will lead", "to faster Nitrate and H2O intake.", "Larger leaves result in more", "light reaching the plant.", "A Bigger Stem will provide", "more spots to grow leaves."],
                     FONT, TITLE_FONT, mass=4),
             ToolTip(800, 240, 0, 0,
                     ["For every level up", "you will get one chloroplast", "to buy upgrades."],
                     FONT,
                     mass=5, point=(-50, 20)),
             ToolTip(400, 400, 0, 0, ["The yellow dots indicate", "how much energy your plant", "produces with phtosynthesis."],
                     FONT, mass=6,
                     point=(-50, 20)),
             ToolTip(220, 100, 0, 0, ["Instead of growing organs", "Select the starch icon", "to activate starch production."],
                     FONT, mass=8,
                     point=(50, 20)),
             ToolTip(1100, 300, 0, 0, ["50 gramms!"], FONT, mass=50),
             ToolTip(1100, 300, 0, 0, ["100 gramms!"], FONT, mass=100),
             ToolTip(1000, 600, 0, 0, ["You son of a b*tch did it!" "200 Gramms, thats game"], FONT, mass=200,
                     point=(50, 20), )]

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
day = 1000*60*6
e = [{"type": CLOUD,
      "start_time": 1000 * 60},
    {"type": RAIN,
      "start_time": 1000 * 60 * 6},
    {"type": CLOUD,
      "start_time": 1000 * 60 * 9},
     {"type": SUN,
      "start_time": 1000 * 60 * 12},
     {"type": HAWK,
      "start_time": day * 8},
     {"type": CLOUD,
      "start_time": 1000 * 60 * 18},
     ]
