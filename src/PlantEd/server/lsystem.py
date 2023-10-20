from __future__ import annotations
import math
import random
import numpy as np

short_root = [
    {"max_length": 150, "duration": 0.03, "tries": 5, "max_branches": 5},
    {"max_length": 100, "duration": 0.04, "tries": 4, "max_branches": 5},
    {"max_length": 30, "duration": 0.03, "tries": 1, "max_branches": 0},
]

medium_root = [
    {"max_length": 600, "duration": 0.05, "tries": 5, "max_branches": 5},
    {"max_length": 250, "duration": 0.03, "tries": 4, "max_branches": 3},
    {"max_length": 50, "duration": 0.02, "tries": 1, "max_branches": 0},
]

long_root = [
    {"max_length": 800, "duration": 3, "tries": 6, "max_branches": 3},
    {"max_length": 450, "duration": 2, "tries": 5, "max_branches": 2},
    {"max_length": 90, "duration": 1, "tries": 1, "max_branches": 0},
]

root_classes = [short_root, medium_root, long_root]

"""
Letters are part of a root. Each letter has an id, that indicates its state.
# 300 -> apex
# 200 -> branching
# 100 -> basal
# <100 -> fully grown
Rules apply based on its id. Growth depends on duration (delta mass).
Following branches or segments are stored in a list of branches.
"""


class Letter:
    def __init__(
            self,
            id: int,
            root_class: int,
            tier: int,
            dir: tuple[float, float],
            max_length: float,
            mass_start: float,
            mass_end: float,
            max_branches: int = None,
            branches: list = [],
            t: float = None,
            branching_t: list[float] = None,
            length: float = 0,
            pos: tuple[float, float] = (0, 0)
    ):
        self.id: int = id
        self.tier: int = tier
        self.root_class: int = root_class
        self.dir: tuple[float, float] = dir
        if branching_t is None:
            self.branching_t: float = (
                np.random.random(max_branches).tolist()
                if max_branches is not None
                else None
            )  # branching dist
        else:
            self.branching_t = branching_t
        self.t: float = t
        self.max_length: float = max_length
        self.mass_start: float = mass_start
        self.mass_end: float = mass_end
        self.max_branches: int = max_branches
        self.branches: list[Letter] = branches
        self.length: float = length
        self.pos: tuple[float, float] = pos

    def calc_position(self, start_pos):
        if self.id == 300:
            self.pos = start_pos

        for branch in self.branches:
            next_start_pos = (
                start_pos[0] + self.dir[0] * branch.t * self.length,
                start_pos[1] + self.dir[1] * branch.t * self.length,
            )
            branch.calc_position(next_start_pos)

    def draw(self, screen, start_pos):
        import pygame

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
        import pygame

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

    def get_pos(self) -> tuple[float, float]:
        return self.pos


