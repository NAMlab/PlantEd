import logging
from pathlib import Path

import cobra

from PlantEd import server
from PlantEd.client import GrowthRates, GrowthPercent, Water
from PlantEd.fba.helpers import (
    create_objective,
    update_objective,
    normalize,
)

# states for objective
BIOMASS_ROOT = "Biomass_tx_root"
BIOMASS_STEM = "Biomass_tx_stem"
BIOMASS_LEAF = "Biomass_tx_leaf"
BIOMASS_SEED = "Biomass_tx_seed"
BIOMASS = "Biomass_tx_leaf"
STARCH_OUT = "Starch_out_tx_stem"
STARCH_IN = "Starch_in_tx_stem"

# intake reaction names
NITRATE = "Nitrate_tx_root"
WATER = "H2O_tx_root"
PHOTON = "Photon_tx_leaf"
CO2 = "CO2_tx_leaf"

# mol
Vmax = 3360 / 3600  # mikroMol/gDW/s
Km = 4000  # mikromol

# Todo change to 0.1 maybe
MAX_STARCH_INTAKE = 0.9

# gram to mikromol
MAX_WATER_POOL_GRAMM = 0.05550843506179199 * 1000000

FLUX_TO_GRAMM = 0.002299662183

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

logger = logging.getLogger(__name__)

#script_dir = Path(__file__).parent.absolute()
fileDir = Path(__file__)
script_dir = fileDir.parent
print(script_dir)


# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(
        self,
        gametime,
        water_grid=None,
        log=None,
        plant_mass=None,
        # normal
        #model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
        # build
        model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
    ):
        self.model = model.copy()

        self.plant = server.Plant()

        self.water_pool = 0 # plant water pool
        self.maximum_water_pool = MAX_WATER_POOL_GRAMM

        self.gametime = gametime
        self.use_starch = False
        objective = create_objective(self.model)
        self.model.objective = objective
        self.stomata_open = False
<<<<<<<

        self.temp = 20  # degree ceclsius
=======
        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.nitrate_delta_amount = 0

