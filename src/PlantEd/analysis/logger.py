import csv


class Log:
    def __init__(self, path):
        self.model_file = open(path + "/model_logs.csv", "w")
        self.model_writer = csv.writer(self.model_file)
        self.model_writer.writerow(
            [
                "Days",
                "Hours",
                "Minutes",
                "Leaf_percentage",
                " Stem_percentage",
                "Root_percentage",
                "Starch_percentage",
                "Seed_percentage",
                "Water_in",
                "Nitrate_in",
                "Starch_in",
                "Photon_in",
                "Leaf_mass",
                "Stem_mass",
                "Root_mass",
                "Seed_mass",
                "Water_pool",
                "Starch_pool",
                "Nitrate_pool",
                "Leaf_rate",
                "Stem_rate",
                "Root_rate",
                "Seed_rate",
            ]
        )

    def append_model_row(
        self,
        days,
        hours,
        minutes,
        leaf_percentage,
        stem_percentage,
        root_percentage,
        starch_percentage,
        seed_percentage,
        water_in,
        nitrate_in,
        starch_in,
        photon_in,
        leaf_mass,
        stem_mass,
        root_mass,
        seed_mass,
        water_pool,
        starch_pool,
        nitrate_pool,
        leaf_rate,
        stem_rate,
        root_rate,
        seed_rate,
    ):
        self.model_writer.writerow(
            [
                days,
                hours,
                minutes,
                leaf_percentage,
                stem_percentage,
                root_percentage,
                starch_percentage,
                seed_percentage,
                water_in,
                nitrate_in,
                starch_in,
                photon_in,
                leaf_mass,
                stem_mass,
                root_mass,
                seed_mass,
                water_pool,
                starch_pool,
                nitrate_pool,
                leaf_rate,
                stem_rate,
                root_rate,
                seed_rate,
            ]
        )

    def close_model_file(self):
        self.model_file.close()
