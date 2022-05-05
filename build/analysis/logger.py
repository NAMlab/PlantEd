import os
from datetime import datetime
import csv

class Log():
    def __init__(self):
        self.file = open('logfile.csv', 'w')
        self.writer = csv.writer(self.file)
        self.writer.writerow(["gr", "sr", "time", "speed", "water", "nitrate", "leaf_mass", "stem_mass", "root_mass", "starch_mass"])
        self.path_to_log = os.path.join(os.getcwd(), os.pardir)
        self.loglist = {'growth': [],
                        'gametime': [],
                        'gamespeed': [],
                        'water': [],
                        'nitrate': [],
                        'starch': [],
                        'leaf_mass': [],
                        'stem_mass': [],
                        'root_mass': [],
                        'starch_pool': [],}

    '''self.log.append_row(growth_rate, starch_rate, self.gametime.get_time(), self.gametime.GAMESPEED, water_pool,
                        nitrate_pool,
                        self.plant.organs[0].mass, self.plant.organs[1].mass, self.plant.organs[2].mass,
                        self.plant.organ_starch.mass)'''
    def close_file(self):
        self.file.close()

    def append_row(self, gr, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass):
        self.writer.writerow([gr, sr, time, speed, water, nitrate, leaf_mass, stem_mass, root_mass, starch_mass])

    def append_log(self, growth, starch, gametime, gamespeed, water, nitrate):
        self.loglist['growth'].append(str(growth))
        self.loglist['starch'].append(str(starch))
        self.loglist['gametime'].append(str(gametime))
        self.loglist['gamespeed'].append(str(gamespeed))
        self.loglist['water'].append(str(water))
        self.loglist['nitrate'].append(str(nitrate))

    def append_plant_log(self, leaf_mass, stem_mass, root_mass, starch_pool):
        self.loglist['leaf_mass'].append(str(leaf_mass))
        self.loglist['stem_mass'].append(str(stem_mass))
        self.loglist['root_mass'].append(str(root_mass))
        self.loglist['starch_pool'].append(str(starch_pool))

    def write_log(self, name):
        log_dir = os.path.join('logs', datetime.now().strftime('%Y-%m-%d %H.%M.%S') + name)
        path_to_log_dir = os.path.join(self.path_to_log, log_dir)

        if not os.path.exists(path_to_log_dir):
            os.makedirs(path_to_log_dir)

        for key, value in self.loglist.items():
            with open(os.path.join(path_to_log_dir, key + '.txt'), 'w') as the_file:
                for entry in value:
                    the_file.write(entry + "\n")