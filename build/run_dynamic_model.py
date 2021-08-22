from dynamic_model import DynamicModel


class Plant():
    def __init__(self):
        self.biomass = 0.1
        self.model = DynamicModel(self.get_biomass)

    def update(self):
        self.model.calc_growth_rate()
        self.model.update(self.biomass, self.biomass/2, 1)
        gr, sr, si = self.model.get_rates()
        self.biomass += gr * self.biomass
        #print(self.biomass, gr, sr, si)

    def get_biomass(self):
        return self.biomass

def main():
    plant = Plant()
    # days first
    for i in range(0,100):
        plant.update()

if __name__ == "__main__":
    main()