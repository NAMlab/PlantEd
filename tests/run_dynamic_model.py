from fba.helpers import normalize, update_objective, create_objective
from fba.dynamic_model import DynamicModel


class FixedGametime:
    def __init__(self, ticks=0):
        self.ticks = ticks
        self.gamespeed = 240

    def get_time(self):
        return self.ticks


def test_01():
    gametime = FixedGametime()
    model = DynamicModel(gametime)


    #    def update(self, dt, leaf_mass, stem_mass, root_mass, PLA, sun_intensity, max_water_drain, plant_mass):

    model.update(20, 1, 1, 1, 0.3, 1, 1)


