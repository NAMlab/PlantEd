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
        self.timediff = 0  # used to add sped up or slowed time to the current time
        self.deltatime = self.starttime  # tmp time for states
        self.change_speed(1)

    def change_speed(self, factor=2):
        self.timediff += (
                                     pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = pygame.time.get_ticks()  # set up
        self.GAMESPEED *= factor

    def get_time(self):
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
             ToolTip(655, 380, 0, 0, ["Your seed has no Leaves yet.", "Use Your Starch Deposit", "But don't waste it"],
                     FONT,
                     mass=0, point=(-45, 30)),
             ToolTip(370, 140, 0, 0,
                     ["These are your main 3 Organs.", "Select them for Details.", "Once your roots are big enough",
                      "your are able to grow a stem!"], FONT, mass=1, point=(-40, 0)),
             ToolTip(300, 300, 0, 0,
                     ["Grow your stem", "to get your first leaves", "The biomass can be",
                      "split up between all organs."],
                     FONT, mass=6, point=(-50, 20)),
             ToolTip(685, 450, 0, 0,
                     ["One leaf can be added", " for each skillpoint", "But remember to keep", "the stem big enough"],
                     FONT,
                     mass=10, point=(-50, 20)),
             ToolTip(240, 230, 0, 0, ["You can fill up", "your starch deposit", "instead of growing"], FONT, mass=15,
                     point=(50, 20)),
             ToolTip(850, 300, 0, 0, ["Congratulations, you reached", " 30gr of plant mass"], FONT, mass=30,
                     point=(50, 20)),
             ToolTip(1100, 300, 0, 0, ["50 Gramms!"], FONT, mass=50, point=(50, 20)),
             ToolTip(1100, 300, 0, 0, ["100 Gramms!"], FONT, mass=100, point=(50, 20)),
             ToolTip(1000, 600, 0, 0, ["You son of a b*tch did it!" "200 Gramms, thats game"], FONT, mass=200,
                     point=(50, 20), )]

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
e0 = {"type": RAIN,
      "start_time": 1000 * 5,  # miliseconds
      "delta_temp": -5}  # temperature in celsius

e1 = {"type": SUN,
      "start_time": 1000 * 30,  # miliseconds
      "delta_temp": 5}  # temperature in celsius

e2 = {"type": CLOUD,
      "start_time": 1000 * 35,  # miliseconds
      "delta_temp": 5}  # temperature in celsius

e3 = {"type": SUN,
      "start_time": 1000 * 60,  # miliseconds
      "delta_temp": 5}  # temperature in celsius
