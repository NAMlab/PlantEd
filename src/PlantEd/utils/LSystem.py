import json
import math
import random
from types import SimpleNamespace

import pygame
import numpy as np

tier_list_basic = [
    {"max_length": 400, "duration": 7, "tries": 5, "max_branches": 10},
    {"max_length": 200, "duration": 2, "tries": 3, "max_branches": 5},
    {"max_length": 50, "duration": 1, "tries": 1, "max_branches": 0},
]

short_root = [
    {"max_length": 150, "duration": 4, "tries": 5, "max_branches": 5},
    {"max_length": 100, "duration": 2, "tries": 4, "max_branches": 5},
    {"max_length": 30, "duration": 1, "tries": 1, "max_branches": 0},
]

medium_root = [
    {"max_length": 600, "duration": 5, "tries": 5, "max_branches": 5},
    {"max_length": 250, "duration": 3, "tries": 4, "max_branches": 3},
    {"max_length": 50, "duration": 2, "tries": 1, "max_branches": 0},
]

long_root = [
    {"max_length": 800, "duration": 6, "tries": 6, "max_branches": 3},
    {"max_length": 450, "duration": 4, "tries": 5, "max_branches": 2},
    {"max_length": 90, "duration": 2, "tries": 1, "max_branches": 0},
]

root_classes = [short_root, medium_root, long_root]


class Letter:
    def __init__(
            self,
            id: int,
            root_class: dict,
            tier: int,
            dir: tuple[float, float],
            max_length: int,
            mass_start: float,
            mass_end: float,
            max_branches: int = None,
            branches: list = [],
            t: float = None,
    ):
        self.id: int = id
        self.tier: int = tier
        self.root_class: dict = root_class
        self.dir: tuple[float, float] = dir
        self.branching_t: float = (
            np.random.random(max_branches).tolist()
            if max_branches is not None
            else None
        )  # branching dist
        self.t: float = t
        self.max_length: int = max_length
        self.mass_start: float = mass_start
        self.mass_end: float = mass_end
        self.max_branches: int = max_branches
        self.branches: list[Letter] = branches
        self.length: float = 0
        self.pos: tuple[float, float] = (0, 0)

    def draw(self, screen, start_pos):
        if self.id == 300:
            self.pos = start_pos
        end_pos = (
            start_pos[0] + self.dir[0] * self.length,
            start_pos[1] + self.dir[1] * self.length,
        )
        # pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 7 - self.tier)
        pygame.draw.line(
            screen, (180, 170, 148), start_pos, end_pos, 5 - self.tier
        )
        for branch in self.branches:
            next_start_pos = (
                start_pos[0] + self.dir[0] * branch.t * self.length,
                start_pos[1] + self.dir[1] * branch.t * self.length,
            )
            # get t of branch, calc length
            branch.draw(screen, next_start_pos)

    def draw_highlighted(self, screen, start_pos):
        if self.id == 300 or self.id == 301:
            # pygame.draw.circle(screen,(255,0,0),start_pos,10)
            self.pos = start_pos
        end_pos = (
            start_pos[0] + self.dir[0] * self.length,
            start_pos[1] + self.dir[1] * self.length,
        )
        pygame.draw.line(
            screen, (255, 255, 255), start_pos, end_pos, 7 - self.tier
        )
        # pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 7 - self.tier)
        pygame.draw.line(
            screen, (180, 170, 148), start_pos, end_pos, 5 - self.tier
        )
        for branch in self.branches:
            next_start_pos = (
                start_pos[0] + self.dir[0] * branch.t * self.length,
                start_pos[1] + self.dir[1] * branch.t * self.length,
            )
            # get t of branch, calc length
            branch.draw_highlighted(screen, next_start_pos)

    def to_dict(self) -> dict:
        dic = {}

        dic["id"] = self.id
        dic["tier"] = self.tier
        dic["root_class"] = self.root_class
        dic["length"] = self.length
        dic["max_length"] = self.max_length
        dic["mass_start"] = self.mass_start
        dic["mass_end"] = self.mass_end
        dic["branching_t"] = self.branching_t
        dic["branches"] = [branch.to_dict() for branch in self.branches]
        dic["max_branches"] = self.max_branches
        dic["t"] = self.t
        dic["pos"] = self.pos
        dic["dir"] = self.dir
        return dic

    def from_dict(self, dic):
        self.id = dic["id"]
        self.tier = dic["tier"]
        self.root_class = dic["root_class"]
        self.length = dic["length"]
        self.max_length = dic["max_length"]
        self.mass_start = dic["mass_start"]
        self.mass_end = dic["mass_end"]
        self.branching_t = dic["branching_t"]

        self.branches = [branch.from_dict(branch) for branch in
                         dic["branches"]]  # Todo wont work this way, need another class to do it
        self.max_branches = dic["max_branches"]
        self.t = dic["t"]
        self.pos = dic["pos"]
        self.dir = dic["dir"]

    def print(self, offset=""):
        print(
            offset,
            self.id,
            self.tier,
            self.length,
            self.max_length,
            self.mass_start,
            self.mass_end,
            self.branching_t,
            len(self.branches),
        )
        for branch in self.branches:
            branch.print(offset="   " + offset)

    def get_pos(self):
        return self.pos


