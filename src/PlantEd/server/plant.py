import json
from collections import namedtuple

import numpy as np

from PlantEd.constants import PLANT_POS, START_LEAF_BIOMASS_GRAM, START_STEM_BIOMASS_GRAM, \
    START_ROOT_BIOMASS_GRAM, START_SEED_BIOMASS_GRAM, MAXIMUM_LEAF_BIOMASS_GRAM, MAXIMUM_ROOT_BIOMASS_GRAM, \
    MAXIMUM_STEM_BIOMASS_GRAM, MAXIMUM_SEED_BIOMASS_GRAM, BRANCH_MASS_PER_SPOT, BRANCH_SPOTS_BASE, BRANCH_SPOTS_TOTAL
from PlantEd.server.lsystem import LSystem
from PlantEd.constants import MAX_WATER_POOL_PER_GRAMM, water_concentration_at_temp, \
    PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP, PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP, \
    MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT


class Leaf:
    def __init__(self, id, mass):
        self.id = id
        self.mass = mass


class Branch:
    def __init__(self, id, mass, spots):
        self.id = id
        self.mass = mass
        self.spots = spots


class Root:
    def __init__(self, id, mass):
        self.id = id
        self.mass = mass


class Seed:
    def __init__(self, id, mass):
        self.id = id
        self.mass = mass


