import cobra

# states for objective
BIOMASS = "leaf_AraCore_Biomass_tx"
STARCH_OUT = "root_Starch_out_tx"
STARCH_IN = "root_Starch_in_tx"

# intake reaction names
NITRATE = "root_Nitrate_tx"
WATER = "root_H2O_tx"
PHOTON = "leaf_Photon_tx"

# mol
Vmax = 0.00336
max_nitrate_pool_low = 0.0012    # based on paper
max_nitrate_pool_high = 0.05
Km = 0.0004

# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(self, plant_mass=None, model=cobra.io.read_sbml_model("whole_plant.sbml")):
        self.model = model
        self.plant_mass = plant_mass
        self.use_starch = False
        # model.objective can be changed by this string, but not compared, workaround: self.objective
        self.objective = BIOMASS
        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.water_pool = 0
        self.max_water_pool = 0.1
        self.temp = 20 # degree ceclsius
             # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0                 # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        self.photon_intake = 0                  # 300micromol /m2 s * PLA(gDW * slope)
        self.water_intake = 0
        self.starch_intake = 0                  # actual starch consumption
        self.starch_intake_max = 10            # upper bound for init consumption

        # growth rates for each objective
        self.starch_rate = 0
        self.biomass_rate = 0

        self.init_constraints()
        self.calc_growth_rate()

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        self.nitrate_pool = max_nitrate_pool_low
        self.water_pool = 0.1
        self.set_bounds(NITRATE, (0, self.get_nitrate_intake(0.01)))
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
        # transporter

        # calc current objective rate
        # constraints to restrict transfer flows
        # 5g Root, (0,5) mol/h/g Nitrate -> 0.001g Stem, 1000 mol/h/g
        # vNitrateRoot * RootMass = vNitrateStem * StemMass
        #
        solution = self.model.optimize()
        # update bounds
        if self.objective == BIOMASS:
            self.biomass_rate = solution.objective_value/60/60*240 # make it every ingame second
            self.starch_rate = 0
        elif self.objective == STARCH_OUT:
            self.starch_rate = solution.objective_value/60/60*240 # make it every ingame second
            self.biomass_rate = 0
        # it does not mater what intake gets limited beforehand, after all intakes are needed for UI, Growth
        self.water_intake = solution.fluxes[WATER]#self.get_flux(WATER)
        self.nitrate_intake = solution.fluxes[NITRATE]#self.get_flux(NITRATE)
        self.starch_intake =  solution.fluxes[STARCH_IN]#self.get_flux(STARCH_IN)
        self.photon_intake = solution.fluxes[PHOTON]

    def get_rates(self):
        return (self.biomass_rate, self.starch_rate, self.starch_intake)

    def get_nitrate_pool(self):
        return self.nitrate_pool

    def increase_nitrate_pool(self, amount):
        self.nitrate_pool += amount

    def get_nitrate_intake(self, mass):
        # Michaelis-Menten Kinetics
        # v = Vmax*S/Km+S, v=intake speed, Vmax=max Intake, Km=Where S that v=Vmax/2, S=Substrate Concentration
        # Literature: Vmax ~ 0.00336 mol g DW−1 day−1, KM = 0.4 mmol,  S = 50 mmol and 1.2 mmol (high, low)
        # day --> sec (240 real sec = 1 ingame sec)
        return max(((Vmax*self.nitrate_pool)/(Km+self.nitrate_pool))*mass/23/60/60*240,0) #day

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

    def update(self, mass, PLA, sun_intensity):
        self.update_bounds(mass, PLA*sun_intensity)
        self.update_pools()
        self.calc_growth_rate()
        #print("biomass_rate: ", self.biomass_rate, "pools: ", self.nitrate_pool, mass, PLA, sun_intensity)

    def update_pools(self):
        self.nitrate_pool -= self.nitrate_intake
        self.water_pool -= self.water_intake
        # starch gets handled separatly in Organ Starch

    def update_bounds(self, mass, photon_in):
        # update photon intake based on sun_intensity
        # update nitrate inteake based on Substrate Concentration
        # update water, co2? maybe later in dev
        self.set_bounds(NITRATE,(0,self.get_nitrate_intake(mass)))
        self.set_bounds(PHOTON,(0,100))