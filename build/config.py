import pygame

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
#
SUN = 0
RAIN = 1
CLOUD = 2

GAMESPEED = 4
GROWTH_TICK_RATE = 1000  # in ms

def get_time():
    return pygame.time.get_ticks()

class GameTime:
    def __init__(self):
        self.starttime = pygame.time.get_ticks()
        self.currenttime = self.starttime
        self.GAMESPEED = 1
        self.timediff = 0 # used to add sped up or slowed time to the current time
        self.deltatime = self.starttime # tmp time for states
        self.change_speed(1)

    def change_speed(self, factor=2):
        self.timediff += (pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED # how long the gamespeed has beend altered
        self.deltatime = pygame.time.get_ticks() # set up
        self.GAMESPEED *= factor

    def get_time(self):
        return pygame.time.get_ticks() - self.starttime + self.timediff + ((pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)



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

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
e0 =       {"type": RAIN,
           "start_time": 1000 * 5,  # miliseconds
           "delta_temp": -5}  # temperature in celsius

e1 =      {"type": SUN,
           "start_time": 1000 * 30,  # miliseconds
           "delta_temp": 5}  # temperature in celsius

e2 =      {"type": CLOUD,
           "start_time": 1000 * 35,  # miliseconds
           "delta_temp": 5}  # temperature in celsius

e3 =      {"type": SUN,
           "start_time": 1000 * 60,  # miliseconds
           "delta_temp": 5}  # temperature in celsius
