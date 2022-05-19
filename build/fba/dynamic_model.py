import cobra
import config
import os
from fba.helpers import (
    autotroph,
    heterotroph,
    update_objective,
    create_objective,
    get_ndaph_atp,
    get_ngam,
)


# states for objective
BIOMASS = "AraCore_Biomass_tx_leaf"
STARCH_OUT = "Starch_out_tx_root"
STARCH_IN = "Starch_in_tx_root"

# intake reaction names
NITRATE = "Nitrate_tx_root"
WATER = "H2O_tx_root"
PHOTON = "Photon_tx_leaf"

# mol
Vmax = 0.8
max_nitrate_pool_low = 10
max_nitrate_pool_high = 50
Km = 4

# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(self, gametime, log=None, plant_mass=None, model=cobra.io.read_sbml_model("fba/PlantEd_model.sbml")):
        self.model = model
        self.gametime = gametime
        self.log = log
        self.plant_mass = plant_mass
        self.use_starch = False
        # model.objective can be changed by this string, but not compared, workaround: self.objective
        #self.objective = BIOMASS
        self.model.objective = create_objective(self.model)
        self.set_bounds(STARCH_OUT, (0, 1000))
        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.water_pool = 0
        self.max_water_pool = 10
        self.temp = 20 # degree ceclsius
             # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0                 # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        self.photon_intake = 0                  # 300micromol /m2 s * PLA(gDW * slope)
        self.water_intake = 0
        self.starch_intake = 0                  # actual starch consumption
        self.starch_intake_max = 1              # upper bound /h

        # growth rates for each objective
        self.root_rate = 0
        self.stem_rate = 0
        self.leaf_rate = 0
        self.starch_rate = 0

        self.init_constraints()
        self.calc_growth_rate(0.1,0.1,1,0.1)

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.nitrate_pool = max_nitrate_pool_low
        self.water_pool = 1
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(0.1)))
        self.set_bounds(PHOTON, (0, 100))

        '''forced_ATP = (
                0.0049 * self.model.reactions.get_by_id("leaf_Photon_tx").upper_bound
                + 2.7851
        )
        # This ensures that the sum of the three ATP are always forced_ATP
        multi_ATPase = self.model.problem.Constraint(
            (
                    self.model.reactions.get_by_id("leaf_ATPase_tx").flux_expression
                    + self.model.reactions.get_by_id("root_ATPase_tx").flux_expression
                    + self.model.reactions.get_by_id("stem_ATPase_tx").flux_expression
            ),
            ub=forced_ATP,
            lb=forced_ATP,
        )
        self.model.add_cons_vars([multi_ATPase])'''

        # Literature ATP NADPH: 7.27 and 2.56 mmol gDW−1 day−1
        atp = 0.00727 /24
        nadhp = 0.00256 /24

    def calc_growth_rate(self, leaf_percent, stem_percent, root_percent, starch_percent):
        update_objective(self.model, root_percent, stem_percent, leaf_percent, starch_percent)
        solution = self.model.optimize()
        gamespeed = self.gametime.GAMESPEED

        #self.biomass_rate = solution.objective_value / 60 / 60 * 240 * gamespeed  # make it every ingame second
        self.root_rate = solution.fluxes.get("AraCore_Biomass_tx_root")/ 60 / 60 * 240 * gamespeed
        self.stem_rate = solution.fluxes.get("AraCore_Biomass_tx_stem")/ 60 / 60 * 240 * gamespeed
        self.leaf_rate = solution.fluxes.get("AraCore_Biomass_tx_leaf")/ 60 / 60 * 240 * gamespeed
        self.starch_rate = solution.fluxes.get("Starch_out_tx_stem")/ 60 / 60 * 240 * gamespeed

        '''if self.objective == BIOMASS:
            self.biomass_rate = solution.objective_value/60/60*240*gamespeed# make it every ingame second
            #print(self.biomass_rate)
            self.starch_rate = 0
        elif self.objective == STARCH_OUT:
            # Todo find fix for low production
            # beware workaround just 10fold
            self.starch_rate = solution.objective_value/60/60*240*gamespeed# make it every ingame second
            self.biomass_rate = 0
        # it does not mater what intake gets limited beforehand, after all intakes are needed for UI, Growth'''

        # hourly rates
        self.water_intake = solution.fluxes[WATER]#self.get_flux(WATER)
        self.nitrate_intake = solution.fluxes[NITRATE]#self.get_flux(NITRATE)
        self.starch_intake =  solution.fluxes[STARCH_IN]#self.get_flux(STARCH_IN)
        self.photon_intake = solution.fluxes[PHOTON]

        #if self.log:
        #    self.log.append_log(self.biomass_rate, self.starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, self.water_pool, self.nitrate_pool)

    def get_rates(self):
        return (self.leaf_rate, self.stem_rate, self.root_rate, self.starch_rate, self.starch_intake/60/60*240*self.gametime.GAMESPEED)

    def get_pools(self):
        return (self.nitrate_pool, self.water_pool)

    def get_photon_upper(self):
        return self.model.reactions.get_by_id(PHOTON).bounds[1]

    def get_nitrate_pool(self):
        return self.nitrate_pool

    def increase_nitrate_pool(self, amount):
        if self.nitrate_pool >= max_nitrate_pool_low:
            self.nitrate_pool = max_nitrate_pool_low
            return
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

    def activate_starch_resource(self):
        self.use_starch = True
        self.set_bounds(STARCH_IN, (0, self.starch_intake_max))

    def deactivate_starch_resource(self):
        self.use_starch = False
        self.set_bounds(STARCH_IN, (0, 0))

    def update(self, root_mass, PLA, sun_intensity):
        self.update_bounds(root_mass, PLA*sun_intensity*50)
        self.update_pools()
        #print("biomass_rate: ", self.biomass_rate, "pools: ", self.nitrate_pool, mass, PLA, sun_intensity)

    def update_pools(self):
        gamespeed = self.gametime.GAMESPEED
        #print(self.nitrate_pool, self.nitrate_intake/60/60*gamespeed, self.water_pool)
        self.nitrate_pool -= self.nitrate_intake/60/60*gamespeed
        #if self.nitrate_pool > max_nitrate_pool_low:
        #    self.nitrate_pool = max_nitrate_pool_low
        if self.nitrate_pool < 0:
            self.nitrate_pool = 0
        self.water_pool -= self.water_intake/60/60*gamespeed
        if self.water_pool < 0:
            self.water_pool = 0
        # starch gets handled separatly in Organ Starch

    def update_bounds(self, root_mass, photon_in):
        # update photon intake based on sun_intensity
        # update nitrate inteake based on Substrate Concentration
        # update water, co2? maybe later in dev
        if self.use_starch:
            self.set_bounds(STARCH_IN, (0, self.starch_intake_max))
            #print(self.starch_intake_max, self.starch_intake)
        self.set_bounds(NITRATE,(0,self.get_nitrate_intake(root_mass)*40))
        if self.water_pool <= 0:
            self.set_bounds(WATER, (0,0))
        else:
            self.set_bounds(WATER, (-1000,1000))
        self.set_bounds(PHOTON,(0,photon_in))
        #self.set_bounds(PHOTON,(0,0))