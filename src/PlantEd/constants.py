"""
This module contains all constants used in PlantEd. As well as all
assumptions and initialization values that are not calculated dynamically.
"""
from typing import Final

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
PLANT_POS = (SCREEN_WIDTH / 2, SCREEN_HEIGHT - SCREEN_HEIGHT / 5)
MAX_DAYS = 35

###############################################################################
# Starch
###############################################################################
# ↓ according to doi: 10.1073/pnas.021304198
GRAM_STARCH_PER_GRAM_FRESH_WEIGHT: Final[float] = 0.0015

# ↓ according to https://doi.org/10.1046/j.0028-646X.2001.00320.x
GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT: Final[float] = 5.0
GRAM_DRY_WEIGHT_PER_GRAM_FRESH_WEIGHT: Final[float] = 1/GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT

GRAM_STARCH_PER_MICROMOL_STARCH: Final[float] = 0.0001621406
MICROMOL_STARCH_PER_GRAM_STARCH: Final[float] = (
    1 / GRAM_STARCH_PER_MICROMOL_STARCH
)

MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT = GRAM_FRESH_WEIGHT_PER_GRAM_DRY_WEIGHT * GRAM_STARCH_PER_GRAM_FRESH_WEIGHT * MICROMOL_STARCH_PER_GRAM_STARCH

###############################################################################
# Water
###############################################################################
# ToDo source
# ↓ according to ?
# 18 gram/mol -> mol/gramm = 1/18 -> 0.05550843506179199 mol/gramm -> 0.05550843506179199 * 1000000 mikromol/gram, 80% water in plant
WATER_MOL_PER_GRAM = 1/18
WATER_MIKROMOL_PER_GRAM = WATER_MOL_PER_GRAM * 1000000
MAX_WATER_POOL_PER_GRAMM = WATER_MIKROMOL_PER_GRAM * 0.8

# rainwater mm to mikromol -> 1mm/m² = 1 Liter -> are is 1/4 m²
WATER_MIKROMOL_PER_LITER = WATER_MIKROMOL_PER_GRAM * 1000 / 100

# 1.5 Tons of soil in one m³ -> PlantEd has exactly one -> 30% water, 500Kg -> 500 Litre -> 500000 Gram /18 -> 8333.333 Mol -> 8333.333/(20*6) = 70 Mol -> 70000000 Mikromol
MAX_WATER_PER_CELL = 10000
TRICKLE_AMOUNT: float = 1/10000

###############################################################################
# Nitrate
###############################################################################

# ↓ value according to https://doi.org/10.1104/pp.105.074385
# ↓ only for Roots reported
# ↓ Arabidopsis thaliana
MICROMOL_NITRATE_PER_GRAMM_FRESH_WEIGHT = 7.9

# ↓ value according to https://doi.org/10.3389/fpls.2018.00884
# ↓ Arabidopsis thaliana
MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY = 0.00336
# michaelis menten
# 0.00336 * 1000000 / (24*60*60) = 0.03888888888 RIGHT  ,mikromol g DW⁻¹s⁻¹
# Vmax ~ 0.00336 mol g DW−1 day−1 -> 3.36 mikromol g DW⁻¹ day⁻¹ -> 3.36 / (24/60/60) mikromol g DW⁻¹s⁻¹

#depending on paper
#MAX_NITRATE_INTAKE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND = MAX_NITRATE_INTAKE_PER_GRAM_ROOT_PER_DAY / 1000000 * (24 * 60 *60)
MAX_NITRATE_INTAKE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND = 0.00027


# guiding paper has 50 mmol high /0.4 mmol low for a complete growth -> 5 per cell maybe? -> 50000 mikromol
MAX_NITRATE_PER_CELL = 100     # 20*6 cells overall ->

Vmax = MAX_NITRATE_INTAKE_IN_MICROMOL_PER_GRAM_ROOT_PER_SECOND
Km = 400  # mikromol, Substrate density at which intake is 50% of max


###############################################################################
# Photon
###############################################################################

# ↓ value according to https://doi.org/10.1007/s13595-019-0911-2
# ↓ Leaf Mass per Area (LMA)
LMA_IN_GRAM_PER_SQUARE_METER: Final[float] = 40

# ↓ Specific leaf Area (SLA)
SLA_IN_SQUARE_METER_PER_GRAM: Final[float] = 1/LMA_IN_GRAM_PER_SQUARE_METER


# photon availability according to https://doi.org/10.1146/annurev-arplant-070221-024745
PEAK_PHOTON = 2000

###############################################################################
# Plant initialization values
###############################################################################

START_LEAF_BIOMASS_GRAM = 0.01
START_STEM_BIOMASS_GRAM = 0.02
START_ROOT_BIOMASS_GRAM = 0.02
START_SEED_BIOMASS_GRAM = 0.001
START_SUM_BIOMASS_GRAM = 0.05


MAXIMUM_LEAF_BIOMASS_GRAM = START_LEAF_BIOMASS_GRAM  * 10
MAXIMUM_STEM_BIOMASS_GRAM = START_STEM_BIOMASS_GRAM * 7 # base 3, plus 7 = 10 overall max
MAXIMUM_ROOT_BIOMASS_GRAM = 0.1
MAXIMUM_SEED_BIOMASS_GRAM = 0.1

BRANCH_SPOTS_BASE = 3
BRANCH_SPOTS_TOTAL = 3 + BRANCH_SPOTS_BASE
BRANCH_MASS_PER_SPOT = MAXIMUM_STEM_BIOMASS_GRAM/BRANCH_SPOTS_TOTAL


# ↓ if negative set to multiple of max_{molecule}_pool
# ↓ => for starch : -2 = 2 * max_starch_pool
# ↓ --------------------------------------------------------------------
# ↓ since plant can consume up to its pools in one simulation -2 results
# ↓ in metabolites for a minimum of 2 simulations
START_STARCH_POOL_IN_MICROMOL = -1

###############################################################################
# Pool usage factors
###############################################################################

# ↓ Factor that limits how much of the pool the plant can use per
# ↓ simulation step. The Plant can only use up to this percent
# ↓ of the pool very step. (applies to Starch, Water and Nitrate)
# ↓ value of 1 = 100% and a value of .3 = 30% of the available pool
PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP = 0.01

# ↓ Factor that limits how much of the pool the plant can use per
# ↓ simulation step. This scales based on the maximum of the pool therefore
# ↓ a value of 0.05 limits the uptake of the plant per step to 5%
# ↓ of the max pool.
PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP = 0.01


###############################################################################
# Shop Item Cost
###############################################################################

LEAF_COST = 1
BRANCH_COST = 1
ROOT_COST = 2
FLOWER_COST = 3
WATERING_CAN_COST = 1
NITRATE_COST = 1
SPRAYCAN_COST = 0


###############################################################################
# Shop Item Effect
###############################################################################
WATERING_CAN_AMOUNT = 30000  # mikromol
NITRATE_FERTILIZE_AMOUNT = 500 # mikromol

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