>>>>>>>
        # based on paper
        # copies of intake rates to drain form pools
        self.photon_intake = 0  # 300micromol /m2 s * PLA(gDW * slope)
        self.transpiration_factor = 0
        self.co2_intake = 0
        self.starch_intake_max = MAX_STARCH_INTAKE  # upper bound
        self.percentages_sum = 0

        # growth rates for each objective
        self.growth_rates = GrowthRates("1flux/s", 0, 0, 0, 0, 0, 0)

        self.percentages = GrowthPercent(0.1, 0.1, 1, 0.1, 0)
        self.init_constraints()
        self.calc_growth_rate(self.percentages)

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.plant.nitrate.set_pool_to_high()
        self.plant.water.water_pool = self.plant.water.max_water_pool
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(0.1)))
        self.set_bounds(PHOTON, (0, 0))
        self.set_bounds(CO2, (-1000, 0))
        self.set_bounds(STARCH_OUT, (0, 1000))
        self.set_bounds(STARCH_IN, (0, 0))

        # Literature ATP NADPH: 7.27 and 2.56 mmol gDW−1 day−1
        atp = 0.00727 / 24
        nadhp = 0.00256 / 24

    def calc_growth_rate(self, new_growth_percentages: GrowthPercent) -> GrowthRates:
        if new_growth_percentages != self.percentages:
            logger.info("Updating the model objectives.")
            update_objective(
                self.model, growth_percentages=new_growth_percentages
            )
            self.percentages = new_growth_percentages
        solution = self.model.optimize()

        # calc_rates 1flux/s
        self.growth_rates.root_rate = solution.fluxes.get(BIOMASS_ROOT)
        self.growth_rates.stem_rate = solution.fluxes.get(BIOMASS_STEM)
        self.growth_rates.leaf_rate = solution.fluxes.get(BIOMASS_LEAF)
        self.growth_rates.starch_rate = solution.fluxes.get(STARCH_OUT)
        self.growth_rates.seed_rate = solution.fluxes.get(BIOMASS_SEED)

        # 1/s
        self.plant.water.water_intake = solution.fluxes[WATER]
        self.co2_intake = solution.fluxes[CO2]
        self.plant.nitrate.nitrate_intake = solution.fluxes[NITRATE]
        self.growth_rates.starch_intake = solution.fluxes[STARCH_IN]
        self.photon_intake = solution.fluxes[PHOTON]

        return self.get_rates()

    def open_stomata(self):
        """
        Method that realizes the opening of the stomas.
        """

        logger.info("Opening stomata")
        self.stomata_open = True

        bounds = (-1000, 1000)
        self.set_bounds(CO2, bounds)
        logger.debug(f"CO2 bounds set to {bounds}")

    def update_transpiration_factor(self, RH, T):
        K = 291.18
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 60 * 24
        hour = day / 24
        hours = (ticks % day) / hour
        # RH = config.get_y(hours, config.humidity)
        # T = config.get_y(hours, config.summer)
        In_Concentration = water_concentration_at_temp[int(T + 2)]
        Out_Concentration = water_concentration_at_temp[int(T)]
        self.transpiration_factor = K * (
            In_Concentration - Out_Concentration * RH/100
        )

    def get_water_needed(self):
        transpiration = 0
        if self.stomata_open:
            if self.co2_intake > 0:
                transpiration = (
                    self.co2_intake * self.transpiration_factor
                )
        return self.water_intake, transpiration

    def close_stomata(self):
        """
        Method that realizes the closing of the stomas.
        """
        logger.info("Closing stomata")
        self.stomata_open = False

        bounds = (-1000, 0)
        self.set_bounds(CO2, bounds)
        logger.debug(f"CO2 bounds set to {bounds}")

    def get_rates(self) -> GrowthRates:
        """
        Method to obtain the GrowthRates in grams for the specified time period.
        The time period corresponds to the variable GAMESPEED of the gametime object.

        Returns: A GrowthRates object that describes the growth rates in grams.

        """

        growth_rates = self.growth_rates.flux2grams(self.gametime)

        logger.info(
            "Returning following growth rates:\n"
            f"leaf: {growth_rates.root_rate}, "
            f"stem {growth_rates.stem_rate}, "
            f"root {growth_rates.root_rate}, "
            f"starch: {growth_rates.starch_rate}, "
            f"starch_intake {growth_rates.starch_intake}, "
            f"seed {growth_rates.seed_rate}"
        )

        return growth_rates

    def get_absolute_rates(self):
        forced_ATP = (
            0.0049
            * self.model.reactions.get_by_id("Photon_tx_leaf").upper_bound
            + 2.7851
        )
        return (
            self.growth_rates.leaf_rate,
            self.growth_rates.stem_rate,
            self.growth_rates.root_rate,
            self.growth_rates.seed_rate,
            self.growth_rates.stem_rate,
            self.growth_rates.starch_intake,
            forced_ATP,
        )

    def get_photon_upper(self):
        return self.model.reactions.get_by_id(PHOTON).bounds[1]

    def get_nitrate_pool(self):
        return self.plant.nitrate.nitrate_pool

    def increase_nitrate_pool(self, amount):
        self.plant.nitrate.nitrate_pool += amount

    def get_nitrate_intake(self, mass):
        # ToDo move to nitrate class
        nitrate_pool = self.plant.nitrate.nitrate_pool


        # Michaelis-Menten Kinetics
        # v = Vmax*S/Km+S, v=intake speed, Vmax=max Intake, Km=Where S that v=Vmax/2, S=Substrate Concentration
        # Literature: Vmax ~ 0.00336 mol g DW−1 day−1, KM = 0.4 mmol,  S = 50 mmol and 1.2 mmol (high, low)
        # day --> sec
        return max(
            ((Vmax * nitrate_pool) / (Km + nitrate_pool)) * mass, 0
        )  # second

    def stop_water_intake(self):
        self.set_bounds(WATER, (-1000,0))

    def enable_water_intake(self):
        self.set_bounds(WATER, (-1000,1000))


    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def increase_nitrate(self, amount):
        self.plant.nitrate.nitrate_delta_amount = amount

    def set_stomata_automation(self, hours):
        self.stomata_hours = hours

    def activate_starch_resource(self, percentage=1):
        logger.info("Activating starch resource")

        self.use_starch = True

        bounds = (0, self.starch_intake_max * (percentage / 100))
        self.set_bounds(STARCH_IN, bounds)

        logger.debug(
            f"Set use_starch to {self.use_starch} "
            f"and STARCH_IN to {bounds}"
        )

    def deactivate_starch_resource(self):
        logger.info("Deactivating starch resource")

        self.use_starch = False
        bounds = (0, 0)
        self.set_bounds(STARCH_IN, bounds)
        logger.debug(
            f"Set use_starch to {self.use_starch} "
            f"and STARCH_IN to {bounds}"
        )

    def update(
        self,
        dt,
        leaf_mass,
        stem_mass,
        root_mass,
        PLA,
        sun_intensity,
        plant_mass,
        RH,
        T,
    ):
        #normalize(self.model, root_mass, stem_mass, leaf_mass, 1)
        self.update_bounds(root_mass, PLA * sun_intensity)
        self.update_pools(dt)
        self.update_transpiration_factor(RH, T)
        self.maximum_water_pool = plant_mass * MAX_WATER_POOL_GRAMM

    def update_pools(self, dt):
        gamespeed = self.gametime.GAMESPEED
        # self.water_intake_pool = 0  # reset to not drain for no reason

        self.nitrate_pool -= self.nitrate_intake * dt * gamespeed
        if self.nitrate_pool < 0:
            self.nitrate_pool = 0
        # slowly add nitrate after buying
        if nitrate_delta_amount > 0:
            nitrate_pool += max_nitrate_pool_high / 2 * dt
            nitrate_delta_amount -= max_nitrate_pool_high / 2 * dt

    def update_bounds(self, root_mass, photon_in):
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(root_mass)))
        photon_in = photon_in * 300  # mikromol/m2/s
        self.set_bounds(PHOTON, (0, photon_in))
