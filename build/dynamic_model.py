import cobra

# states for objective
BIOMASS = "leaf_AraCore_Biomass_tx"
STARCH_OUT = "root_Starch_out_tx"
STARCH_IN = "root_Starch_in_tx"

# intake reaction names
NITRATE = "root_Nitrate_tx"
WATER = "root_H2O_tx"
PHOTON = "leaf_Photon_tx"

# interface and state holder of model --> dynamic wow
class DynamicModel:
    def __init__(self, model=cobra.io.read_sbml_model("whole_plant.sbml")):
        self.model = model
        self.use_starch = False
        # model.objective can be changed by this simple string, but not compared, workaround: self.objective
        self.objective = BIOMASS
        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.water_pool = 0
        self.max_nitrate_intake_low = 0.0012    # based on paper
        self.max_nitrate_intake_high = 0.05     # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0                 # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        #self.photon_intake = 0                  # 300micromol /m2 s * PLA(gDW * slope)
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
        self.set_bounds(NITRATE, (0, self.max_nitrate_intake_high))
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
        # calc current objective rate
        solution = self.model.optimize()
        # update bounds
        if self.objective == BIOMASS:
            self.biomass_rate = solution.objective_value
            self.starch_rate = 0
        elif self.objective == STARCH_OUT:
            self.starch_rate = solution.objective_value
            self.biomass_rate = 0
        self.water_intake = solution.fluxes[WATER]#self.get_flux(WATER)
        self.nitrate_intake = solution.fluxes[NITRATE]#self.get_flux(NITRATE)
        self.starch_intake =  solution.fluxes[STARCH_IN]#self.get_flux(STARCH_IN)
        #print(self.model.objective, self.get_rate(), "Water: ", self.water_intake, "N: ", self.nitrate_intake, "starch: ", self.starch_intake)

    def get_flux(self, reaction):
        pass
        #return self.model.reactions.get_by_id(reaction).flux

    def get_rates(self):
        return (self.biomass_rate, self.starch_rate, self.starch_intake)

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

    def update_pools(self):
        self.nitrate_pool -= self.nitrate_intake
        self.water_pool -= self.water_intake