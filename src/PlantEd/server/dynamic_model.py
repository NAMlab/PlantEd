from pathlib import Path
import cobra
from cobra import Reaction
from sympy import Add
from PlantEd.server.helpers import normalize
from PlantEd.server.environment import Environment
from PlantEd.constants import Vmax, Km, SLA_IN_SQUARE_METER_PER_GRAM

fileDir = Path(__file__)
script_dir = fileDir.parent

# output
BIOMASS_ROOT = "Biomass_tx_root"
BIOMASS_STEM = "Biomass_tx_stem"
BIOMASS_LEAF = "Biomass_tx_leaf"
BIOMASS_SEED = "Biomass_tx_seed"
STARCH_OUT = "Starch_out_tx_stem"

# input
NITRATE = "Nitrate_tx_root"
WATER = "H2O_tx_root"
PHOTON = "Photon_tx_leaf"
CO2 = "CO2_tx_leaf"
STARCH_IN = "Starch_in_tx_stem"


class DynamicModel:
    def __init__(
            self,
            environment,
            plant,
            model=cobra.io.read_sbml_model(script_dir.parent / "data/PlantEd_model.sbml"),
            start_time=0
            ):
        self.environment: Environment = environment
        self.plant = plant
        self.model = model.copy()
        self.model.solver.configuration.timeout = 1  # avoid getting stuck in an infinite loop of numerical instability when working with seeds
        self.time = start_time
        self.set_objective()
        self.used_fluxes = None

        # initial percentages to set constraints
        percentages = {
            "root_percent": 1,
            "stem_percent": 0,
            "leaf_percent": 0,
            "seed_percent": 0,
            "starch_percent": 0,
            "stomata": False,
            }

        self.update_constraints(percentages)
        self.init_bounds()

    def to_dict(self):
        pass

    def update_bounds(self, delta_t: int, percentages: dict):
        """
        Bounds are normalized to gram/gram*second
        """
        # update bounds: nitrate, water, photon, co2, starch
        # co2
        if percentages["stomata"]:
            self.set_bounds(CO2, (-1000, 1000))
        else:
            self.set_bounds(CO2, (-1000, 0))

        # starch
        # STARCH_OUT stays 1000, since the plant is allowed to produce it anytime
        if percentages["starch_percent"] > 0:
            self.set_bounds(STARCH_IN, (0, 0))
        else:
            upper_bound_starch_in = self.plant.calc_available_starch_in_mol_per_gram_and_time(
                percentage=percentages["starch_percent"],
                time_in_seconds=delta_t
                )
            self.set_bounds(STARCH_IN, (0, upper_bound_starch_in))

        # nitrate
        root_grid = self.plant.lsystem.root_grid
        nitrate_upper_bound_env_pool = self.environment.nitrate_grid.available_relative_mm(
            time_seconds=delta_t,
            g_root=self.plant.root_mass,
            v_max=Vmax,
            k_m=Km,
            root_grid=root_grid,
            )
        self.set_bounds(NITRATE, (-1000, nitrate_upper_bound_env_pool))

        # photon
        photon_upper_bound = (self.plant.leaf_mass * SLA_IN_SQUARE_METER_PER_GRAM  # m^2
                              * self.environment.micromol_photon_per_square_meter(self.time, self.time + delta_t)
                              ) / self.plant.leaf_mass  # g_organ -> normalize?
        self.set_bounds(PHOTON, (0, photon_upper_bound))

        # water
        water_upper_bound_plant_pool = (
            self.plant.calc_available_water_in_mol_per_gram_and_time(delta_t)
        )

        water_upper_bound_env_pool = self.environment.water_grid.available_absolute(
            root_grid=root_grid
            ) / (self.plant.root_mass * delta_t)

        transpiration_per_second_and_gram = self.plant.get_transpiration_in_micromol_per_second_and_gram()
        max_usable_water = max(
            water_upper_bound_plant_pool + water_upper_bound_env_pool - transpiration_per_second_and_gram, 0
            )

        self.set_bounds(WATER, (-1000, max_usable_water))

    def normalize_model(self):
        root_mass = self.plant.root_mass
        stem_mass = self.plant.stem_mass
        leaf_mass = self.plant.leaf_mass
        seed_mass = self.plant.seed_mass
        normalize(
            model=self.model,
            root=root_mass,
            stem=stem_mass,
            leaf=leaf_mass,
            seed=seed_mass,
            )

    def simulate(self, delta_t, percentages):
        # slim optimize best case
        self.update_bounds(delta_t, percentages)
        self.update_constraints(percentages)
        print(f"Simulation: \n"
              f"Inputs: \n"
              f"Water: {self.get_bounds(WATER)} \n"
              f"nitrate: {self.get_bounds(NITRATE)} \n"
              f"starch_in: {self.get_bounds(STARCH_IN)} with a pool of {self.plant.starch_pool} \n"
              f"co2: {self.get_bounds(CO2)} \n"
              )
        self.normalize_model()
        self.model.slim_optimize()

        water_flux = self.model.reactions.get_by_id(WATER).flux
        nitrate_flux = self.model.reactions.get_by_id(NITRATE).flux
        photon_flux = self.model.reactions.get_by_id(PHOTON).flux
        starch_in = self.model.reactions.get_by_id(STARCH_IN).flux
        co2 = self.model.reactions.get_by_id(CO2).flux

        water_used = max(0, water_flux / self.get_bounds(WATER)[1]) if self.get_bounds(WATER)[1] > 0 else 0
        nitrate_used = nitrate_flux / self.get_bounds(NITRATE)[1] if self.get_bounds(NITRATE)[1] > 0 else 0
        starch_in_used = starch_in / self.get_bounds(STARCH_IN)[1] if self.get_bounds(STARCH_IN)[1] > 0 else 0
        co2_used = co2 / self.get_bounds(CO2)[1] if self.get_bounds(CO2)[1] > 0 else 0
        photon_used = photon_flux / self.get_bounds(PHOTON)[1] if self.get_bounds(PHOTON)[1] > 0 else 0
        print(f"Percentage used of available: \n"
              f"water_used: {water_used} of pool: \n"
              f"nitrate_used: {nitrate_used} \n"
              f"starch_in_used: {starch_in_used} \n"
              f"co2_used: {co2_used} \n"
              f"photon_used: {photon_used} \n"
              )

        self.used_fluxes = {
            "water_used": water_used,
            "nitrate_used": nitrate_used,
            "starch_in_used": starch_in_used,
            "co2_used": co2_used,
            "photon_used": photon_used
            }

        root_flux = self.model.reactions.get_by_id(BIOMASS_ROOT).flux
        stem_flux = self.model.reactions.get_by_id(BIOMASS_STEM).flux
        leaf_flux = self.model.reactions.get_by_id(BIOMASS_LEAF).flux
        seed_flux = self.model.reactions.get_by_id(BIOMASS_SEED).flux

        starch_out_flux = self.model.reactions.get_by_id(STARCH_OUT).flux
        starch_in_flux = self.model.reactions.get_by_id(STARCH_IN).flux

        co2_flux = self.model.reactions.get_by_id(CO2).flux

        print(f"Output: \n"
              f"water_flux: {water_flux} \n"
              f"nitrate_flux: {nitrate_flux} \n"
              f"root_flux: {root_flux} \n"
              f"stem_flux: {stem_flux} \n"
              f"leaf_flux: {leaf_flux} \n"
              f"seed_flux: {seed_flux} \n"
              f"starch_out_flux: {starch_out_flux} \n"
              f"starch_in_flux: {starch_in_flux} \n"
              )
        self.update_plant(delta_t, percentages["stomata"], root_flux, stem_flux, leaf_flux, seed_flux, starch_out_flux,
                          starch_in_flux, co2_flux)

        water_per_second = water_flux * self.plant.root_mass
        nitrate_per_second = nitrate_flux * self.plant.root_mass
        self.update_environment(delta_t, water_per_second, nitrate_per_second)

        self.time += delta_t

    def update_environment(self, delta_t, water_per_second, nitrate_per_second):
        # -> drain from ground, else take from pool -> try to fill pool
        root_grid = self.plant.lsystem.root_grid

        # update water
        water_intake = water_per_second * delta_t  # solution.fluxes[WATER] * delta_t * self.plant.root_biomass
        water_upper_bound_env_pool = self.environment.water_grid.available_absolute(
            root_grid=root_grid
            )


        used_water = water_intake + self.plant.get_transpiration_in_micromol(delta_t=delta_t)

        print(f"SOIL_AVAILABLE: {water_upper_bound_env_pool},\n"
              f"WATER IN PLANT: {self.plant.water_pool}, \n"
              f"WATER NEEDED: {used_water}\n"
              f"PLANT NEEDS: {water_intake}\n"
              f"TRANSPIRATION: {self.plant.get_transpiration_in_micromol(delta_t=delta_t)}")

        if used_water > water_upper_bound_env_pool:
            taken_from_internal_pool = used_water - water_upper_bound_env_pool
            if self.plant.water_pool - taken_from_internal_pool < 0:
                taken_from_internal_pool -= self.plant.water_pool
                self.plant.water_pool = 0
            else:
                self.plant.water_pool -= taken_from_internal_pool
            used_water -= taken_from_internal_pool

        self.environment.water_grid.drain(amount=used_water, root_grid=root_grid)
        missing_water = self.plant.max_water_pool - self.plant.water_pool
        available_water = self.environment.water_grid.available_absolute(
            root_grid=root_grid
            )
        diff = min(missing_water, available_water)
        self.environment.water_grid.drain(amount=diff, root_grid=root_grid)
        self.plant.water_pool += diff

        print(f"AFTER WATER CALCS \n"
              f"SOIL_AVAILABLE: {water_upper_bound_env_pool},\n"
              f"WATER IN PLANT: {self.plant.water_pool}, \n"
              f"WATER NEEDED: {used_water}\n"
              f"PLANT NEEDS: {water_intake}\n"
              f"TRANSPIRATION: {self.plant.get_transpiration_in_micromol(delta_t=delta_t)}")

        # update nitrate
        nitrate_intake = nitrate_per_second * delta_t  # solution.fluxes[NITRATE] * delta_t * self.plant.root_biomass
        self.environment.nitrate_grid.drain(amount=nitrate_intake, root_grid=root_grid)

    def update_plant(self, delta_t, stomata_open, root_flux, stem_flux, leaf_flux, seed_flux, starch_out_flux,
                     starch_in_flux, co2_flux):
        # update max pools based on mass
        weather_state = self.environment.weather.get_weather_state(int(self.time / 3600))
        self.plant.update_transpiration(
            co2_uptake_in_micromol_per_second_and_gram=co2_flux,
            stomata_open=stomata_open,
            weather_state=weather_state,
            )
        self.plant.update_masses(delta_t, root_flux, stem_flux, leaf_flux, seed_flux, starch_out_flux, starch_in_flux)
        self.plant.update_max_water_pool()

    def init_bounds(self):
        self.set_bounds(WATER, (-1000, 1000))
        self.set_bounds(NITRATE, (0, 1000))
        self.set_bounds(PHOTON, (0, 0))
        self.set_bounds(CO2, (-1000, 0))
        self.set_bounds(STARCH_OUT, (0, 1000))
        self.set_bounds(STARCH_IN, (0, 0))

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

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

    def update_constraints(self, percentages):
        constraint_starch_percentage = max(percentages["starch_percent"], 0)

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
            float(percentages["root_percent"]),
            float(percentages["stem_percent"]),
            float(percentages["leaf_percent"]),
            float(percentages["seed_percent"]),
            float(constraint_starch_percentage),
            ]

        mass_organ = [
            self.plant.root_mass,
            self.plant.stem_mass,
            self.plant.leaf_mass,
            self.plant.seed_mass,
            self.plant.stem_mass,
            ]

        n_reactions = len(reactions)
        cons = []

        for i in range(0, n_reactions):
            reaction = reactions[i]

            if percentage[i] == 0:
                # cannot transfer molecule into pool
                bounds = (0, 0)
                reaction.bounds = bounds

                # skip iteration since no constraint needs to be set
                # since the bounds already take care of setting reaction to 0
            else:
                # it's possible to transfer molecule into pool
                # => set bounds in a way that molecule can be exported
                bounds = (0, 1000)
                reaction.bounds = bounds

            for j in range(i + 1, n_reactions):
                name = f"{names[i]}_and_{names[j]}"

                # check for old constraint and remove them
                old_cons = self.model.constraints.get(name)
                if old_cons is not None:
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

                    cons.append(constraint)

        if cons:
            self.model.add_cons_vars(cons)