"""
A list of all root segments
Roots consist of basal, branching ans apex
All three segments can grow. The branching part is also able to grow branches.
When doing so, it will create a new segment and pick a new semi-random direction.
Initial roots can bew small, medium and long. Each type has a different architecture.
Root tiers describe the degree of each branch. Once the lowest tier has been reached, 
branching can no longer happen.
"""


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
        self.directions: list[tuple[float, float]] = directions  # if directions is not None else []
        self.root_classes: list[list[dict]] = root_classes
        for dir in directions:
            self.first_letters.append(self.create_root(dir, mass))

    def __eq__(self, other):
        if not isinstance(other, LSystem):
            return False

        if not np.all(self.root_grid == other.root_grid):
            return False
        if self.water_grid_pos != other.water_grid_pos:
            return False
        if self.positions != other.positions:
            return False
        if self.directions != other.directions:
            return False
        if self.root_classes != other.root_classes:
            return False
        if set(self.first_letters) != set(other.first_letters):
            return False

        return True

    def to_dict(self) -> dict:
        dic = {"root_grid": self.root_grid.tolist(),
               "water_grid_pos": self.water_grid_pos,
               "positions": self.positions,
               "directions": self.directions,
               "root_classes": self.root_classes,
               "first_letters": [first_letter.to_dict() for first_letter in self.first_letters]}
        return dic

    """
    Make a root of basal, branching and apex letters
    Duration is staggered. Therefore each segment has to be 
    fully grown before the next one can grow
    """

    def create_root(self, dir: tuple[float, float] = None, mass: float = 0, root_class: int = 0, tier: int = None,
                    t: float = None):
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
            id=300,
            root_class=root_class,
            tier=next_tier,
            dir=self.get_random_dir(dic["tries"], dir),
            max_length=apex_length,
            mass_start=mass + basal_duration + branching_duration,
            mass_end=mass + basal_duration + branching_duration + apex_duration,
            t=1,
        )
        branching = Letter(
            id=200,
            root_class=root_class,
            tier=next_tier,
            dir=self.get_random_dir(dic["tries"], dir),
            max_length=branching_length,
            mass_start=mass + basal_duration,
            mass_end=mass + basal_duration + branching_duration,
            max_branches=dic["max_branches"],
            branches=[apex],
            t=1,
        )
        branching.branching_t.sort()
        basal = Letter(
            id=100,
            root_class=root_class,
            tier=next_tier,
            dir=self.get_random_dir(dic["tries"], dir),
            max_length=basal_length,
            mass_start=mass,
            mass_end=mass + basal_duration,
            branches=[branching],
            t=t,
        )
        return basal

    """
    Apply rules to each letter
    """

    def update(self, mass):
        """
        mass should change from 0.00001 to 1
        rules should apply for each 0.1 step
        but should be called once at least

        delta_mass = 0.2 -> 2 apply_rules calls
        delta_mass = 0.02 -> 1
        """
        # delta_mass = mass_end - mass_start

        # mass_per_letter = mass/max(0,len(self.first_letters))

        for letter in self.first_letters:
            self.apply_rules(letter, mass)
        self.calc_positions()

    """

    """

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
            x = min(19, max(0, int((pos[0] - self.water_grid_pos[0]) / 100)))
            y = min(5, max(0, int((pos[1] - self.water_grid_pos[1]) / 100)))
            self.root_grid[x, y] = 1

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
                id=letter.id,
                root_class=letter.root_class,
                tier=letter.tier,
                dir=self.get_random_dir(
                    self.root_classes[letter.root_class][letter.tier]["tries"],
                    letter.dir,
                ),
                max_length=letter.max_length - letter.length,
                mass_start=mass,
                mass_end=letter.mass_end,
                max_branches=letter.max_branches - len(letter.branches),
                branches=[apex],
                t=1,
            )
            segment.branching_t = letter.branching_t
            letter.branching_t = []
            letter.id = 99
            letter.branches.append(segment)

    def create_new_first_letter(self, dir, pos, mass, dist=None):
        root_class = 1
        # todo maybe make better classes
        if dist:
            if dist < 300:
                root_class = 1
            elif dist < 600:
                root_class = 1
            else:
                root_class = 1
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

    def calc_positions(self):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].calc_position(self.positions[i])

    def draw(self, screen):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].draw(screen, self.positions[i])

    def draw_highlighted(self, screen):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].draw_highlighted(screen, self.positions[i])

    def print(self):
        for letter in self.first_letters:
            letter.print()

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


class DictToRoot:
    @staticmethod
    def load_root_system(dic: dict) -> LSystem:
        # convert LSystem dict to key, values
        # for each first letter: convert dict of first letter
        # for each branch in first letter: convert -> until

        root_grid: np.ndarray = np.asarray(dic["root_grid"])

        water_grid_pos: tuple[float, float] = tuple(dic["water_grid_pos"])
        directions = []
        positions: list[tuple[float, float]] = dic["positions"]

        # mass: float = dic["mass"]
        root_system = LSystem(root_grid=root_grid,
                              water_grid_pos=water_grid_pos,
                              directions=directions,
                              positions=positions)

        first_letters = dic["first_letters"]
        # root_system.apexes = dic["apexes"]
        root_system.directions = dic["directions"]
        for i in range(len(first_letters)):
            root_system.first_letters.append(DictToRoot.dict2letter(first_letters[i]))

        return root_system

    @staticmethod
    def dict2letter(dic_letter):
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
            branches.append(DictToRoot.dict2letter(branch))
        max_branches = dic_letter["max_branches"]
        t = dic_letter["t"]
        pos = dic_letter["pos"]
        dir = dic_letter["dir"]
        letter = Letter(id, root_class, tier, dir, max_length, mass_start, mass_end, max_branches, branches, t,
                        branching_t, length, pos)
        return letter
