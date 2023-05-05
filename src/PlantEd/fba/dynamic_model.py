import logging
from pathlib import Path

import cobra
from cobra import Reaction
from sympy import Add

from PlantEd import config
from PlantEd.client.growth_rates import GrowthRates
from PlantEd.client.growth_percentage import GrowthPercent

from PlantEd.client.update import UpdateInfo
from PlantEd.fba.helpers import (
    normalize,
)
from PlantEd.server.plant.plant import (
    Plant,
    ROOT_BIOMASS_GRAM_PER_MICROMOL,
    STEM_BIOMASS_GRAM_PER_MICROMOL,
    LEAF_BIOMASS_GRAM_PER_MICROMOL,
    SEED_BIOMASS_GRAM_PER_MICROMOL,
)
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
Km = 4000  # mikromol

# Todo change to 0.1 maybe
MAX_STARCH_INTAKE = 0.9

# gram to mikromol
MAX_WATER_POOL_GRAMM = 0.05550843506179199 * 1000000

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


# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(
        self,
        model=cobra.io.read_sbml_model(script_dir / "PlantEd_model.sbml"),
    ):
        self.model = model.copy()
        self.set_objective()
        self._objective_value: float = 0

        self.plant = Plant()

        self.use_starch = False
        self.temp = 20  # degree ceclsius        # define init pool and rates in JSON or CONFIG

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

        self.percentages: GrowthPercent = GrowthPercent(
            0.25, 0.25, 0.25, 0, 0, 1
        )
        self.update_constraints()

        self.init_constraints()
        self.calc_growth_rate(self.percentages)

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
        return 150 * self.percentages.time_frame

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.plant.water.water_pool = self.plant.water.max_water_pool
        self.set_bounds(NITRATE, (0, 1000))
        self.set_bounds(PHOTON, (0, 0))
        self.set_bounds(CO2, (-1000, 0))
        self.set_bounds(STARCH_OUT, (0, 1000))
        self.set_bounds(STARCH_IN, (0, 0))

        # Literature ATP NADPH: 7.27 and 2.56 mmol gDW−1 day−1

    def calc_growth_rate(self, new_growth_percentages: GrowthPercent):
        time_frame = new_growth_percentages.time_frame
        self.seconds_passed += time_frame

        logger.debug(
            f"Simulating the growth of the plant for {time_frame} seconds."
        )

        self.plant.update_nitrate_pool_intake(
            seconds= time_frame,
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
        starch_upper_bound = self.plant.starch_pool.calc_available_starch_in_mol_per_gram_and_time(
            gram_of_organ=self.plant.stem_biomass_gram,
            time_in_seconds=time_frame,
        )
        logger.debug(f"Upper Bound for starch is {starch_upper_bound}")

        starch_bounds = (0, starch_upper_bound)
        logger.debug(f"Bounds for starch are {starch_bounds}")
        self.set_bounds(STARCH_IN, starch_bounds)

        water_upper_bounds = (
            self.plant.water.calc_available_water_in_mol_per_gram_and_time(
                gram_of_organ=self.plant.root_biomass_gram,
                time_in_seconds=time_frame,
            )
        )
        water_bounds = (-1000, water_upper_bounds)
        logger.debug(f"Bounds for water are  {water_bounds}")
        self.set_bounds(WATER, water_bounds)

        photon_upper_bound = (
            self.plant.specific_leaf_area_in_square_meter
            * self.micromol_photon_per_square_meter
        )
        photon_bounds = (0, photon_upper_bound)
        logger.debug(f"Bounds for photons are {photon_bounds}")
        self.set_bounds(PHOTON, photon_bounds)

        nitrate_upper_bounds = (
            self.plant.nitrate.calc_available_nitrate_in_micromol_per_gram_and_time(
                gram_of_organ=self.plant.root_biomass_gram,
                time_in_seconds=time_frame,
            )
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
        co2 = co2 * leaf_biomass * time_frame
        photon = photon * leaf_biomass * time_frame

        # via stem
        starch_out = starch_out * stem_biomass * time_frame
        starch_in = starch_in * stem_biomass * time_frame
        logger.debug(
            f"Starch_in is {starch_in} and starch_out is {starch_out}"
        )

        # via root
        water = water * root_biomass * time_frame
        nitrate = nitrate * root_biomass * time_frame

        # set values
        self.plant.root_biomass = self.plant.root_biomass + root
        self.plant.stem_biomass = self.plant.stem_biomass + stem
        self.plant.leafs_biomass = self.plant.leafs_biomass + leaf
        self.plant.seed_biomass = self.plant.seed_biomass + seed

        self.plant.photon = photon
        self.plant.co2 = co2


        # update water
        self.plant.water.water_intake = water
        self.plant.update_max_water_pool()
        self.update_transpiration_factor()
        self.plant.update_transpiration(
            transpiration_factor = self.transpiration_factor,
        )

        # update starch pool
        self.plant.starch_out = starch_out
        self.plant.starch_in = starch_in
        self.plant.update_max_starch_pool()
        self.plant.starch_pool.available_starch_pool = (
            self.plant.starch_pool.available_starch_pool
            + (starch_out - starch_in)
        )

        # update nitrate pool
        self.plant.update_max_nitrate_pool()
        self.plant.nitrate.nitrate_intake = nitrate
        self.plant.nitrate.nitrate_pool -= nitrate

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

    def update_transpiration_factor(self):
        K = 291.18

        day = 1000 * 60 * 60 * 24
        hour = day / 24
        current_hour = (self.seconds_passed % day) / hour

        RH = config.get_y(current_hour, config.humidity)
        T = config.get_y(current_hour, config.summer)
        In_Concentration = water_concentration_at_temp[int(T + 2)]
        Out_Concentration = water_concentration_at_temp[int(T)]
        new_transpiration_factor = K * (
            In_Concentration - Out_Concentration * RH / 100
        )

        logger.debug(f"Setting transpiration_factor to {new_transpiration_factor}.")

        self.transpiration_factor = new_transpiration_factor

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
        self.plant.nitrate.nitrate_pool += amount

    def activate_starch_resource(self, percentage: float=1):
        logger.info("Activating starch resource")

        self.plant.starch_pool.allowed_starch_pool_consumption = percentage

    def deactivate_starch_resource(self):
        logger.info("Deactivating starch resource")
        self.plant.starch_pool.allowed_starch_pool_consumption = 0

    def update(self, update_info=UpdateInfo):
        dt = update_info.delta_time
        root_mass = self.plant.root_biomass_gram
        PLA = update_info.PLA
        sun_intensity = update_info.sun_intensity
        RH = update_info.humidity
        T = update_info.temperature

        self.update_bounds(root_mass, PLA * sun_intensity)
        self.update_pools(dt)

    def update_pools(self, dt):
        gamespeed = self.gametime.GAMESPEED
        self.plant.water.water_intake_pool = (
            0  # reset to not drain for no reason
        )

    def update_bounds(self, root_mass, photon_in):
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(root_mass)))
        # photon_in = photon_in * 300  # mikromol/m2/s
        # self.set_bounds(PHOTON, (0, photon_in))

    def update_constraints(self):
        root_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_ROOT)
        stem_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_STEM)
        leaf_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_LEAF)
        seed_reaction: Reaction = self.model.reactions.get_by_id(BIOMASS_SEED)
        starch_out_reaction: Reaction = self.model.reactions.get_by_id(
            STARCH_OUT
        )

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
        mass_molecule = [
            ROOT_BIOMASS_GRAM_PER_MICROMOL,
            STEM_BIOMASS_GRAM_PER_MICROMOL,
            LEAF_BIOMASS_GRAM_PER_MICROMOL,
            SEED_BIOMASS_GRAM_PER_MICROMOL,
            GRAM_STARCH_PER_MICROMOL_STARCH,
        ]

        n_reactions = len(reactions)
        cons = []

        for i in range(0, n_reactions):
            reaction = reactions[i]

            if percentage[i] == 0:
                # cannot transfer molecule into pool
                bounds = (0, 0)
                reaction.bounds = bounds
                logger.debug(
                    f"Setting bounds for Reaction {reaction.id} to {bounds}"
                )

                # skip iteration since no constraint needs to be set
                # since the bounds already take care of setting reaction to 0
            else:
                # it's possible to transfer molecule into pool
                # => set bounds in a way that molecule can be exported
                bounds = (0, 1000)
                reaction.bounds = bounds
                logger.debug(
                    f"Setting bounds for Reaction {reaction.id} to {bounds}"
                )

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
                            reactions[i].flux_expression
                            * mass_organ[i]
                            * mass_molecule[i]
                            / percentage[i]
                            - reactions[j].flux_expression
                            * mass_organ[j]
                            * mass_molecule[j]
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
