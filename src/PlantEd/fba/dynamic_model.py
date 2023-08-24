import logging
import math
from pathlib import Path

import cobra
from cobra import Reaction
from sympy import Add
import numpy as np
import scipy.integrate as integrate

from PlantEd.client.growth_rates import GrowthRates
from PlantEd.client.growth_percentage import GrowthPercent

from PlantEd.client.update import UpdateInfo
from PlantEd.fba.helpers import (
    normalize,
)
from PlantEd.server.environment.environment import Environment
from PlantEd.server.plant.plant import Plant

from PlantEd.server.plant.starch import GRAM_STARCH_PER_MICROMOL_STARCH

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
Vmax = 0.038 # mikroMol/gDW / s

Km = 4000  # mikromol

# Todo change to 0.1 maybe
MAX_STARCH_INTAKE = 0.9

# gram to mikromol
MAX_WATER_POOL_GRAMM = 0.05550843506179199 * 1000000

summer = {"Min_T": 15, "Max_T": 30, "shift": 10, "skew": 3.2}

fall = {"Min_T": 1, "Max_T": 18, "shift": 10, "skew": 3.2}

winter = {"Min_T": -5, "Max_T": 10, "shift": 10, "skew": 3.2}

# HUMIDITY
humidity = {"Min_T": 0.4, "Max_T": 1, "shift": -20.8, "skew": 3.2}


def get_y(x, dict):
    M = (dict["Min_T"] + dict["Max_T"]) / 2  # mean
    A = (dict["Max_T"] - dict["Min_T"]) / 2  # amplitude
    F = (2 * math.pi) / 24  # based on a 24 hour cycle
    P = dict["shift"]  # shift
    d = dict["skew"]  # skewness
    temp = M + A * math.sin(F * ((x - P) + d * (math.sin(F * (x - P)) / 2)))
    # print(temp)

    mean_temperature = (dict["Min_T"] + dict["Max_T"]) / 2
    amplitude = (dict["Max_T"] - dict["Min_T"]) / 2
    F = (2 * math.pi) / 24
    shift = dict["shift"]
    skew = dict["skew"]
    temp = mean_temperature + amplitude * math.sin(
        F * ((x - shift) + skew * (math.sin(F * (x - shift)) / 2))
    )
    return temp


logger = logging.getLogger(__name__)

# script_dir = Path(__file__).parent.absolute()
fileDir = Path(__file__)
script_dir = fileDir.parent


# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(
        self,
        enviroment: Environment,
        model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
    ):
        self.model = model.copy()
        self.set_objective()
        self._objective_value: float = 0

        self.plant = Plant(ground_grid_resolution=Environment.water_grid.grid_size)

        self.use_starch = False
        self.temp = (
            20  # degree ceclsius        # define init pool and rates in JSON or CONFIG
        )

        # based on paper
        # copies of intake rates to drain form pools
        self.photon_intake = 0  # 300micromol /m2 s * PLA(gDW * slope)
        self.transpiration_factor = 0
        self.co2_intake = 0
        self.starch_intake_max = MAX_STARCH_INTAKE  # upper bound
        self.percentages_sum = 0
        self.seconds_passed = 0

        # growth rates for each objective
        self.growth_rates = GrowthRates("mol", 0, 0, 0, 0, 0, 0, 0)

        self.percentages: GrowthPercent = GrowthPercent(0.25, 0.25, 0.25, 0, 0, 1)
        self.update_constraints()

        self.init_constraints()
        self.calc_growth_rate(
            new_growth_percentages=self.percentages, environment=enviroment
        )

    def set_objective(self):
        root: Reaction = self.model.reactions.get_by_id("Biomass_tx_root")
        stem: Reaction = self.model.reactions.get_by_id("Biomass_tx_stem")
        leaf: Reaction = self.model.reactions.get_by_id("Biomass_tx_leaf")
        seed: Reaction = self.model.reactions.get_by_id("Biomass_tx_seed")
        starch: Reaction = self.model.reactions.get_by_id("Starch_out_tx_stem")

        objective = self.model.problem.Objective(
            expression=Add(leaf.flux_expression)
            + Add(root.flux_expression)
            + Add(seed.flux_expression)
            + Add(stem.flux_expression)
            + Add(starch.flux_expression),
            direction="max",
            name="multi_objective",
        )

        self.model.objective = objective

    @property
    def micromol_photon_per_square_meter(self):
        # ToDo better scaling over day (no light at 'night')

        # ↓ 150 according to https://doi.org/10.3389/fpls.2017.00681
        # up to 1230 mikromol/s/m² max -> sine function to simulate?
        return 1200 * self.get_sun_intensity_for_duration(
            self.seconds_passed - self.percentages.time_frame, self.seconds_passed
        )  # * self.percentages.time_frame

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.plant.water.water_pool = self.plant.water.max_water_pool
        self.set_bounds(NITRATE, (0, 1000))
        self.set_bounds(PHOTON, (0, 0))
        self.set_bounds(CO2, (-1000, 0))
        self.set_bounds(STARCH_OUT, (0, 1000))
        self.set_bounds(STARCH_IN, (0, 0))

        # Literature ATP NADPH: 7.27 and 2.56 mmol gDW−1 day−1

    def calc_growth_rate(
        self, new_growth_percentages: GrowthPercent, environment: Environment
    ):
        time_frame = new_growth_percentages.time_frame
        weather_state = environment.weather.get_latest_weather_state()

        self.seconds_passed += time_frame

        logger.debug(f"Simulating the growth of the plant for {time_frame} seconds.")

        self.plant.update_nitrate_pool_intake(
            seconds=time_frame,
        )

        if new_growth_percentages != self.percentages:
            logger.info("Updating the model objectives.")
            self.percentages = new_growth_percentages
            self.update_constraints()

        # ToDo only approx since only current weather is taken into account

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

        # set limits from pools
        # ToDo move in own function
        starch_upper_bound = (
            self.plant.starch_pool.calc_available_starch_in_mol_per_gram_and_time(
                gram_of_organ=self.plant.stem_biomass_gram,
                time_in_seconds=time_frame,
            )
        )
        logger.debug(f"Upper Bound for starch is {starch_upper_bound}")

        starch_bounds = (0, starch_upper_bound)
        logger.debug(f"Bounds for starch are {starch_bounds}")
        self.set_bounds(STARCH_IN, starch_bounds)

        water_upper_bound_plant_pool = (
            self.plant.water.calc_available_water_in_mol_per_gram_and_time(
                gram_of_organ=self.plant.root_biomass_gram,
                time_in_seconds=time_frame,
            )
        )

        water_upper_bound_env_pool = environment.water_grid.available_absolute(
            self.plant.root
        ) / (self.plant.root_biomass_gram * time_frame)

        self.plant.water.update_transpiration_factor(weather_state=weather_state)
        self.plant.update_transpiration()

        transpiration = self.plant.get_transpiration_in_micromol(
            time_in_s=time_frame
        )  # ToDo check with stomata

        max_usable_water = max(
            water_upper_bound_plant_pool + water_upper_bound_env_pool - transpiration, 0
        )

        water_bounds = (-1000, max_usable_water)
        logger.debug(
            f"Available Water from Plant pool is: {water_upper_bound_plant_pool}, available water from env pool is: {water_upper_bound_env_pool}, transpiration is {transpiration}. Bounds for water set to: {water_bounds}"
        )
        self.set_bounds(WATER, water_bounds)

        photon_upper_bound = (
            self.plant.specific_leaf_area_in_square_meter
            * self.micromol_photon_per_square_meter
        )
        photon_bounds = (0, photon_upper_bound)
        logger.debug(f"Bounds for photons are {photon_bounds}")
        self.set_bounds(PHOTON, photon_bounds)

        # Nitrate

        nitrate_upper_bound_plant_pool = (
            self.plant.nitrate.calc_available_nitrate_in_micromol_per_gram_and_time(
                gram_of_organ=self.plant.root_biomass_gram,
                time_in_seconds=time_frame,
            )
        )

        nitrate_upper_bound_env_pool = environment.nitrate_grid.available_relative_mm(
            roots= self.plant.root,
            time_seconds= time_frame,
            g_root= self.plant.root_biomass_gram,
            v_max= Vmax,
            k_m= Km,
        )

        nitrate_upper_bounds = (
            nitrate_upper_bound_env_pool + nitrate_upper_bound_plant_pool
        )

        nitrate_bounds = (-1000, nitrate_upper_bounds)
        logger.debug(f"Bounds for nitrate are  {nitrate_bounds}")
        self.set_bounds(NITRATE, nitrate_bounds)

        solution = self.model.optimize()

        logger.debug(
            f"Simulation resulted in an objective_value of "
            f"{solution.objective_value:.4E}."
        )

        self._objective_value = solution.objective_value

        # get flux with unit micromol/(hour * organ_mass)

        # biomass
        root = solution.fluxes.get(BIOMASS_ROOT)
        stem = solution.fluxes.get(BIOMASS_STEM)
        leaf = solution.fluxes.get(BIOMASS_LEAF)
        seed = solution.fluxes.get(BIOMASS_SEED)

        logger.debug(
            f"Flux of leaf biomass is {leaf}, "
            f"flux of stem biomass is {stem}, "
            f"flux of root biomass is {root}, "
            f"flux of seed biomass is {seed}"
        )

        # via leaf
        co2 = solution.fluxes[CO2]
        photon = solution.fluxes[PHOTON]

        # via stem
        starch_out = solution.fluxes.get(STARCH_OUT)
        starch_in = solution.fluxes[STARCH_IN]

        # via root
        water = solution.fluxes[WATER]
        nitrate = solution.fluxes[NITRATE]

        # Normalize
        # - multiply with time and mass resulting in micromol as unit
        # - micromol/(seconds * organ_mass) * organ_mass[gram] * time_frame[s]

        # biomass
        root = root * root_biomass * time_frame
        stem = stem * stem_biomass * time_frame
        leaf = leaf * leaf_biomass * time_frame
        seed = seed * seed_biomass * time_frame

        logger.debug(
            f"Leaf biomass is {leaf} micromol, "
            f"stem biomass is {stem} micromol, "
            f"root biomass is {root} micromol, "
            f"seed biomass is {seed} micromol."
        )

        # Uptake and release
        # via leaf
        co2_uptake_in_micromol_per_second_and_gram = co2
        co2 = co2 * leaf_biomass * time_frame
        photon = photon * leaf_biomass * time_frame
        logger.debug(f"CO2 uptake is {co2}, photon uptake is {photon}")

        # via stem
        starch_out = starch_out * stem_biomass * time_frame
        starch_in = starch_in * stem_biomass * time_frame
        logger.debug(f"Starch_in is {starch_in} and starch_out is {starch_out}")

        # via root
        water = water * root_biomass * time_frame
        nitrate = nitrate * root_biomass * time_frame
        logger.debug(f"Water uptake is {water}, nitrate uptake is {nitrate}")

        # set values
        self.plant.root_biomass = self.plant.root_biomass + root
        self.plant.stem_biomass = self.plant.stem_biomass + stem
        self.plant.leafs_biomass = self.plant.leafs_biomass + leaf
        self.plant.seed_biomass = self.plant.seed_biomass + seed

        self.plant.photon = photon
        self.plant.co2 = co2
        self.plant.co2_uptake_in_micromol_per_second_and_gram = (
            co2_uptake_in_micromol_per_second_and_gram
        )

        # update water
        used_water = water + transpiration

        if used_water > water_upper_bound_env_pool:
            taken_from_internal_pool = used_water - water_upper_bound_env_pool

            self.plant.water.water_pool -= taken_from_internal_pool
            used_water -= taken_from_internal_pool

        environment.water_grid.drain(amount=used_water, roots=self.plant.root)

        self.plant.update_max_water_pool()
        self.plant.water.update_transpiration_factor(weather_state=weather_state)
        self.plant.update_transpiration()

        amount = self.plant.water.missing_amount
        available = environment.water_grid.available_absolute(roots=self.plant.root)
        diff = min(amount, available)

        environment.water_grid.drain(amount=diff, roots=self.plant.root)
        self.plant.water.water_pool += diff

        # update nitrate
        used_nitrate = nitrate

        if used_nitrate > nitrate_upper_bound_env_pool:
            taken_from_internal_pool = used_nitrate - nitrate_upper_bound_env_pool

            self.plant.nitrate.nitrate_pool -= taken_from_internal_pool
            used_nitrate -= taken_from_internal_pool

        environment.nitrate_grid.drain(amount=used_nitrate, roots=self.plant.root)

        self.plant.update_max_nitrate_pool()
        self.plant.nitrate.nitrate_intake = nitrate
        amount = self.plant.nitrate.missing_amount
        available = environment.nitrate_grid.available_absolute(roots=self.plant.root)
        diff = min(amount, available)
        environment.nitrate_grid.drain(amount=diff, roots=self.plant.root)
        self.plant.nitrate.nitrate_pool += diff

        self.plant.nitrate.nitrate_pool -= nitrate

        # update starch pool
        self.plant.starch_out = starch_out
        self.plant.starch_in = starch_in
        self.plant.update_max_starch_pool()
        self.plant.starch_pool.available_starch_pool = (
            self.plant.starch_pool.available_starch_pool + (starch_out - starch_in)
        )

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

        logger.debug(f"Updated Plant is as follows - {str(self.plant)}")

    def open_stomata(self):
        """
        Method that realizes the opening of the stomas.
        """

        logger.info("Opening stomata")
        self.plant.stomata_open = True

        bounds = (-1000, 1000)
        self.set_bounds(CO2, bounds)
        logger.debug(f"CO2 bounds set to {bounds}")

    def close_stomata(self):
        """
        Method that realizes the closing of the stomas.
        """
        logger.info("Closing stomata")
        self.plant.stomata_open = False

        bounds = (-1000, 0)
        self.set_bounds(CO2, bounds)
        logger.debug(f"CO2 bounds set to {bounds}")

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
        return max(((Vmax * nitrate_pool) / (Km + nitrate_pool)) * mass, 0)  # second

    def stop_water_intake(self):
        self.set_bounds(WATER, (-1000, 0))

    def enable_water_intake(self):
        self.set_bounds(WATER, (-1000, 1000))

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def increase_nitrate(self, amount):
        self.plant.nitrate.nitrate_pool += amount

    def activate_starch_resource(self, percentage: float = 1):
        logger.info("Activating starch resource")

        self.plant.starch_pool.allowed_starch_pool_consumption = percentage

    def deactivate_starch_resource(self):
        logger.info("Deactivating starch resource")
        self.plant.starch_pool.allowed_starch_pool_consumption = 0

    def get_sun_intensity_for_duration(self, start, end):
        start = start / (3600 * 24)
        end = end / (3600 * 24)
        f = lambda x: np.sin((2 * np.pi) * ((x) - (8 / 24)))
        i = integrate.quad(f, start, end)
        return max(i[0] / (end - start), 0)

    def update_constraints(self):
        root_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_ROOT)
        stem_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_STEM)
        leaf_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_LEAF)
        seed_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_SEED)
        starch_out_reaction: Reaction = self.model.reactions.get_by_id(STARCH_OUT)

        names = ["root", "stem", "leaf", "seed", "starch_out"]
        reactions = [
            root_reaction,
            stem_reaction,
            leaf_reaction,
            seed_reaction,
            starch_out_reaction,
        ]
        percentage = [
            self.percentages.root,
            self.percentages.stem,
            self.percentages.leaf,
            self.percentages.flower,
            self.percentages.starch,
        ]
        mass_organ = [
            self.plant.root_biomass_gram,
            self.plant.stem_biomass_gram,
            self.plant.leafs_biomass_gram,
            self.plant.seed_biomass_gram,
            self.plant.stem_biomass_gram,
        ]

        n_reactions = len(reactions)
        cons = []

        for i in range(0, n_reactions):
            reaction = reactions[i]

            if percentage[i] == 0:
                # cannot transfer molecule into pool
                bounds = (0, 0)
                reaction.bounds = bounds
                logger.debug(f"Setting bounds for Reaction {reaction.id} to {bounds}")

                # skip iteration since no constraint needs to be set
                # since the bounds already take care of setting reaction to 0
            else:
                # it's possible to transfer molecule into pool
                # => set bounds in a way that molecule can be exported
                bounds = (0, 1000)
                reaction.bounds = bounds
                logger.debug(f"Setting bounds for Reaction {reaction.id} to {bounds}")

            for j in range(i + 1, n_reactions):
                name = f"{names[i]}_and_{names[j]}"

                # check for old constraint and remove them
                old_cons = self.model.constraints.get(name)
                if old_cons is not None:
                    logger.debug(f"Removing the constraint with name {name}")
                    self.model.remove_cons_vars(old_cons)

                # check if new constraint needs to be set in place (percentages != 0)
                # and set them
                if percentage[i] != 0 and percentage[j] != 0:
                    constraint = self.model.problem.Constraint(
                        (
                            reactions[i].flux_expression * mass_organ[i] / percentage[i]
                            - reactions[j].flux_expression
                            * mass_organ[j]
                            / percentage[j]
                        ),
                        lb=0,
                        ub=0,
                        name=name,
                    )

                    logger.debug(f"Creating new Constraints {constraint}")

                    cons.append(constraint)

        if cons:
            self.model.add_cons_vars(cons)
