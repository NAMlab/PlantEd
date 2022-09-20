import os
from datetime import datetime
import csv

class Log():
    def __init__(self):
        self.file = open('logfile.csv', 'w')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["leaf_rate", "stem_rate", "root_rate", "sr", "time", "speed", "water", "nitrate", "leaf_mass", "stem_mass", "root_mass", "starch_mass"])

    def close_file(self):
        self.file.close()

    def append_row(self, leaf_rate, stem_rate, root_rate, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass):
        self.writer.writerow([leaf_rate, stem_rate, root_rate, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass])