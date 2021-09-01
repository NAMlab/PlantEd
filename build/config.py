import pygame

# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
#
SUN = 0
RAIN = 1
CLOUD = 2

GAMESPEED = 1
GROWTH_TICK_RATE = 1000  # in ms

STARTTIME = 0


def get_time():
    return pygame.time.get_ticks() - STARTTIME


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
