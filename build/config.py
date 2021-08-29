import pygame
# this file is for configurations, options, rates, gamespeed
# is this the playce to get gametime from?
# settings: HARD, INTERMEDIATE, EASY, Graphics - not yet
#
SUN = pygame.USEREVENT+1
RAIN = pygame.USEREVENT+2
CLOUD = pygame.USEREVENT+3

GAMESPEED = 1
GROWTH_TICK_RATE = 1000 # in ms

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
    #STEM
    # ROOTS
    # STARCH

    # SHOPITEMS

# TOOLTIPPS

# PARTICLE SYSTEMS

# BUTTONS

# EVENTS
rain = {"type": RAIN,
        "time": 1000*60*60, #miliseconds
        "duration": 10000, #in milliseconds
        "delta_temp": -5} #temperature in celsius