class LSystem:
    def __init__(
            self,
            root_grid: np.ndarray,
            water_grid_pos: tuple[float, float],
            directions: list[tuple[float, float]] = [],
            positions: list[tuple[float, float]] = None,
            mass: float = 0,
    ):
        self.root_grid: np.ndarray = root_grid
        self.water_grid_pos: tuple[float, float] = water_grid_pos
        self.positions: list[tuple[float, float]] = positions if positions is not None else []
        self.first_letters: list[Letter] = []
        self.apexes: list[Letter] = []
        self.directions = directions  # if directions is not None else []
        self.root_classes = root_classes
        for dir in directions:
            self.first_letters.append(self.create_root(dir, mass))

    def to_dict(self) -> dict:
        dic = {}
        dic["root_grid"] = dict(enumerate(self.root_grid.flatten(), 1))
        dic["water_grid_pos"] = self.water_grid_pos
        dic["positions"] = self.positions
        dic["apexes"] = self.apexes
        dic["directions"] = self.directions
        dic["root_classes"] = self.root_classes
        dic["first_letters"] = [first_letter.to_dict() for first_letter in self.first_letters]
        return dic

    def create_root(self, dir=None, mass=0, root_class=0, tier=None, t=None):
        dir = dir if dir is not None else (0, 1)
        next_tier = tier if tier else 0
        dic = self.root_classes[root_class][next_tier]

        basal_length = dic["max_length"] / 10 * 2
        branching_length = dic["max_length"] / 10 * 6
        apex_length = dic["max_length"] / 10 * 2

        basal_duration = dic["duration"] / 10 * 2
        branching_duration = dic["duration"] / 10 * 6
        apex_duration = dic["duration"] / 10 * 2

        apex = Letter(
            300,
            root_class,
            next_tier,
            self.get_random_dir(dic["tries"], dir),
            apex_length,
            mass + basal_duration + branching_duration,
            mass + basal_duration + branching_duration + apex_duration,
            t=1,
        )
        branching = Letter(
            200,
            root_class,
            next_tier,
            self.get_random_dir(dic["tries"], dir),
            branching_length,
            mass + basal_duration,
            mass + basal_duration + branching_duration,
            max_branches=dic["max_branches"],
            branches=[apex],
            t=1,
        )
        branching.branching_t.sort()
        basal = Letter(
            100,
            root_class,
            next_tier,
            self.get_random_dir(dic["tries"], dir),
            basal_length,
            mass,
            mass + basal_duration,
            branches=[branching],
            t=t,
        )
        return basal

    """def set_root_tier(self, root_tier):
        self.tier_list = tier_lists[root_tier]"""

    def update(self, mass):
        self.apexes = []
        for letter in self.first_letters:
            self.apply_rules(letter, mass)

    def apply_rules(self, letter, mass):
        if letter.max_length <= letter.length:
            letter.id = 99
        # growing
        if letter.id > 99:
            self.update_letter_length(letter, mass)
        # branching
        if letter.id == 200:
            if letter.max_branches > len(letter.branches):
                if letter.branching_t and len(letter.branching_t) > 0:
                    # make branch, remove apex, apend branch, make segment, apend apex

                    self.create_branch(letter, mass)

        # calc root pos in water grid
        if letter.id == 300:
            pos = letter.get_pos()
            if pos[1] > 1260:
                letter.id = 99
            # todo fix ugly hard coded numbers
            x = min(19, max(0, int((pos[0] - self.water_grid_pos[0]) / 100)))
            y = min(5, max(0, int((pos[1] - self.water_grid_pos[1]) / 100)))
            # print(x,y,pos, self.root_grid, self.water_grid_pos)
            self.root_grid[y, x] = 1

        for branch in letter.branches:
            self.apply_rules(branch, mass)

    def create_branch(self, letter, mass):
        if letter.branching_t[0] < letter.length / letter.max_length:
            t = letter.branching_t.pop(0)
            branch = self.create_root(
                self.get_ortogonal(letter.dir),
                mass,
                root_class=letter.root_class,
                tier=letter.tier + 1,
                t=t,
            )
            apex = letter.branches.pop(-1)
            letter.branches.append(branch)
            segment = Letter(
                letter.id,
                letter.root_class,
                letter.tier,
                self.get_random_dir(
                    self.root_classes[letter.root_class][letter.tier]["tries"],
                    letter.dir,
                ),
                letter.max_length - letter.length,
                mass,
                letter.mass_end,
                letter.max_branches - len(letter.branches),
                [apex],
                t=1,
            )
            segment.branching_t = letter.branching_t
            letter.branching_t = []
            letter.id = 99
            letter.branches.append(segment)

    def create_new_first_letter(self, dir, pos, mass, dist=None):
        root_class = 0
        if dist:
            if dist < 300:
                root_class = 0
            elif dist < 600:
                root_class = 1
            else:
                root_class = 2
        self.positions.append(pos)
        self.first_letters.append(
            self.create_root(dir, mass, root_class=root_class)
        )

    def update_letter_length(self, letter, mass):
        if mass > letter.mass_start:
            letter.length = letter.max_length * min(
                1,
                (mass - letter.mass_start)
                / (letter.mass_end - letter.mass_start),
            )
            # print(letter.length, letter.mass_start, letter.mass_end, mass)

    def get_random_dir(self, tries, growth_dir=None, down=(0, 1)):
        phi = random.uniform(0, math.pi)
        dir = (math.cos(phi), math.sin(phi))
        for i in range(0, tries):
            phi = random.uniform(0, math.pi)
            x = math.cos(phi)
            y = math.sin(phi)

            angle_down_xy = self.angle_between(down, (x, y))
            angle_down_dir = self.angle_between(down, dir)

            angle_growth_xy = 0
            angle_growth_dir = 0
            if growth_dir is not None:
                angle_growth_xy = self.angle_between(growth_dir, (x, y))
                angle_growth_dir = self.angle_between(growth_dir, dir)
            if (angle_down_xy + angle_growth_xy * 3) < (
                    angle_down_dir + angle_growth_dir * 3
            ):
                dir = (x, y)
            # if self.angle_between(down, (x, y)) < self.angle_between(down, dir):  # downward directions get promoted
            #    dir = (x, y)
        return dir

    def draw(self, screen):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].draw(screen, self.positions[i])

    def draw_highlighted(self, screen):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].draw_highlighted(screen, self.positions[i])

    def print(self):
        # print(self.first_letter.dir[0], self.first_letter.dir[1])
        for letter in self.first_letters:
            letter.print()

    def handle_event(self, e):
        pass
        """if e.type == pygame.KEYDOWN and e.key == pygame.K_p:
            print(self.root_grid)
        if e.type == pygame.KEYDOWN and e.key == pygame.K_l:
            self.print()
"""

    def unit_vector(self, vector):
        return vector / np.linalg.norm(vector)

    def angle_between(self, v1, v2):
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

    def get_ortogonal(self, v1):
        norm_vec = self.unit_vector(v1)
        v2 = np.random.randn(2)
        v2 -= v2.dot(norm_vec) * norm_vec
        v2 /= np.linalg.norm(v2)
        return v2


