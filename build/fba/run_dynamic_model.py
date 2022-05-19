from dynamic_model import DynamicModel


class Plant():
    def __init__(self):
        self.biomass = 1
        self.model = DynamicModel(self.get_biomass)
        self.model.activate_starch_resource()

    def update(self, i):
        if i % 10 == 0:
            self.model.calc_growth_rate()
            self.model.update(self.biomass, 0, 1)
            #gr, sr, si = self.model.get_rates()
            self.biomass += gr * self.biomass
            print(self.biomass, gr, sr, si, self.biomass/2*30)
        if i == 0 or i == 24*10*3-1:
            print(self.model.model.summary())


    def get_biomass(self):
        return self.biomass

def main():
    plant = Plant()
    # days first
    for i in range(0,24*10*3):
        plant.update(i)

if __name__ == "__main__":
    main()