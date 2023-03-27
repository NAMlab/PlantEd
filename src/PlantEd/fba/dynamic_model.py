import logging
from pathlib import Path

import cobra

from PlantEd import server
from PlantEd.client import GrowthRates, GrowthPercent
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
max_nitrate_pool_low = 12000  # mikromol
max_nitrate_pool_high = 100000  # mikromol

# Todo change to 0.1 maybe
MAX_STARCH_INTAKE = 10

MAX_WATER_POOL = 1000000
MAX_WATER_POOL_CONSUMPTION = 1

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

script_dir = Path(__file__).parent.absolute()


# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(
        self,
        gametime,
        water_grid=None,
        log=None,
        plant_mass=None,
        model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
    ):
        self.model = model.copy()
        self.plant = server.Plant()

        self.gametime = gametime
        self.water_grid = water_grid
        self.plant_mass = plant_mass
        self.use_starch = False
        objective = create_objective(self.model)
        self.model.objective = objective
        self.stomata_open = False
        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.nitrate_delta_amount = 0
        self.water_pool = 0
        self.water_intake_pool = 0
        self.max_water_pool = MAX_WATER_POOL
        self.temp = 20  # degree ceclsius
        # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0  # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        self.photon_intake = 0  # 300micromol /m2 s * PLA(gDW * slope)
        self.water_intake = 0
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
        self.nitrate_pool = max_nitrate_pool_high
        self.water_pool = self.max_water_pool
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
        self.water_intake = solution.fluxes[WATER]
        self.co2_intake = solution.fluxes[CO2]
        self.nitrate_intake = solution.fluxes[NITRATE]
        self.growth_rates.starch_intake = solution.fluxes[STARCH_IN]
        self.photon_intake = solution.fluxes[PHOTON]

        if self.stomata_open:
            if solution.fluxes[CO2] > 0 and self.water_intake > 0:
                self.water_intake = (
                    self.water_intake
                    + solution.fluxes[CO2] * self.transpiration_factor
                )

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
            In_Concentration - Out_Concentration * RH
        )

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

    def get_actual_water_drain(self):
        return self.water_intake + self.water_intake_pool

    def get_photon_upper(self):
        return self.model.reactions.get_by_id(PHOTON).bounds[1]

    def get_nitrate_pool(self):
        return self.nitrate_pool

    def increase_nitrate_pool(self, amount):
        self.nitrate_pool += amount

    def get_nitrate_percentage(self) -> float:
        return self.nitrate_pool / max_nitrate_pool_high

    def get_nitrate_intake(self, mass):
        # Michaelis-Menten Kinetics
        # v = Vmax*S/Km+S, v=intake speed, Vmax=max Intake, Km=Where S that v=Vmax/2, S=Substrate Concentration
        # Literature: Vmax ~ 0.00336 mol g DW−1 day−1, KM = 0.4 mmol,  S = 50 mmol and 1.2 mmol (high, low)
        # day --> sec
        return max(
            ((Vmax * self.nitrate_pool) / (Km + self.nitrate_pool)) * mass, 0
        )  # second

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def increase_nitrate(self, amount):
        self.nitrate_delta_amount = amount

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
        max_water_drain,
        plant_mass,
        RH,
        T,
    ):
        normalize(self.model, root_mass, stem_mass, leaf_mass, 1)
        self.max_water_pool = MAX_WATER_POOL + (plant_mass * 10000)
        self.update_bounds(root_mass, PLA * sun_intensity, max_water_drain)
        self.update_pools(dt, max_water_drain)
        self.update_transpiration_factor(RH, T)

    def update_pools(self, dt, max_water_drain):
        gamespeed = self.gametime.GAMESPEED
        # self.water_intake_pool = 0  # reset to not drain for no reason

        # Todo make work
        # if all is zero but pool not and photosynthesis, set bounds back to max

        # max water drain tells how much is there to take
        # if last intake was higher, drain differenz from pool
        # if last intake was lower, drain normally -> if water pool is lower than max, drain more, put diff in pool

        # take more water in, if possible and pool not full

        if self.water_pool < self.max_water_pool:
            if self.water_intake < max_water_drain:
                self.water_intake_pool = 0
                # excess has to be negative to get added to pool
                excess = self.water_intake - max_water_drain
                if excess < MAX_WATER_POOL_CONSUMPTION:
                    self.water_intake_pool = excess
                else:
                    self.water_intake_pool = MAX_WATER_POOL_CONSUMPTION
        self.water_pool -= self.water_intake_pool * dt * gamespeed

        if self.water_pool > self.max_water_pool:
            self.water_pool = self.max_water_pool

        self.nitrate_pool -= self.nitrate_intake * dt * gamespeed
        if self.nitrate_pool < 0:
            self.nitrate_pool = 0
        # slowly add nitrate after buying
        if self.nitrate_delta_amount > 0:
            self.nitrate_pool += max_nitrate_pool_high / 2 * dt
            self.nitrate_delta_amount -= max_nitrate_pool_high / 2 * dt

    def update_bounds(self, root_mass, photon_in, max_water_drain):
        # update photon intake based on sun_intensity
        # update nitrate inteake based on Substrate Concentration
        # update water based on grid
        # co2? maybe later in dev
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(root_mass)))

        # take from pool, if no enough
        # not enough water in soil - take from pool
        intake = max_water_drain
        self.water_intake_pool = 0
        if photon_in > 0:
            if max_water_drain < MAX_WATER_POOL_CONSUMPTION:
                if self.water_pool > 0:
                    shortage = MAX_WATER_POOL_CONSUMPTION - max_water_drain
                    # take diff from pool
                    self.water_intake_pool = shortage
                    intake = MAX_WATER_POOL_CONSUMPTION

        self.set_bounds(WATER, (-1000, intake))
        photon_in = photon_in * 300  # mikromol/m2/s
        self.set_bounds(PHOTON, (0, photon_in))
