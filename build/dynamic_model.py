import cobra
import config
import os


# states for objective
BIOMASS = "leaf_AraCore_Biomass_tx"
STARCH_OUT = "root_Starch_out_tx"
STARCH_IN = "root_Starch_in_tx"

# intake reaction names
NITRATE = "root_Nitrate_tx"
WATER = "root_H2O_tx"
PHOTON = "leaf_Photon_tx"

# mol
Vmax = 0.8
max_nitrate_pool_low = 10
max_nitrate_pool_high = 50
Km = 4

# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(self, gametime, log=None, plant_mass=None, model=cobra.io.read_sbml_model("whole_plant.sbml")):
        self.model = model
        self.gametime = gametime
        self.log = log
        self.plant_mass = plant_mass
        self.use_starch = False
        # model.objective can be changed by this string, but not compared, workaround: self.objective
        self.objective = BIOMASS
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
        self.starch_rate = 0
        self.biomass_rate = 0

        self.init_constraints()
        self.calc_growth_rate()

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.nitrate_pool = max_nitrate_pool_low
        self.water_pool = 1
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(0.1)))
        self.set_bounds(PHOTON, (0, 0))

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

    def calc_growth_rate(self):
        solution = self.model.optimize()
        gamespeed = self.gametime.GAMESPEED

        if self.objective == BIOMASS:
            self.biomass_rate = solution.objective_value/60/60*240*gamespeed# make it every ingame second
            self.starch_rate = 0
        elif self.objective == STARCH_OUT:
            # Todo find fix for low production
            # beware workaround just 10fold
            self.starch_rate = solution.objective_value/60/60*240*gamespeed# make it every ingame second
            self.biomass_rate = 0
        # it does not mater what intake gets limited beforehand, after all intakes are needed for UI, Growth

        # hourly rates
        self.water_intake = solution.fluxes[WATER]#self.get_flux(WATER)
        self.nitrate_intake = solution.fluxes[NITRATE]#self.get_flux(NITRATE)
        self.starch_intake =  solution.fluxes[STARCH_IN]#self.get_flux(STARCH_IN)
        self.photon_intake = solution.fluxes[PHOTON]

        if self.log:
            self.log.append_log(self.biomass_rate, self.starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, self.water_pool, self.nitrate_pool)

    def get_rates(self):
        return (self.biomass_rate, self.starch_rate, self.starch_intake/60/60*240*self.gametime.GAMESPEED)

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

    def get_rate(self):
        if self.objective == BIOMASS:
            return self.biomass_rate
        elif self.objective == STARCH_OUT:
            return self.starch_rate
        else:
            return -1

    def get_objective_is_biomass(self):
        if self.objective == BIOMASS:
            return True
        else:
            return False

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def get_bounds(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def set_objective(self, objective):
        if objective == BIOMASS:
            self.objective = BIOMASS
            self.set_bounds(STARCH_OUT, (0, 0))
            self.model.objective = BIOMASS
        elif objective == STARCH_OUT:
            self.objective = STARCH_OUT
            self.set_bounds(STARCH_OUT, (0, 1000))
            self.model.objective = STARCH_OUT
        self.calc_growth_rate()

    def activate_starch_resource(self):
        self.use_starch = True
        self.set_bounds(STARCH_IN, (0, self.starch_intake_max))
        self.calc_growth_rate()

    def deactivate_starch_resource(self):
        self.use_starch = False
        self.set_bounds(STARCH_IN, (0, 0))
        self.calc_growth_rate()

    def update(self, root_mass, PLA, sun_intensity, starch_percentage):
        self.update_bounds(root_mass, PLA*sun_intensity*50, starch_percentage)
        self.update_pools()
        #print("biomass_rate: ", self.biomass_rate, "pools: ", self.nitrate_pool, mass, PLA, sun_intensity)

    def update_pools(self):
        gamespeed = self.gametime.GAMESPEED
        #print(self.nitrate_pool, self.nitrate_intake/60/60*gamespeed, self.water_pool)
        self.nitrate_pool -= self.nitrate_intake/60/60*gamespeed
        if self.nitrate_pool > max_nitrate_pool_low:
            self.nitrate_pool = max_nitrate_pool_low
        if self.nitrate_pool < 0:
            self.nitrate_pool = 0.001
        self.water_pool -= self.water_intake/60/60*gamespeed
        if self.water_pool < 0:
            self.water_pool = 0
        # starch gets handled separatly in Organ Starch

    def update_bounds(self, root_mass, photon_in, starch_percenatage):
        # update photon intake based on sun_intensity
        # update nitrate inteake based on Substrate Concentration
        # update water, co2? maybe later in dev
        if self.use_starch:
            self.set_bounds(STARCH_IN, (0, self.starch_intake_max*starch_percenatage/100))
        self.set_bounds(NITRATE,(0,self.get_nitrate_intake(root_mass)*40))
        if self.water_pool <= 0:
            self.set_bounds(WATER, (0,0))
        else:
            self.set_bounds(WATER, (-1000,1000))
        self.set_bounds(PHOTON,(0,photon_in))
