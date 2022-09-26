import cobra
import config
import os
from fba.helpers import (
    autotroph,
    heterotroph,
    update_objective,
    create_objective,
    get_ndaph_atp
)


# states for objective
BIOMASS = "AraCore_Biomass_tx_leaf"
STARCH_OUT = "Starch_out_tx_leaf"
STARCH_IN = "Starch_in_tx_root"

# intake reaction names
NITRATE = "Nitrate_tx_root"
WATER = "H2O_tx_root"
PHOTON = "Photon_tx_leaf"
CO2 = "CO2_tx_leaf"

# mol
Vmax = 0.8
max_nitrate_pool_low = 10
max_nitrate_pool_high = 50
Km = 4

MAX_WATER_POOL = 10000
MAX_WATER_POOL_CONSUMPTION = 1

# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(self, gametime, water_grid, log=None, plant_mass=None, model=cobra.io.read_sbml_model("fba/PlantEd_model.sbml")):
        self.model = model
        self.gametime = gametime
        self.water_grid = water_grid
        self.log = log
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
        self.temp = 20 # degree ceclsius
             # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0                 # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        self.photon_intake = 0                  # 300micromol /m2 s * PLA(gDW * slope)
        self.water_intake = 0
        self.transpiration_factor = 0
        self.co2_intake = 0
        self.starch_intake = 0                  # actual starch consumption
        self.starch_intake_max = 0.01              # upper bound /h ingame
        self.percentages_sum = 0

        # growth rates for each objective
        self.root_rate = 0
        self.stem_rate = 0
        self.leaf_rate = 0
        self.starch_rate = 0
        self.percentages = [0,0,0,0]
        self.init_constraints()
        self.calc_growth_rate(0.1,0.1,1,0.1)

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.nitrate_pool = max_nitrate_pool_low
        self.water_pool = self.max_water_pool
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(0.1)))
        self.set_bounds(PHOTON, (0, 0))
        self.set_bounds(STARCH_OUT, (0, 1000))
        self.set_bounds(STARCH_IN, (0, 0))

        # Literature ATP NADPH: 7.27 and 2.56 mmol gDW−1 day−1
        atp = 0.00727 /24
        nadhp = 0.00256 /24

    def calc_growth_rate(self, leaf_percent, stem_percent, root_percent, starch_percent):
        new_percentages = [leaf_percent, stem_percent, root_percent, starch_percent]
        for i in range(0, len(self.percentages)):
            if self.percentages[i] != new_percentages[i]:
                update_objective(self.model, root_percent, stem_percent, leaf_percent, starch_percent)
                self.percentages =  new_percentages
                break
        solution = self.model.optimize()
        gamespeed = self.gametime.GAMESPEED

        # calc_rates 1/s
        self.root_rate = (solution.fluxes.get("AraCore_Biomass_tx_root"))
        self.stem_rate = (solution.fluxes.get("AraCore_Biomass_tx_stem"))
        self.leaf_rate = (solution.fluxes.get("AraCore_Biomass_tx_leaf"))
        self.starch_rate = (solution.fluxes.get("Starch_out_tx_stem"))

        # 1/s
        self.water_intake = solution.fluxes[WATER]
        self.co2_intake = solution.fluxes[CO2]
        self.nitrate_intake = solution.fluxes[NITRATE]
        self.starch_intake =  solution.fluxes[STARCH_IN]
        self.photon_intake = solution.fluxes[PHOTON]


        if self.stomata_open:
            if solution.fluxes[CO2] > 0 and self.water_intake > 0:
                self.water_intake = self.water_intake + solution.fluxes[CO2]*self.transpiration_factor

        print("Root_prod: ", self.root_rate,
            "Starch_prod: ", self.starch_rate, " Starch_intake: ", self.starch_intake,
              " Water intake: ", self.water_intake, " Water_pool: ", self.water_pool, "Water_pool_consumption: ", self.water_intake_pool
        , "Nitrate_intake: ", self.nitrate_intake,
              " Factor: ", self.transpiration_factor, " CO2: ", solution.fluxes[CO2])

    def open_stomata(self):
        self.stomata_open = True
        self.set_bounds(CO2, (-1000,1000))

    def update_transpiration_factor(self):
        K = 291.18
        ticks = self.gametime.get_time()
        day = 1000 * 60 * 6
        hour = day / 24
        hours = (ticks % day) / hour
        RH = config.get_y(hours, config.humidity)
        T = config.get_y(hours, config.summer)
        In_Concentration = config.water_concentration_at_temp[int(T + 2)]
        Out_Concentration = config.water_concentration_at_temp[int(T)]
        self.transpiration_factor = K * (In_Concentration - Out_Concentration * RH)

    def close_stomata(self):
        self.stomata_open = False
        self.set_bounds(CO2, (0,0))

    def get_rates(self):
        gamespeed = self.gametime.GAMESPEED
        return (self.leaf_rate*gamespeed, self.stem_rate*gamespeed, self.root_rate*gamespeed, self.starch_rate*gamespeed, self.starch_intake*gamespeed)

    def get_actual_water_drain(self):
        return self.water_intake + self.water_intake_pool

    def get_photon_upper(self):
        return self.model.reactions.get_by_id(PHOTON).bounds[1]

    def get_nitrate_pool(self):
        return self.nitrate_pool

    def increase_nitrate_pool(self, amount):
        self.nitrate_pool += amount

    def get_nitrate_percentage(self):
        return self.nitrate_pool/max_nitrate_pool_low

    def get_nitrate_intake(self, mass):
        # Michaelis-Menten Kinetics
        # v = Vmax*S/Km+S, v=intake speed, Vmax=max Intake, Km=Where S that v=Vmax/2, S=Substrate Concentration
        # Literature: Vmax ~ 0.00336 mol g DW−1 day−1, KM = 0.4 mmol,  S = 50 mmol and 1.2 mmol (high, low)
        # day --> sec (240 real sec = 1 ingame sec)
        return max(((Vmax*self.nitrate_pool)/(Km+self.nitrate_pool))*mass/24,0) #hour

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def increase_nitrate(self, amount):
        self.nitrate_delta_amount = amount

    def activate_starch_resource(self):
        self.use_starch = True
        self.set_bounds(STARCH_IN, (0, self.starch_intake_max))

    def deactivate_starch_resource(self):
        self.use_starch = False
        self.set_bounds(STARCH_IN, (0, 0))

    def update(self, dt, root_mass, PLA, sun_intensity, max_water_drain):
        self.update_bounds(root_mass, PLA*sun_intensity, max_water_drain)
        self.update_pools(dt, max_water_drain)
        self.update_transpiration_factor()

    def update_pools(self,dt, max_water_drain):
        gamespeed = self.gametime.GAMESPEED
        #self.water_intake_pool = 0  # reset to not drain for no reason

        # Todo make work
        # if all is zero but pool not and photosynthesis, set bounds back to max

        # max water drain tells how much is there to take
        # if last intake was higher, drain differenz from pool
        # if last intake was lower, drain normally -> if water pool is lower than max, drain more, put diff in pool

        #print(max_water_drain, self.water_intake)

        # take more water in, if possible and pool not full

        if self.water_pool < MAX_WATER_POOL:
            if self.water_intake < max_water_drain:
                self.water_intake_pool = 0
                # excess has to be negative to get added to pool
                excess =  self.water_intake - max_water_drain
                if excess < MAX_WATER_POOL_CONSUMPTION:
                    self.water_intake_pool = excess
                else:
                    self.water_intake_pool = MAX_WATER_POOL_CONSUMPTION
        self.water_pool -= self.water_intake_pool * dt * gamespeed


        self.nitrate_pool -= self.nitrate_intake * dt * gamespeed
        if self.nitrate_pool < 0:
            self.nitrate_pool = 0
        # starch gets handled separatly in Organ Starch
        if self.nitrate_delta_amount > 0:
            self.nitrate_pool += 0.1 * gamespeed * dt
            self.nitrate_delta_amount -= 0.1 * gamespeed * dt

    def update_bounds(self, root_mass, photon_in, max_water_drain):
        # update photon intake based on sun_intensity
        # update nitrate inteake based on Substrate Concentration
        # update water based on grid
        # co2? maybe later in dev
        self.set_bounds(NITRATE,(0,self.get_nitrate_intake(root_mass)))

        # take from pool, if no enough
        #print(max_water_drain, MAX_WATER_POOL_CONSUMPTION-max_water_drain)
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

        self.set_bounds(WATER, (-1000,intake))
        self.set_bounds(PHOTON,(0,photon_in))