class Plant:
    def __init__(self, ground_grid_resolution):
        self.leafs: list[Leaf] = [Leaf(0, START_LEAF_BIOMASS_GRAM)]
        self.branches: list[Branch] = [Branch(0, START_STEM_BIOMASS_GRAM, BRANCH_SPOTS_BASE)]
        self.roots: list[Root] = [Root(0, START_ROOT_BIOMASS_GRAM)]
        self.seeds: list[Seed] = []
        self.seed_mass_base = START_SEED_BIOMASS_GRAM
        self.lsystem: LSystem = LSystem(
            root_grid=np.zeros(
                ground_grid_resolution,
            ),  # same resolution as environment grids
            water_grid_pos=(0, 900),  # hardcoded at ui [game.py 310]
        )
        self.lsystem.create_new_first_letter((0, 1), PLANT_POS, self.get_total_plant_mass())
        self.lsystem.update(self.root_mass)

        self.max_starch_pool = (self.get_total_plant_mass() * MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT)
        self.starch_pool = self.max_starch_pool  # mikromol
        self.max_water_pool = MAX_WATER_POOL_PER_GRAMM * self.get_total_plant_mass()
        self.water_pool = self.max_water_pool
        self.transpiration_factor = 0
        self.transpiration = 0

    ######################################################################
    # LEAF OPERATIONS
    ######################################################################
    @property
    def leaf_mass(self):
        leaf_mass = sum([leaf.mass for leaf in self.leafs])
        return leaf_mass

    def update_leaf_mass(self, delta_leaf_mass):
        if delta_leaf_mass <= 0 or len(self.leafs) <= 0:
            return
        growable_leafs = []
        for leaf in self.leafs:
            if leaf.mass < MAXIMUM_LEAF_BIOMASS_GRAM:
                growable_leafs.append(leaf)
        n_leafs_to_grow = len(growable_leafs)
        if n_leafs_to_grow <= 0:
            return
        delta_each_leaf = delta_leaf_mass / n_leafs_to_grow
        growable_leafs.sort(key=lambda leaf: leaf.mass)
        for leaf in growable_leafs:
            if leaf.mass + delta_each_leaf > MAXIMUM_LEAF_BIOMASS_GRAM:
                leaf.mass = MAXIMUM_LEAF_BIOMASS_GRAM
                overflow_mass = MAXIMUM_LEAF_BIOMASS_GRAM - leaf.mass + delta_each_leaf
                n_leafs_to_grow -= 1
                if n_leafs_to_grow <= 0:
                    break
                delta_each_leaf = (delta_leaf_mass + overflow_mass) / n_leafs_to_grow
            else:
                leaf.mass += delta_each_leaf

    def get_leaf_mass_to_grow(self) -> float:
        leaf_mass_to_grow = MAXIMUM_LEAF_BIOMASS_GRAM*len(self.leafs) - self.leaf_mass
        return leaf_mass_to_grow

    def create_new_leaf(self):
        id: int = len(self.leafs)
        self.leafs.append(Leaf(id, 0))

    ######################################################################
    # STEM OPERATIONS
    ######################################################################
    @property
    def stem_mass(self):
        stem_mass = sum([branch.mass for branch in self.branches])
        return stem_mass

    def update_stem_mass(self, delta_stem_mass):
        if delta_stem_mass <= 0 or len(self.branches) <= 0:
            return
        growable_branches = []
        for branch in self.branches:
            if branch.mass < MAXIMUM_STEM_BIOMASS_GRAM:
                growable_branches.append(branch)
        n_branches_to_grow = len(growable_branches)
        if n_branches_to_grow <= 0:
            return
        delta_each_branch = delta_stem_mass / n_branches_to_grow
        growable_branches.sort(key=lambda branch: branch.mass)
        for branch in growable_branches:
            if branch.mass + delta_each_branch > MAXIMUM_STEM_BIOMASS_GRAM:
                branch.mass = MAXIMUM_STEM_BIOMASS_GRAM
                overflow_mass = MAXIMUM_STEM_BIOMASS_GRAM - branch.mass + delta_each_branch
                n_branches_to_grow -= 1
                if n_branches_to_grow <= 0:
                    break
                delta_each_branch = (delta_stem_mass + overflow_mass) / n_branches_to_grow
            else:
                branch.mass += delta_each_branch
            if branch.spots < (branch.mass / BRANCH_MASS_PER_SPOT + BRANCH_SPOTS_BASE) and branch.spots <= BRANCH_SPOTS_TOTAL:
                branch.spots += 1

    def get_free_spots(self) -> int:
        spots = sum(branch.spots for branch in self.branches)
        spots_occupied = sum([len(self.branches), len(self.leafs), len(self.seeds)]) - 1    # for the starting seed -> doesnt count, bu has to be in for the model
        return spots - spots_occupied     # -1 for the first branch

    def get_stem_mass_to_grow(self) -> float:
        return MAXIMUM_STEM_BIOMASS_GRAM*len(self.branches) - self.stem_mass

    def create_new_branch(self):
        id: int = len(self.branches)
        self.branches.append(Branch(id, 0, BRANCH_SPOTS_BASE))

    ######################################################################
    # ROOT OPERATIONS
    ######################################################################
    @property
    def root_mass(self):
        root_mass = sum([root.mass for root in self.roots])
        return root_mass

    def update_root_mass(self, delta_root_mass):
        if delta_root_mass <= 0 or len(self.roots) <= 0:
            return
        growable_roots = []
        for root in self.roots:
            if root.mass < MAXIMUM_ROOT_BIOMASS_GRAM:
                growable_roots.append(root)
        n_roots_to_grow = len(growable_roots)
        if n_roots_to_grow <= 0:
            return
        delta_each_root = delta_root_mass / n_roots_to_grow
        growable_roots.sort(key=lambda root: root.mass)
        for root in growable_roots:
            if root.mass + delta_each_root > MAXIMUM_ROOT_BIOMASS_GRAM:
                root.mass = MAXIMUM_ROOT_BIOMASS_GRAM
                overflow_mass = MAXIMUM_ROOT_BIOMASS_GRAM - root.mass + delta_each_root
                n_roots_to_grow -= 1
                if n_roots_to_grow <= 0:
                    break
                delta_each_root = (delta_root_mass + overflow_mass) / n_roots_to_grow

            else:
                root.mass += delta_each_root

        for i, first_letter in enumerate(self.lsystem.first_letters):
            self.lsystem.apply_rules(first_letter, self.roots[i].mass)
        self.lsystem.calc_positions()

    def get_root_mass_to_grow(self) -> float:
        return MAXIMUM_ROOT_BIOMASS_GRAM*len(self.roots) - self.root_mass

    def create_new_root(self, target):
        self.lsystem.create_new_first_letter(dir=target,
                                             pos=PLANT_POS,
                                             mass=self.root_mass,
                                             )

        #self.lsystem.create_new_first_letter(dir=(0, 1), pos=PLANT_POS, mass=self.root_mass)
        while len(self.lsystem.first_letters) > len(self.roots):
            id: int = len(self.roots)
            self.roots.append(Root(id, 0))

    ######################################################################
    # SEED OPERATIONS
    ######################################################################
    @property
    def seed_mass(self):
        seed_mass = sum([seed.mass for seed in self.seeds]) + self.seed_mass_base
        return seed_mass

    def update_seed_mass(self, delta_seed_mass):
        if delta_seed_mass <= 0 or len(self.seeds) <= 0:
            return
        growable_seeds = []
        for seed in self.seeds:
            if seed.mass < MAXIMUM_SEED_BIOMASS_GRAM:
                growable_seeds.append(seed)
        n_seeds_to_grow = len(growable_seeds)
        if n_seeds_to_grow <= 0:
            return
        delta_each_seed = delta_seed_mass / n_seeds_to_grow
        growable_seeds.sort(key=lambda seed: seed.mass)
        for seed in growable_seeds:
            if seed.mass + delta_each_seed > MAXIMUM_SEED_BIOMASS_GRAM:
                seed.mass = MAXIMUM_SEED_BIOMASS_GRAM
                overflow_mass = MAXIMUM_SEED_BIOMASS_GRAM - seed.mass + delta_each_seed
                n_seeds_to_grow -= 1
                if n_seeds_to_grow <= 0:
                    break
                delta_each_seed = (delta_seed_mass + overflow_mass) / n_seeds_to_grow
            else:
                seed.mass += delta_each_seed

    def get_seed_mass_to_grow(self) -> float:
        return MAXIMUM_SEED_BIOMASS_GRAM*len(self.seeds) - self.seed_mass

    def create_new_seed(self):
        id: int = len(self.seeds)
        self.seeds.append(Seed(id, 0))

    def to_json(self) -> str:
        """
        Function that returns the plant object encoded in json. Using the
        from_json function a new plant object can be created whose instance
        variables are identical to those of the original object.

        Returns: A JSON string that contains all instance variables
        of the Plant Object.

        """
        return json.dumps(self.to_dict())

    def to_dict(self):
        """
        Function that returns the plant object encoded as :py:class:`dict`.
        Using the :py:meth:`from_dict` method a new plant object can be
        created whose instance variables are identical to those of the
        original object.

        Returns: The instance variables of the :py:class:`Plant` object
        encoded as a :py:class:`dict`.

        """

        dic = {"leafs_biomass": [(leaf.id, leaf.mass) for leaf in self.leafs],
               "stems_biomass": [(branch.id, branch.mass, branch.spots) for branch in self.branches],
               "roots_biomass": self.root_mass,
               "seeds_biomass": [(seed.id, seed.mass) for seed in self.seeds],
               "starch_pool": self.starch_pool,
               "max_starch_pool": self.max_starch_pool,
               "root": self.lsystem.to_dict(),
               "water_pool": self.water_pool,
               "max_water_pool": self.max_water_pool,
               "open_spots": self.get_free_spots(),
               }

        return dic

    def update(self, delta_t):
        pass

        # update root lsystem
    def update_starch_max(self, max_pool):
        if self.starch_pool > max_pool:
            self.starch_pool = max_pool
        self.max_starch_pool = max_pool

    def update_masses(
            self,
            delta_t: float,
            root_flux: float,
            stem_flux: float,
            leaf_flux: float,
            seed_flux: float,
            starch_out_flux: float,
            starch_in_flux: float):

        self.update_root_mass(root_flux * delta_t * self.root_mass)
        self.update_stem_mass(stem_flux * delta_t * self.stem_mass)
        self.update_leaf_mass(leaf_flux * delta_t * self.leaf_mass)
        self.update_seed_mass(seed_flux * delta_t * self.seed_mass)
        self.starch_pool -= (starch_in_flux * delta_t * self.stem_mass)
        self.starch_pool += (starch_out_flux * delta_t * self.stem_mass)

        self.update_starch_max(MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT * self.get_total_plant_mass())

        '''print(f"root_mass: {self.root_biomass}\n"
              f"stem mass: {self.stem_biomass}\n"
              f"leaf mass: {self.leaf_biomass}\n"
              f"seed_mass: {self.seed_biomass}\n"
              f"starch_pool: {self.starch_pool} or starch_max: {self.max_starch_pool}")'''

    def calc_available_starch_in_mol_per_gram_and_time(
            self,
            percentage: float,
            time_in_seconds: float,
    ) -> float:
        """
        Method that calculates the maximum extractable starch from the pool.
        This is done on the basis of a time period and the mass of the
        organ that has access to this reservoir. The value calculated
        here corresponds to the `upper_bound` within a
        :py:class:`cobra.Reaction`.
        The unit is micromol / (second * gram_of_organ).
        Args:
            percentage: The slider value of starch consumption UI
            time_in_seconds: The time span over which the pool is accessed in
                seconds.

        Returns: Maximum usable starch in micromol / (second * gram).
        """

        # Pool usage factors (see constants.py)
        value = min(self.starch_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
                    self.max_starch_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP)

        try:
            value = value / (
                    self.root_mass * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({self.root_mass}) are 0. "
                f"Therefore, the available micromole per time and "
                f"gram cannot be calculated."
            ) from e

        value = value * (abs(percentage) / 100)
        #print(f"Available starch {value} from pool of {self.starch_pool} and a percentage of {percentage/100}")
        return value

    def calc_available_water_in_mol_per_gram_and_time(
            self,
            time_in_seconds: float,
    ) -> float:
        # Pool usage factors (see constants.py)
        value = min(
            self.water_pool * PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP,
            self.max_water_pool * PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP,
        )

        try:
            value = value / (self.get_total_plant_mass() * time_in_seconds)
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({self.get_total_plant_mass()}) are 0. "
                f"Therefore, the available µmole per time and "
                f"gram cannot be calculated."
            ) from e

        return value

    def update_transpiration(
        self,
        co2_uptake_in_micromol_per_second_and_gram,
        weather_state,
        stomata_open: bool,
    ):
        K = 291.18
        RH = weather_state.humidity
        T = weather_state.temperature

        In_Concentration = water_concentration_at_temp[int(T + 2)]
        Out_Concentration = water_concentration_at_temp[int(T)]
        new_transpiration_factor = K * (In_Concentration - Out_Concentration * RH / 100)

        transpiration_factor = new_transpiration_factor

        transpiration = 0
        if stomata_open:
            if co2_uptake_in_micromol_per_second_and_gram > 0:
                transpiration = (
                    co2_uptake_in_micromol_per_second_and_gram * transpiration_factor
                )
        self.transpiration = transpiration  # in seconds and 1 gram

    def update_max_water_pool(self):
        self.max_water_pool = MAX_WATER_POOL_PER_GRAMM * self.get_total_plant_mass()

    def get_transpiration_in_micromol(self, delta_t: int):
        return self.transpiration * self.leaf_mass * delta_t

    def get_transpiration_in_micromol_per_second_and_gram(self):
        return self.transpiration

    def get_total_plant_mass(self):
        return self.leaf_mass + self.stem_mass + self.root_mass + self.seed_mass


