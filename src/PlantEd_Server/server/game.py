from PlantEd_Server.server.plant import Plant
from PlantEd_Server.server.dynamic_model import DynamicModel
from PlantEd_Server.server.environment import Environment


class Game:
    def __init__(self, start_time=0):
        self.time = start_time
        self.resolution = 600
        self.time_left_from_last_simulation = 0  # seconds
        self.plant = Plant(ground_grid_resolution=(20, 6))
        self.environment = Environment(self.time)
        self.model = DynamicModel(self.environment, self.plant)

    def reset(self):
        self.time = 0
        self.time_left_from_last_simulation = 0
        self.plant = Plant(ground_grid_resolution=(20, 6))
        self.environment = Environment(self.time)
        self.model = DynamicModel(self.environment, self.plant)

    # dt in seconds
    def update(self, delta_t, growth_percentages, increase_water_grid, increase_nitrate_grid, buy_new_root) -> dict:
        self.time += delta_t
        n_simulations = int((delta_t + self.time_left_from_last_simulation) / self.resolution)
        self.time_left_from_last_simulation = (delta_t + self.time_left_from_last_simulation) % self.resolution
        print(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} and time_left: {self.time_left_from_last_simulation}")
        # for n cycles
        # -----------------------
        # simulate environment
        # update model bounds
        # simulate model
        # update plant
        # -----------------------
        # send response dicts

        if increase_water_grid is not None:
            self.environment.increase_water_grid(increase_water_grid)

        if increase_nitrate_grid is not None:
            self.environment.increase_nitrate_grid(increase_nitrate_grid)

        if buy_new_root is not None:
            self.plant.create_new_root(buy_new_root)

        for i in range(n_simulations):
            self.plant.update(self.resolution)
            #print(f"updated plant res: {self.resolution}")
            self.environment.update(self.resolution)
            #print(f"updated env water: {increase_water_grid}, nitrate: {increase_nitrate_grid}")
            print(f"Percentages in game: {growth_percentages}")
            self.model.simulate(self.resolution, growth_percentages)
            #print(f"model simmed with percentages: {growth_percentages}")
        response = {
            "plant": self.plant.to_dict(),
            "environment": self.environment.to_dict()
        }
        return response