root = {
    'root_grid': {1: 1.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0, 10: 1.0, 11: 1.0, 12: 0.0,
                  13: 0.0, 14: 0.0, 15: 0.0, 16: 0.0, 17: 0.0, 18: 0.0, 19: 0.0, 20: 0.0, 21: 0.0, 22: 0.0, 23: 0.0,
                  24: 0.0, 25: 0.0, 26: 0.0, 27: 0.0, 28: 0.0, 29: 0.0, 30: 1.0, 31: 0.0, 32: 0.0, 33: 0.0, 34: 0.0,
                  35: 0.0, 36: 0.0, 37: 0.0, 38: 0.0, 39: 0.0, 40: 0.0, 41: 0.0, 42: 0.0, 43: 0.0, 44: 0.0, 45: 0.0,
                  46: 0.0, 47: 0.0, 48: 0.0, 49: 0.0, 50: 0.0, 51: 0.0, 52: 0.0, 53: 0.0, 54: 0.0, 55: 0.0, 56: 0.0,
                  57: 0.0, 58: 0.0, 59: 0.0, 60: 0.0, 61: 0.0, 62: 0.0, 63: 0.0, 64: 0.0, 65: 0.0, 66: 0.0, 67: 0.0,
                  68: 0.0, 69: 0.0, 70: 0.0, 71: 0.0, 72: 0.0, 73: 0.0, 74: 0.0, 75: 0.0, 76: 0.0, 77: 0.0, 78: 0.0,
                  79: 0.0, 80: 0.0, 81: 0.0, 82: 0.0, 83: 0.0, 84: 0.0, 85: 0.0, 86: 0.0, 87: 0.0, 88: 0.0, 89: 0.0,
                  90: 0.0, 91: 0.0, 92: 0.0, 93: 0.0, 94: 0.0, 95: 0.0, 96: 0.0, 97: 0.0, 98: 0.0, 99: 0.0,
                  100: 0.0, 101: 0.0, 102: 0.0, 103: 0.0, 104: 0.0, 105: 0.0, 106: 0.0, 107: 0.0, 108: 0.0,
                  109: 0.0, 110: 0.0, 111: 0.0, 112: 0.0, 113: 0.0, 114: 0.0, 115: 0.0, 116: 0.0, 117: 0.0,
                  118: 0.0, 119: 0.0, 120: 0.0},
    'water_grid_pos': (0, 900),
    'positions': [(955.0, 904.0)],
    'apexes': [], 'directions': [], 'root_classes': [
        [{'max_length': 150, 'duration': 4, 'tries': 5, 'max_branches': 5},
         {'max_length': 100, 'duration': 2, 'tries': 4, 'max_branches': 5},
         {'max_length': 30, 'duration': 1, 'tries': 1, 'max_branches': 0}],
        [{'max_length': 600, 'duration': 5, 'tries': 5, 'max_branches': 5},
         {'max_length': 250, 'duration': 3, 'tries': 4, 'max_branches': 3},
         {'max_length': 50, 'duration': 2, 'tries': 1, 'max_branches': 0}],
        [{'max_length': 800, 'duration': 6, 'tries': 6, 'max_branches': 3},
         {'max_length': 450, 'duration': 4, 'tries': 5, 'max_branches': 2},
         {'max_length': 90, 'duration': 2, 'tries': 1, 'max_branches': 0}]], 'first_letters': [
        {'id': 99, 'tier': 0, 'root_class': 0, 'length': 30.0, 'max_length': 30.0, 'mass_start': 1, 'mass_end': 1.8,
         'branching_t': None, 'branches': [
            {'id': 99, 'tier': 0, 'root_class': 0, 'length': 17.462638136234233, 'max_length': 90.0,
             'mass_start': 1.8, 'mass_end': 4.2, 'branching_t': [], 'branches': [
                {'id': 99, 'tier': 1, 'root_class': 0, 'length': 20.0, 'max_length': 20.0,
                 'mass_start': 2.2656703502995796, 'mass_end': 2.6656703502995795, 'branching_t': None,
                 'branches': [
                     {'id': 99, 'tier': 1, 'root_class': 0, 'length': 12.263276552283541, 'max_length': 60.0,
                      'mass_start': 2.6656703502995795, 'mass_end': 3.8656703502995797, 'branching_t': [],
                      'branches': [{'id': 99, 'tier': 2, 'root_class': 0, 'length': 6.0, 'max_length': 6.0,
                                    'mass_start': 2.9109358813452504, 'mass_end': 3.1109358813452506,
                                    'branching_t': None, 'branches': [
                              {'id': 99, 'tier': 2, 'root_class': 0, 'length': 18.0, 'max_length': 18.0,
                               'mass_start': 3.1109358813452506, 'mass_end': 3.7109358813452507, 'branching_t': [],
                               'branches': [{'id': 300, 'tier': 2, 'root_class': 0, 'length': 4.772323043950953,
                                             'max_length': 6.0, 'mass_start': 3.7109358813452507,
                                             'mass_end': 3.910935881345251, 'branching_t': None, 'branches': [],
                                             'max_branches': None, 't': 1,
                                             'pos': (943.3195049443465, 959.6695258037696),
                                             'dir': (0.49254221085035726, 0.8702885559000775)}], 'max_branches': 0,
                               't': 1, 'pos': (0, 0), 'dir': (-0.999628393121145, 0.027259414264389124)}],
                                    'max_branches': None, 't': 0.20409972065852489, 'pos': (0, 0),
                                    'dir': (0.8604410104359249, 0.5095500638406443)},
                                   {'id': 99, 'tier': 1, 'root_class': 0, 'length': 19.06867578912492,
                                    'max_length': 47.73672344771646, 'mass_start': 2.9109358813452504,
                                    'mass_end': 3.8656703502995797, 'branching_t': [], 'branches': [
                                       {'id': 99, 'tier': 2, 'root_class': 0, 'length': 6.0, 'max_length': 6.0,
                                        'mass_start': 3.292309397127749, 'mass_end': 3.492309397127749,
                                        'branching_t': None, 'branches': [
                                           {'id': 200, 'tier': 2, 'root_class': 0, 'length': 11.331117570475996,
                                            'max_length': 18.0, 'mass_start': 3.492309397127749,
                                            'mass_end': 4.0923093971277495, 'branching_t': [], 'branches': [
                                               {'id': 300, 'tier': 2, 'root_class': 0, 'length': 0,
                                                'max_length': 6.0, 'mass_start': 4.0923093971277495,
                                                'mass_end': 4.29230939712775, 'branching_t': None, 'branches': [],
                                                'max_branches': None, 't': 1,
                                                'pos': (949.5003795422665, 985.2562545655746),
                                                'dir': (-0.8633266320539521, 0.5046455452952895)}],
                                            'max_branches': 0, 't': 1, 'pos': (0, 0),
                                            'dir': (-0.20646291688590335, 0.9784544260981012)}],
                                        'max_branches': None, 't': 0.3987742837047302, 'pos': (0, 0),
                                        'dir': (-0.9883053795623646, 0.15248762811484215)},
                                       {'id': 99, 'tier': 1, 'root_class': 0, 'length': 11.483580267672684,
                                        'max_length': 28.668047658591536, 'mass_start': 3.292309397127749,
                                        'mass_end': 3.8656703502995797, 'branching_t': [], 'branches': [
                                           {'id': 99, 'tier': 2, 'root_class': 0, 'length': 6.0, 'max_length': 6.0,
                                            'mass_start': 3.5219810024812026, 'mass_end': 3.721981002481203,
                                            'branching_t': None, 'branches': [
                                               {'id': 200, 'tier': 2, 'root_class': 0, 'length': 4.440969409872392,
                                                'max_length': 18.0, 'mass_start': 3.721981002481203,
                                                'mass_end': 4.321981002481203, 'branching_t': [], 'branches': [
                                                   {'id': 300, 'tier': 2, 'root_class': 0, 'length': 0,
                                                    'max_length': 6.0, 'mass_start': 4.321981002481203,
                                                    'mass_end': 4.521981002481203, 'branching_t': None,
                                                    'branches': [], 'max_branches': None, 't': 1,
                                                    'pos': (955.9370594604119, 998.0485425098653),
                                                    'dir': (-0.9982740837902937, 0.058726941284640816)}],
                                                'max_branches': 0, 't': 1, 'pos': (0, 0),
                                                'dir': (-0.4371423928920477, 0.8993923105834376)}],
                                            'max_branches': None, 't': 0.40001342925989625, 'pos': (0, 0),
                                            'dir': (-0.5240382695727909, 0.8516947176207886)},
                                           {'id': 99, 'tier': 1, 'root_class': 0, 'length': 12.61867966425294,
                                            'max_length': 17.184467390918854, 'mass_start': 3.5219810024812026,
                                            'mass_end': 3.8656703502995797, 'branching_t': [], 'branches': [
                                               {'id': 100, 'tier': 2, 'root_class': 0, 'length': 2.869761611320631,
                                                'max_length': 6.0, 'mass_start': 3.7743545957662614,
                                                'mass_end': 3.9743545957662616, 'branching_t': None, 'branches': [
                                                   {'id': 200, 'tier': 2, 'root_class': 0, 'length': 0,
                                                    'max_length': 18.0, 'mass_start': 3.9743545957662616,
                                                    'mass_end': 4.574354595766262, 'branching_t': [], 'branches': [
                                                       {'id': 300, 'tier': 2, 'root_class': 0, 'length': 0,
                                                        'max_length': 6.0, 'mass_start': 4.574354595766262,
                                                        'mass_end': 4.774354595766262, 'branching_t': None,
                                                        'branches': [], 'max_branches': None, 't': 1,
                                                        'pos': (962.0912512558889, 1007.9229445699128),
                                                        'dir': (0.2408662109923304, 0.9705583281813609)}],
                                                    'max_branches': 0, 't': 1, 'pos': (0, 0),
                                                    'dir': (-0.4767490905204566, 0.879039421577848)}],
                                                'max_branches': None, 't': 0.7338193616808149, 'pos': (0, 0),
                                                'dir': (0.02163709129944256, 0.9997658907364761)},
                                               {'id': 99, 'tier': 1, 'root_class': 0, 'length': 4.5657877266659135,
                                                'max_length': 4.5657877266659135, 'mass_start': 3.7743545957662614,
                                                'mass_end': 3.8656703502995797, 'branching_t': [0.9994344806305506],
                                                'branches': [{'id': 300, 'tier': 1, 'root_class': 0,
                                                              'length': 0.21714829220180756, 'max_length': 20.0,
                                                              'mass_start': 3.8656703502995797,
                                                              'mass_end': 4.26567035029958, 'branching_t': None,
                                                              'branches': [], 'max_branches': None, 't': 1,
                                                              'pos': (961.42180125693, 1012.9191817710932),
                                                              'dir': (-0.31831847836769855, 0.9479838323144931)}],
                                                'max_branches': 1, 't': 1, 'pos': (0, 0),
                                                'dir': (-0.15802503924034195, 0.9874351051958242)}],
                                            'max_branches': 2, 't': 1, 'pos': (0, 0),
                                            'dir': (0.03398548330887773, 0.9994223266088575)}], 'max_branches': 3,
                                        't': 1, 'pos': (0, 0), 'dir': (0.10041126996775096, 0.9949460170599526)}],
                                    'max_branches': 4, 't': 1, 'pos': (0, 0),
                                    'dir': (0.24350741631111264, 0.9698990350554466)}], 'max_branches': 5, 't': 1,
                      'pos': (0, 0), 'dir': (-0.02378570534165525, 0.999717080088862)}], 'max_branches': None,
                 't': 0.19393130761918342, 'pos': (0, 0), 'dir': (-0.4491436354940321, 0.8934595652267673)},
                {'id': 99, 'tier': 0, 'root_class': 0, 'length': 40.4009081833529, 'max_length': 72.53736186376577,
                 'mass_start': 2.2656703502995796, 'mass_end': 4.2, 'branching_t': [], 'branches': [
                    {'id': 99, 'tier': 1, 'root_class': 0, 'length': 20.0, 'max_length': 20.0,
                     'mass_start': 3.343027901855657, 'mass_end': 3.743027901855657, 'branching_t': None,
                     'branches': [
                         {'id': 99, 'tier': 1, 'root_class': 0, 'length': 0.6977924098730212, 'max_length': 60.0,
                          'mass_start': 3.743027901855657, 'mass_end': 4.9430279018556575, 'branching_t': [],
                          'branches': [{'id': 100, 'tier': 2, 'root_class': 0, 'length': 3.390886982714952,
                                        'max_length': 6.0, 'mass_start': 3.7569837500531174,
                                        'mass_end': 3.9569837500531175, 'branching_t': None, 'branches': [
                                  {'id': 200, 'tier': 2, 'root_class': 0, 'length': 0, 'max_length': 18.0,
                                   'mass_start': 3.9569837500531175, 'mass_end': 4.556983750053117,
                                   'branching_t': [], 'branches': [
                                      {'id': 300, 'tier': 2, 'root_class': 0, 'length': 0, 'max_length': 6.0,
                                       'mass_start': 4.556983750053117, 'mass_end': 4.756983750053117,
                                       'branching_t': None, 'branches': [], 'max_branches': None, 't': 1,
                                       'pos': (1009.7906814970033, 959.2635919216195),
                                       'dir': (0.6083186936081879, 0.7936928669244973)}], 'max_branches': 0, 't': 1,
                                   'pos': (0, 0), 'dir': (-0.287338292353145, 0.957829163132747)}],
                                        'max_branches': None, 't': 0.011227924126081312, 'pos': (0, 0),
                                        'dir': (-0.8916981117166731, 0.45263061933647347)},
                                       {'id': 200, 'tier': 1, 'root_class': 0, 'length': 5.651478304524923,
                                        'max_length': 59.302207590126976, 'mass_start': 3.7569837500531174,
                                        'mass_end': 4.9430279018556575,
                                        'branching_t': [0.22707725177001115, 0.26812191500857274,
                                                        0.34103767378590943, 0.4520253426674272], 'branches': [
                                           {'id': 300, 'tier': 1, 'root_class': 0, 'length': 0, 'max_length': 20.0,
                                            'mass_start': 4.9430279018556575, 'mass_end': 5.343027901855658,
                                            'branching_t': None, 'branches': [], 'max_branches': None, 't': 1,
                                            'pos': (1019.0637488447688, 958.797427310914),
                                            'dir': (0.9995824983158749, 0.028893408601167923)}], 'max_branches': 4,
                                        't': 1, 'pos': (0, 0), 'dir': (0.984473714101048, 0.1755320661420241)}],
                          'max_branches': 5, 't': 1, 'pos': (0, 0),
                          'dir': (0.9938117100016995, 0.11107783335795651)}], 'max_branches': None,
                     't': 0.5568857313216825, 'pos': (0, 0), 'dir': (0.986164961065277, 0.16576691336669352)},
                    {'id': 99, 'tier': 0, 'root_class': 0, 'length': 18.185321574794838,
                     'max_length': 32.13645368041287, 'mass_start': 3.343027901855657, 'mass_end': 4.2,
                     'branching_t': [], 'branches': [
                        {'id': 100, 'tier': 1, 'root_class': 0, 'length': 2.1021752813381593, 'max_length': 20.0,
                         'mass_start': 3.8279698105168527, 'mass_end': 4.227969810516853, 'branching_t': None,
                         'branches': [{'id': 200, 'tier': 1, 'root_class': 0, 'length': 0, 'max_length': 60.0,
                                       'mass_start': 4.227969810516853, 'mass_end': 5.427969810516853,
                                       'branching_t': [0.03559480646227853, 0.4459497519426726, 0.7142663030075918,
                                                       0.9019297053235811, 0.9911700717319061], 'branches': [
                                 {'id': 300, 'tier': 1, 'root_class': 0, 'length': 0, 'max_length': 20.0,
                                  'mass_start': 5.427969810516853, 'mass_end': 5.827969810516853,
                                  'branching_t': None, 'branches': [], 'max_branches': None, 't': 1,
                                  'pos': (1018.5735181165059, 960.2426319432589),
                                  'dir': (-0.9504991295830716, 0.31072721905527245)}], 'max_branches': 5, 't': 1,
                                       'pos': (0, 0), 'dir': (-0.9972476926191446, 0.07414202294105691)}],
                         'max_branches': None, 't': 0.5651907870332868, 'pos': (0, 0),
                         'dir': (-0.9628485206483898, 0.2700420824338447)},
                        {'id': 200, 'tier': 0, 'root_class': 0, 'length': 1.5766314610036194,
                         'max_length': 13.951132105618033, 'mass_start': 3.8279698105168527, 'mass_end': 4.2,
                         'branching_t': [0.8556228389559652, 0.8846657048297577], 'branches': [
                            {'id': 300, 'tier': 0, 'root_class': 0, 'length': 0, 'max_length': 30.0,
                             'mass_start': 4.2, 'mass_end': 5.0, 'branching_t': None, 'branches': [],
                             'max_branches': None, 't': 1, 'pos': (1030.0646386956012, 960.1960693389591),
                             'dir': (0.14098718149422454, 0.9900114214766992)}], 'max_branches': 2, 't': 1,
                         'pos': (0, 0), 'dir': (0.9944515021187963, 0.10519605474384357)}], 'max_branches': 3,
                     't': 1, 'pos': (0, 0), 'dir': (0.9989901960207231, 0.04492870190064758)}], 'max_branches': 4,
                 't': 1, 'pos': (0, 0), 'dir': (0.9633751994420918, 0.26815709034054985)}], 'max_branches': 5,
             't': 1, 'pos': (0, 0), 'dir': (0.4415991506636144, 0.8972124554046128)}], 'max_branches': None,
         't': None, 'pos': (0, 0), 'dir': (0.2899026019375908, 0.9570561537286173)}]}


