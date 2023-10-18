import json
import numpy as np

from PlantEd_Server.constants import PLANT_POS, START_LEAF_BIOMASS_GRAM, START_STEM_BIOMASS_GRAM, \
    START_ROOT_BIOMASS_GRAM, START_SEED_BIOMASS_GRAM
from PlantEd_Server.server.lsystem import LSystem
from PlantEd_Server.constants import MAX_WATER_POOL_PER_GRAMM, water_concentration_at_temp, \
    PERCENT_OF_POOL_USABLE_PER_SIMULATION_STEP, PERCENT_OF_MAX_POOL_USABLE_PER_SIMULATION_STEP, \
    MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT


class Plant:
    def __init__(self, ground_grid_resolution):
        self.leaf_biomass = START_LEAF_BIOMASS_GRAM
        self.stem_biomass = START_STEM_BIOMASS_GRAM
        self.root_biomass = START_ROOT_BIOMASS_GRAM
        self.seed_biomass = START_SEED_BIOMASS_GRAM
        self.max_starch_pool = (self.get_total_plant_mass() * MIMROMOL_STARCH_PER_GRAM_DRY_WEIGHT)
        self.starch_pool = self.max_starch_pool  # mikromol
        self.max_water_pool = MAX_WATER_POOL_PER_GRAMM * self.get_total_plant_mass()
        self.water_pool = self.max_water_pool
        self.transpiration_factor = 0
        self.transpiration = 0

        self.root: LSystem = LSystem(
            root_grid=np.zeros(
                ground_grid_resolution,
            ),  # same resolution as environment grids
            water_grid_pos=(0, 900),  # hardcoded at ui [game.py 310]
        )
        self.root.create_new_first_letter(dir=(0, 1), pos=PLANT_POS, mass=self.root_biomass)

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

        dic = {"leaf_biomass": self.leaf_biomass,
               "stem_biomass": self.stem_biomass,
               "root_biomass": self.root_biomass,
               "seed_biomass": self.seed_biomass,
               "starch_pool": self.starch_pool,
               "max_starch_pool": self.max_starch_pool,
               "root": self.root.to_dict(),
               "water_pool": self.water_pool,
               "max_water_pool": self.max_water_pool,
               }

        return dic

    def update(self, delta_t):
        # {'directions': [{'dist': 671.7387885182752, 'dir': [648.0, 132.0]}]}
        self.root.update(self.root_biomass)

    def create_new_root(self, buy_new_root):
        directions = buy_new_root["directions"]
        for direction in directions:
            self.root.create_new_first_letter(dir=direction,
                                              pos=PLANT_POS,
                                              mass=self.root_biomass,
                                              )
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

        self.root_biomass += (root_flux * delta_t * self.root_biomass)
        self.stem_biomass += (stem_flux * delta_t * self.stem_biomass)
        self.leaf_biomass += (leaf_flux * delta_t * self.leaf_biomass)
        self.seed_biomass += (seed_flux * delta_t * self.seed_biomass)
        self.starch_pool -= (starch_in_flux * delta_t * self.stem_biomass)
        self.starch_pool += (starch_out_flux * delta_t * self.stem_biomass)

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
                    self.root_biomass * time_in_seconds
            )
        except ZeroDivisionError as e:
            raise ValueError(
                f"Either the given time ({time_in_seconds})or the organic "
                f"mass ({self.root_biomass}) are 0. "
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
        return self.transpiration * self.leaf_biomass * delta_t

    def get_total_plant_mass(self):
        return self.leaf_biomass + self.stem_biomass + self.root_biomass + self.seed_biomass
