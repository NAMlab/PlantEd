import csv


class Log:
    def __init__(self, path):
        self.model_file = open(path + "/model_logs.csv", "w")
        self.model_writer = csv.writer(self.model_file)
        self.model_writer.writerow(
            [
                "ticks",
                "leaf_mass",
                "stem_mass",
                "root_mass",
                "seed_mass",
                "water_pool_plant",
                "nitrate_pool_plant",
                "starch_pool",
                "temperature",
                "humidity",
                "precipitation",
            ]
        )

    def append_model_row(
        self,
            ticks,
            leaf_mass,
            stem_mass,
            root_mass,
            seed_mass,
            water_pool_plant,
            nitrate_pool_plant,
            starch_pool,
            temperature,
            humidity,
            precipitation
    ):
        self.model_writer.writerow(
            [
                ticks,
                leaf_mass,
                stem_mass,
                root_mass,
                seed_mass,
                water_pool_plant,
                nitrate_pool_plant,
                starch_pool,
                temperature,
                humidity,
                precipitation
            ]
        )

    def close_model_file(self):
        self.model_file.close()
