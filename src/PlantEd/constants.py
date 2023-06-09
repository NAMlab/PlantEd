"""
This module contains all constants used in PlantEd. As well as all
assumptions and initialization values that are not calculated dynamically.
"""
from typing import Final

###############################################################################
# Starch
###############################################################################
# ↓ according to doi: 10.1073/pnas.021304198
GRAM_STARCH_PER_GRAM_FRESH_WEIGHT: Final[float] = 0.0015

# ↓ according to https://doi.org/10.1046/j.0028-646X.2001.00320.x
GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT: Final[float] = 5.0

GRAM_STARCH_PER_MICROMOL_STARCH: Final[float] = 0.0001621406
MICROMOL_STARCH_PER_GRAM_STARCH: Final[float] = (
    1 / GRAM_STARCH_PER_MICROMOL_STARCH
)

###############################################################################
# Water
###############################################################################
# ToDo source
# ↓ according to ?
MAX_WATER_POOL_PER_GRAMM = 0.05550843506179199 * 1000 * 0.8

###############################################################################
# Water
###############################################################################

# ↓ value according to https://doi.org/10.1104/pp.105.074385
# ↓ only for Roots reported
# ↓ Arabidopsis thaliana
MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT = 7.9

# ↓ value according to https://doi.org/10.3389/fpls.2018.00884
# ↓ Arabidopsis thaliana
MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY = 0.00336
MAX_NITRATE_INTALE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND = MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY / 1000000 * 24 * 60 *60

###############################################################################
# Photon
###############################################################################

# ↓ value according to https://doi.org/10.1007/s13595-019-0911-2
# ↓ Leaf Mass per Area (LMA)
LMA_IN_GRAM_PER_SQUARE_METER: Final[float] = 40

# ↓ Specific leaf Area (SLA)
SLA_IN_SQUARE_METER_PER_GRAM: Final[float] = 1/LMA_IN_GRAM_PER_SQUARE_METER

###############################################################################
# Biomass
###############################################################################

LEAF_BIOMASS_GRAM_PER_MICROMOL = 899.477379 / 1000000
STEM_BIOMASS_GRAM_PER_MICROMOL = 916.2985939 / 1000000
ROOT_BIOMASS_GRAM_PER_MICROMOL = 956.3297883 / 1000000
SEED_BIOMASS_GRAM_PER_MICROMOL = 978.8487602 / 1000000

###############################################################################
# Plant initialization values
###############################################################################

START_LEAF_BIOMASS_GRAM = 0.5
START_STEM_BIOMASS_GRAM = 0.5
START_ROOT_BIOMASS_GRAM = 2.0
START_SEED_BIOMASS_GRAM = 0.5

# ↓ if negative set to multiple of max_{molecule}_pool
# ↓ => for starch : -2 = 2 * max_starch_pool
# ↓ --------------------------------------------------------------------
# ↓ since plant can consume up to its pools in one simulation -2 results
# ↓ in metabolites for a minimum of 2 simulations
START_STARCH_POOL_IN_MICROMOL = -1
START_WATER_POOL_IN_MICROMOL = -10
START_NITRATE_POOL_IN_MICROMOL = -10

###############################################################################
# Pool usage factors
###############################################################################

# ↓ Factor that limits how much of the pool the plant can use per
# ↓ simulation step. The Plant can only use up to this percent
# ↓ of the pool very step. (applies to Starch, Water and Nitrate)
# ↓ value of 1 = 100% and a value of .3 = 30% of the available pool
PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP = 1

# ↓ Factor that limits how much of the pool the plant can use per
# ↓ simulation step. This scales based on the maximum of the pool therefore
# ↓ a value of 0.05 limits the uptake of the plant per step to 5%
# ↓ of the max pool.
PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP = 0.02