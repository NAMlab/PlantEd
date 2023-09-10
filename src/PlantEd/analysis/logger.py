import csv


class Log:
    def __init__(self, path):
        self.model_file = open(path + "/model_logs.csv", "w")
        self.model_writer = csv.writer(self.model_file)
        self.model_writer.writerow(
            [
                "ticks",
                "timeframe",
                "leaf_mass",
                "stem_mass",
                "root_mass",
                "seed_mass",
                "leaf_percentage",
                "stem_percentage",
                "root_percentage",
                "starch_percentage",
                "seed_percentage",
                "water_intake",
                "water_pool_plant",
                "water_available_env_abs",
                "nitrate_intake",
                "nitrate_pool_plant",
                "nitrate_available_env_abs",
                "nitrate_available_env_michalis_menten",
                "starch_intake",
                "starch_out",
                "starch_pool",
                "photon_intake",
                "co2_intake",
                "temperature",
                "humidity",
                "precipitation",
            ]
        )

    def append_model_row(
        self,
            ticks,
            timeframe,
            leaf_mass,
            stem_mass,
            root_mass,
            seed_mass,
            leaf_percentage,
            stem_percentage,
            root_percentage,
            starch_percentage,
            seed_percentage,
            water_intake,
            water_pool_plant,
            water_available_env_abs,
            nitrate_intake,
            nitrate_pool_plant,
            nitrate_available_env_abs,
            nitrate_available_env_michalis_menten,
            starch_intake,
            starch_out,
            starch_pool,
            photon_intake,
            co2_intake,
            temperature,
            humidity,
            precipitation,
    ):
        self.model_writer.writerow(
            [
                ticks,
                timeframe,
                leaf_mass,
                stem_mass,
                root_mass,
                seed_mass,
                leaf_percentage,
                stem_percentage,
                root_percentage,
                starch_percentage,
                seed_percentage,
                water_intake,
                water_pool_plant,
                water_available_env_abs,
                nitrate_intake,
                nitrate_pool_plant,
                nitrate_available_env_abs,
                nitrate_available_env_michalis_menten,
                starch_intake,
                starch_out,
                starch_pool,
                photon_intake,
                co2_intake,
                temperature,
                humidity,
                precipitation,
            ]
        )

    def close_model_file(self):
        self.model_file.close()
