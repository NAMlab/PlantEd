from PlantEd.constants import MAX_DAYS, ROOT_COST, BRANCH_COST, LEAF_COST, FLOWER_COST, WATERING_CAN_COST, NITRATE_COST
from PlantEd.server.plant import Plant
from PlantEd.server.dynamic_model import DynamicModel
from PlantEd.server.environment import Environment
import logging

logger = logging.getLogger("server")
logging.basicConfig(level=logging.ERROR)


class Game:
    def __init__(self, player_name, level_name, start_time=0, resolution=3600, green_thumbs=20, seed=15):
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

    # dt in seconds
    def update(self, message) -> dict:
        self.check_game_end()
        delta_t = message["delta_t"]
        growth_percentages = message["growth_percentages"]

        self.time += delta_t
        n_simulations = int((delta_t + self.time_left_from_last_simulation) / self.resolution)
        self.time_left_from_last_simulation = (delta_t + self.time_left_from_last_simulation) % self.resolution
        print(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} and time_left: {self.time_left_from_last_simulation}")

        logger.debug(f"update game time: {self.time} with delta_T: {delta_t} and n_simulations: {n_simulations} "
                     f"and time_left: {self.time_left_from_last_simulation}")

        actions = [(action, content) for action, content in message["shop_actions"].items() if content is not None]
        for action in actions:
            logger.debug(f"shop actions from client: {action}")

        for action, content in message["shop_actions"].items():
            if content is not None:
                match action:
                    case ("buy_watering_can"):
                        if self.green_thumbs - WATERING_CAN_COST >= 0:
                            self.environment.increase_water_grid(content)
                    case "buy_nitrate":
                        if self.green_thumbs - NITRATE_COST >= 0:
                            self.environment.increase_nitrate_grid(content)
                    case "buy_root":
                        for target in content["directions"]:
                            if self.green_thumbs - ROOT_COST >= 0:
                                self.plant.create_new_root(target)
                                self.green_thumbs -= ROOT_COST
                    case "buy_branch":
                        for i in range(content):
                            if self.green_thumbs - BRANCH_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_branch()
                                    self.green_thumbs -= BRANCH_COST
                    case "buy_leaf":
                        for i in range(content):
                            if self.green_thumbs - LEAF_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_leaf()
                                    self.green_thumbs -= LEAF_COST
                    case "buy_seed":
                        for i in range(content):
                            if self.green_thumbs - FLOWER_COST >= 0:
                                if self.plant.get_free_spots() > 0:
                                    self.plant.create_new_seed()
                                    self.green_thumbs -= FLOWER_COST

        for i in range(n_simulations):
            self.plant.update(self.resolution)
            self.environment.update(self.resolution)

            # Todo check percentages, build seed percentage
            percentages = {
                "leaf_percent": growth_percentages["leaf_percent"] if self.plant.get_leaf_mass_to_grow() > 0 else 0,
                "stem_percent": growth_percentages["stem_percent"] if self.plant.get_stem_mass_to_grow() > 0 else 0,
                "root_percent": growth_percentages["root_percent"] if self.plant.get_root_mass_to_grow() > 0 else 0,
                "seed_percent": len(self.plant.seeds) * 10 if self.plant.get_seed_mass_to_grow() > 0 else 0,
                "starch_percent": growth_percentages["starch_percent"],
                "stomata": growth_percentages["stomata"]
            }
            print(percentages)
            sum_percentages = sum([value for key, value in percentages.items() if key != "starch_percent" and key != "stomata"]) + max(0,percentages["starch_percent"])
            if sum_percentages > 0:
                self.model.simulate(self.resolution, percentages)
        game_state = {
            "running": self.running,
            "plant": self.plant.to_dict(),
            "environment": self.environment.to_dict(),
            "green_thumbs": self.green_thumbs,
            "used_fluxes": self.model.used_fluxes,
            "gametime": self.time
        }
        if not self.running:
            pass
            # create scores
            # close logs
            # upload data
        return game_state