class DictToRoot:

    def create_root_system(self):
        dic = root
        # convert LSystem dict to key, values
        # for each first letter: convert dict of first letter
        # for each branch in first letter: convert -> until

        # maybe weird, but works
        result = dic["root_grid"].items()
        data = list(result)
        npa = np.array(data)
        dela = np.delete(npa, 0, 1)
        root_grid: np.ndarray = np.reshape(dela, (-1, 20))

        water_grid_pos: tuple[float, float] = dic["water_grid_pos"]
        directions = []
        positions: list[tuple[float, float]] = dic["positions"]
        #mass: float = dic["mass"]
        root_system = LSystem(root_grid, water_grid_pos, positions, directions)

        first_letters = dic["first_letters"]
        root_system.apexes = dic["apexes"]
        root_system.directions = dic["directions"]

        for i in range(len(first_letters)):
            root_system.first_letters.append(self.dict2letter(first_letters[0]))

        return root_system


    def dict2letter(self, dic_letter):
        id = dic_letter["id"]
        tier = dic_letter["tier"]
        root_class = dic_letter["root_class"]
        length = dic_letter["length"]
        max_length = dic_letter["max_length"]
        mass_start = dic_letter["mass_start"]
        mass_end = dic_letter["mass_end"]
        branching_t = dic_letter["branching_t"]
        branches = []
        for branch in dic_letter["branches"]:
            branches.append(self.dict2letter(branch))
        max_branches = dic_letter["max_branches"]
        t = dic_letter["t"]
        pos = dic_letter["pos"]
        dir = dic_letter["dir"]
        letter = Letter(id, root_class, tier, dir, max_length, mass_start, mass_end, length, max_branches, branches, t, branching_t)
        return letter

        def __init__(
                self,
                id: int,
                root_class: dict,
                tier: int,
                dir: tuple[float, float],
                max_length: int,
                mass_start: float,
                mass_end: float,
                lenght = 0,
                max_branches: int = None,
                branches: list = [],
                t: float = None,
                branching_t = None,
        ):
            self.id: int = id
            self.tier: int = tier
            self.root_class: dict = root_class
            self.dir: tuple[float, float] = dir
            self.branching_t: float = (
                np.random.random(max_branches).tolist()
                if max_branches is not None
                else None
            )  # branching dist
            self.t: float = t
            self.max_length: int = max_length
            self.mass_start: float = mass_start
            self.mass_end: float = mass_end
            self.max_branches: int = max_branches
            self.branches: list[Letter] = branches
            self.length: float = lenght
            self.pos: tuple[float, float] = (0, 0)