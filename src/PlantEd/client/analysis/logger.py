import csv


class Log:
    def __init__(self, path):
        self.model_file = open(path + "/model_logs.csv", "w")
        self.model_writer = csv.writer(self.model_file)
        self.model_writer.writerow(
            [
                "time",
                "temperature",
                "sun_intensity",
                "humidity",
                "precipitation",
                "accessible_water",
                "accessible_nitrate",
                "leaf_biomass",
                "stem_biomass",
                "root_biomass",
                "seed_biomass",
                "starch_pool",
                "max_starch_pool",
                "water_pool",
                "max_water_pool",
                "leaf_percent",
                "stem_percent",
                "root_percent",
                "seed_percent",
                "starch_percent",
                "n_leaves",
                "n_stems",
                "n_roots",
                "n_seeds",
                "green_thumbs",
                "open_spots",
                "action"
            ]
        )

    def append_model_row(
        self,
            time,
            temperature,
            sun_intensity,
            humidity,
            precipitation,
            accessible_water,
            accessible_nitrate,
            leaf_biomass,
            stem_biomass,
            root_biomass,
            seed_biomass,
            starch_pool,
            max_starch_pool,
            water_pool,
            max_water_pool,
            leaf_percent,
            stem_percent,
            root_percent,
            seed_percent,
            starch_percent,
            n_leaves,
            n_stems,
            n_roots,
            n_seeds,
            green_thumbs,
            open_spots,
            action,
    ):
        self.model_writer.writerow(
            [
                time,
                temperature,
                sun_intensity,
                humidity,
                precipitation,
                accessible_water,
                accessible_nitrate,
                leaf_biomass,
                stem_biomass,
                root_biomass,
                seed_biomass,
                starch_pool,
                max_starch_pool,
                water_pool,
                max_water_pool,
                leaf_percent,
                stem_percent,
                root_percent,
                seed_percent,
                starch_percent,
                n_leaves,
                n_stems,
                n_roots,
                n_seeds,
                green_thumbs,
                open_spots,
                action,
            ]
        )

    def close_model_file(self):
        self.model_file.close()
