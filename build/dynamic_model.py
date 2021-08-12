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

        # define init pool and rates in JSON or CONFIG
        self.nitrate_pool = 0
        self.water_pool = 0
        self.starch_pool = 0

        self.max_nitrate_intake_low = 0.0012    # based on paper
        self.max_nitrate_intake_high = 0.05     # based on paper
        # copies of intake rates to drain form pools
        self.nitrate_intake = 0                 # Michaelis–Menten equation: gDW(root) Vmax ~ 0.00336 mol g DW−1 day−1
        #self.photon_intake = 0                  # 300micromol /m2 s * PLA(gDW * slope)
        self.water_intake = 0
        self.starch_intake = 0

        self.starch_rate = 0
        self.biomass_rate = 0

    # set atp constraints, constrain nitrate intake to low/high
    def init_constraints(self):
        pass

    def calc_growth_rate(self):
        # calc current objective rate
        solution = self.model.optimize()
        # update bounds
        if self.model.objective == BIOMASS:
            self.biomass_rate = solution.objective_value
        elif self.model.objective == STARCH_OUT:
            self.starch_rate = solution.objective_value
        self.water_intake = self.get_flux(WATER)
        self.nitrate_intake = self.get_flux(NITRATE)
        self.starch_intake = self.get_flux(STARCH_IN)

    def get_flux(self, reaction):
        return self.model.reactions.get_by_id(reaction).bounds

    def get_rate(self):
        if self.model.objective == BIOMASS:
            return self.biomass_rate
        elif self.model.objective == STARCH_OUT:
            return self.starch_rate
        else:
            return -1

    def set_bounds(self, reaction, bounds):
        self.model.reactions.get_by_id(reaction).bounds = bounds

    def set_objective(self, objective):
        if objective == BIOMASS:
            self.set_bounds(STARCH_OUT, (0, 0))
            self.model.objective = BIOMASS
        elif objective == STARCH_OUT:
            self.set_bounds(STARCH_OUT, (0, 1000))
            self.model.objective = STARCH_OUT

    def activate_starch_resource(self):
        self.use_starch = True
        self.set_bounds(STARCH_IN, (0, self.starch_rate))

    def deactivate_starch_resource(self):
        self.use_starch = False
        self.set_bounds(STARCH_IN, (0, 0))

    def update_pools(self):
        if self.use_starch:
            self.starch_pool -= self.starch_intake
        self.nitrate_pool -= self.nitrate_intake
        self.water_pool -= self.water_intake