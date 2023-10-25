from PlantEd.constants import MAX_DAYS
from PlantEd.server.plant import Plant
from PlantEd.server.dynamic_model import DynamicModel
from PlantEd.server.environment import Environment


class Game:
    def __init__(self, player_name, level_name, start_time=0, resolution=600, green_thumbs=20, seed=15):
        self.player_name = player_name
        self.level_name = level_name
        self.time = start_time
        self.resolution = resolution
        self.green_thumbs = 20
        # Todo include level selection
        self.time_left_from_last_simulation = 0  # seconds
        self.plant = Plant(ground_grid_resolution=(20, 6))
        self.environment = Environment(self.time, seed)
        self.model = DynamicModel(self.environment, self.plant)
        self.running = True

    def check_game_end(self):
        if self.time/(60*60*24) >= MAX_DAYS:
            self.running = False

    def check_sufficient_funds(self, action):
        return True

    def check_free_spot(self):
        return True if self.plant.get_free_branch_spots() > 0 else False

    # dt in seconds
    def update(self, message) -> dict:
        delta_t = message["delta_t"]
        growth_percentages = message["growth_percentages"]

        self.time += delta_t
        n_simulations = int((delta_t + self.time_left_from_last_simulation) / self.resolution)
        self.time_left_from_last_simulation = (delta_t + self.time_left_from_last_simulation) % self.resolution
        print(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} and time_left: {self.time_left_from_last_simulation}")

        for action in message["shop_actions"]:
            if action["buy_waterin_can"] is not None:
                self.environment.increase_water_grid(action["buy_watering_can"])
            if action["buy_nitrate"] is not None:
                self.environment.increase_nitrate_grid(action["buy_nitrate"])
            if action["buy_root"] is not None:
                self.plant.create_new_root(action["buy_root"])
            if action["buy_branch"] is not None:
                if self.check_free_spot():
                    self.plant.create_new_branch()
            if action["buy_leaf"] is not None:
                if self.check_free_spot():
                    self.plant.create_new_leaf()
            if action["buy_seed"] is not None:
                if self.check_free_spot():
                    self.plant.create_new_seed()

        for i in range(n_simulations):
            self.plant.update(self.resolution)
            self.environment.update(self.resolution)

            # Todo check percentages, build seed percentage
            percentages = {
                "leaf_percent": growth_percentages["leaf_percent"] if self.plant.get_leaf_mass_to_grow() > 0 else 0,
                "stem_percent": growth_percentages["stem_percent"] if self.plant.get_stem_mass_to_grow() > 0 else 0,
                "root_percent": growth_percentages["root_percent"] if self.plant.get_root_mass_to_grow() > 0 else 0,
                "seed_percent": sum([10 for seed in self.plant.seeds]),
                "starch_percent": growth_percentages["starch_percent"] if self.plant.get_leaf_mass_to_grow() > 0 else 0,
                "stomata": growth_percentages["stomata"]
            }

            self.model.simulate(self.resolution, percentages)
        game_state = {
            "running": self.running,
            "plant": self.plant.to_dict(),
            "environment": self.environment.to_dict()
        }
        return game_state
