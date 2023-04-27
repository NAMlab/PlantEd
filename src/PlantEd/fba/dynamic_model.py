import logging
from pathlib import Path

import cobra

from PlantEd.client.growth_rates import GrowthRates
from PlantEd.client.growth_percentage import GrowthPercent

from PlantEd.client.update import UpdateInfo
from PlantEd.fba.helpers import (
    create_objective,
    update_objective, normalize,
)
from PlantEd.server.plant.plant import Plant

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

# script_dir = Path(__file__).parent.absolute()
fileDir = Path(__file__)
script_dir = fileDir.parent
print(script_dir)


# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(
            self,
            gametime,
            water_grid=None,
            plant_mass=None,
            # normal
            # model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
            # build
            model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
    ):
        self.model = model.copy()

        self.plant = Plant()

        self.gametime = gametime
        self.use_starch = False
        objective = create_objective(self.model)
        self.model.objective = objective
        self.stomata_open = False

        self.temp = 20  # degree ceclsius        # define init pool and rates in JSON or CONFIG

        # based on paper
        # copies of intake rates to drain form pools
        self.photon_intake = 0  # 300micromol /m2 s * PLA(gDW * slope)
        self.transpiration_factor = 0
        self.co2_intake = 0
        self.starch_intake_max = MAX_STARCH_INTAKE  # upper bound
        self.percentages_sum = 0

        # growth rates for each objective
        self.growth_rates = GrowthRates("mol", 0, 0, 0, 0, 0, 0, 0)

        self.percentages: GrowthPercent = GrowthPercent(0.1, 0.1, 1, 0.1, 0, 1)
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

    def calc_growth_rate(
            self, new_growth_percentages: GrowthPercent
    ):
        if new_growth_percentages != self.percentages:
            logger.info("Updating the model objectives.")
            update_objective(
                self.model, growth_percentages=new_growth_percentages
            )
            self.percentages = new_growth_percentages

        time_frame = new_growth_percentages.time_frame

        root_biomass = self.plant.root_biomass_gram
        stem_biomass = self.plant.stem_biomass_gram
        leaf_biomass = self.plant.leafs_biomass_gram
        seed_biomass = self.plant.seed_biomass_gram

        normalize(
            model=self.model,
            root=root_biomass,
            stem=stem_biomass,
            leaf=leaf_biomass,
            seed=seed_biomass,
        )

        solution = self.model.optimize()

        # get flux with unit mol/(hour * organ_mass)

        # biomass
        root = solution.fluxes.get(BIOMASS_ROOT)
        stem = solution.fluxes.get(BIOMASS_STEM)
        leaf = solution.fluxes.get(BIOMASS_LEAF)
        seed = solution.fluxes.get(BIOMASS_SEED)

        # via leaf
        co2 = solution.fluxes[CO2]
        photon = solution.fluxes[PHOTON]
        photon_upper = self.model.reactions.get_by_id(
            PHOTON
        ).bounds[1]

        # via stem
        starch_out = solution.fluxes.get(STARCH_OUT)
        starch_in = solution.fluxes[STARCH_IN]

        # via root
        water = solution.fluxes[WATER]
        nitrate = solution.fluxes[NITRATE]

        # Normalize
        # - multiply with time and mass resulting in mol as unit

        # biomass
        root = root * root_biomass * time_frame
        stem = stem * stem_biomass * time_frame
        leaf = leaf * leaf_biomass * time_frame
        seed = seed * seed_biomass * time_frame

        # via leaf
        co2 = co2 * leaf_biomass * time_frame
        photon = photon * leaf_biomass * time_frame
        photon_upper = photon_upper * leaf_biomass * time_frame

        # via stem
        starch_out = starch_out * stem_biomass * time_frame
        starch_in = starch_in * stem_biomass * time_frame

        # via root
        water = water * root_biomass * time_frame
        nitrate = nitrate * root_biomass * time_frame

        # set values

        self.plant.root_biomass = root_biomass + root
        self.plant.stem_biomass = stem_biomass + stem
        self.plant.leafs_biomass = leaf_biomass + leaf
        self.plant.seed_biomass = seed_biomass + seed

        self.plant.water.water_intake = water
        self.plant.nitrate.nitrate_intake = nitrate

        self.plant.starch_out = starch_out
        self.plant.starch_in = starch_in
        self.plant.photon = photon
        self.plant.co2 = co2

        self.plant.photon_upper = photon_upper

        # ToDo remove growth_rates not needed anymore everything is in plant
        self.growth_rates.root_rate = root
        self.growth_rates.stem_rate = stem
        self.growth_rates.leaf_rate = leaf
        self.growth_rates.starch_rate = starch_out
        self.growth_rates.starch_intake = starch_in
        self.growth_rates.seed_rate = seed
        self.growth_rates.time_frame = time_frame

        # ToDo remove old duplicates now in plant
        self.co2_intake = co2
        self.photon_intake = photon

        self.plant.update_max_water_pool()


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
        (ticks % day) / hour
        # RH = config.get_y(hours, config.humidity)
        # T = config.get_y(hours, config.summer)
        In_Concentration = water_concentration_at_temp[int(T + 2)]
        Out_Concentration = water_concentration_at_temp[int(T)]
        self.transpiration_factor = K * (
                In_Concentration - Out_Concentration * RH / 100
        )

    def update_transpiration(self):
        transpiration = 0
        if self.stomata_open:
            if self.co2_intake > 0:
                transpiration = self.co2_intake * self.transpiration_factor

        # ToDo do not use Tuple
        self.plant.water.transpiration = transpiration

    def close_stomata(self):
        """
        Method that realizes the closing of the stomas.
        """
        logger.info("Closing stomata")
        self.stomata_open = False

        bounds = (-1000, 0)
        self.set_bounds(CO2, bounds)
        logger.debug(f"CO2 bounds set to {bounds}")

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
        self.set_bounds(WATER, (-1000, 0))

    def enable_water_intake(self):
        self.set_bounds(WATER, (-1000, 1000))

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

    def update(self, update_info=UpdateInfo):
        dt = update_info.delta_time
        root_mass = update_info.root_mass
        PLA = update_info.PLA
        sun_intensity = update_info.sun_intensity
        RH = update_info.humidity
        T = update_info.temperature

        self.update_bounds(root_mass, PLA * sun_intensity)
        self.update_pools(dt)
        self.update_transpiration_factor(RH, T)
        self.update_transpiration()

    def update_pools(self, dt):
        gamespeed = self.gametime.GAMESPEED
        # self.water_intake_pool = 0  # reset to not drain for no reason

        self.plant.nitrate.nitrate_pool -= (
                self.plant.nitrate.nitrate_intake * dt * gamespeed
        )

        if self.plant.nitrate.nitrate_pool < 0:
            self.plant.nitrate.nitrate_pool = 0
        # slowly add nitrate after buying
        if self.plant.nitrate.nitrate_delta_amount > 0:
            self.plant.nitrate.nitrate_pool += (
                    self.plant.nitrate.max_nitrate_pool_high / 2 * dt
            )
            self.plant.nitrate.nitrate_delta_amount -= (
                    self.plant.nitrate.max_nitrate_pool_high / 2 * dt
            )

    def update_bounds(self, root_mass, photon_in):
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(root_mass)))
        photon_in = photon_in * 300  # mikromol/m2/s
        self.set_bounds(PHOTON, (0, photon_in))
