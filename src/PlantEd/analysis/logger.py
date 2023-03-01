import os
from datetime import datetime
import csv

class Log():
    def __init__(self):
        self.file = open('logfile.csv', 'w')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["leaf_rate", "stem_rate", "root_rate", "sr", "time", "speed", "water", "nitrate",
                              "leaf_mass", "stem_mass", "root_mass", "starch_mass"])

        self.model_file = open('model_logs.csv', 'w')
        self.model_writer = csv.writer(self.model_file)
        self.model_writer.writerow(["Time", "", "","Intake", "Mikromol/Second", "", "", "Masses", "gramm DW",
                                    "", "", "Pools", "Mikromol", "", "Rates",
                                    "MirkoMol/Second", "", ""])
        self.model_writer.writerow(["Days", "Hours", "Minutes","Water_in", "Nitrate_in", "Starch_in", "Photon_in", "Leaf_mass", "Stem_mass",
                                    "Root_mass", "Seed_mass", "Water_pool", "Starch_pool", "Nitrate_pool", "Leaf_rate",
                                    "Stem_rate", "Root_rate", "Seed_rate"])
    def close_file(self):
        self.file.close()

    def append_row(self, leaf_rate, stem_rate, root_rate, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass):
        self.writer.writerow([leaf_rate, stem_rate, root_rate, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass])

    def append_model_row(self, days, hours, minutes,water_in, nitrate_in, starch_in, photon_in, leaf_mass, stem_mass,root_mass, seed_mass,
                         water_pool, starch_pool, nitrate_pool, leaf_rate, stem_rate, root_rate, seed_rate):
        self.model_writer.writerow(
            [days, hours, minutes, water_in, nitrate_in, starch_in, photon_in, leaf_mass, stem_mass, root_mass, seed_mass, water_pool,
             starch_pool, nitrate_pool, leaf_rate, stem_rate, root_rate, seed_rate]
        )

    def close_model_file(self):
        self.model_file.close()