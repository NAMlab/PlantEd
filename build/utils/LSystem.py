import math
import random
import pygame
import numpy as np

first_tier_root = {"max_length" : 400,
                   "duration" : 3,
                   "tries" : 5,
                   "max_branches" : 10}
second_tier_root = {"max_length" : 200,
                   "duration" : 2,
                    "tries" : 3,
                    "max_branches" : 5}
third_tier_root = {"max_length" : 50,
                   "duration" : 1,
                   "tries" : 1,
                   "max_branches" : 0}
tier_list = [first_tier_root, second_tier_root, third_tier_root]

class Letter:
    def __init__(self, id, tier, dir, max_length, mass_start, mass_end, max_branches=None, branches = [], t=None):
        self.id = id
        self.tier = tier
        self.dir = dir

        self.branching_t = np.random.random(max_branches).tolist() if max_branches is not None else None    # branching dist
        self.t = t
        self.max_length = max_length
        self.mass_start = mass_start
        self.mass_end = mass_end
        self.max_branches = max_branches
        self.branches = branches
        self.length = 0

    def draw(self, screen, start_pos):
        end_pos = (start_pos[0] + self.dir[0] * self.length, start_pos[1] + self.dir[1] * self.length)
        pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 7 - self.tier)
        pygame.draw.line(screen, (255, 255, 246), start_pos, end_pos, 4 - self.tier)
        for branch in self.branches:
            next_start_pos = (start_pos[0] + self.dir[0] * branch.t * self.length,
                              start_pos[1] + self.dir[1] * branch.t * self.length)
            # get t of branch, calc length
            branch.draw(screen, next_start_pos)

    def draw_highlighted(self, screen, start_pos):
        end_pos = (start_pos[0] + self.dir[0] * self.length, start_pos[1] + self.dir[1] * self.length)
        pygame.draw.line(screen, (255, 255, 255), start_pos, end_pos, 9 - self.tier)
        pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, 7 - self.tier)
        pygame.draw.line(screen, (255, 255, 255), start_pos, end_pos, 4 - self.tier)
        for branch in self.branches:
            next_start_pos = (start_pos[0] + self.dir[0] * branch.t * self.length,
                              start_pos[1] + self.dir[1] * branch.t * self.length)
            # get t of branch, calc length
            branch.draw_highlighted(screen, next_start_pos)

    def print(self, offset=""):
        print(offset, self.id, self.tier, self.length, self.max_length, self.mass_start, self.mass_end, self.branching_t, len(self.branches))
        for branch in self.branches:
            branch.print(offset="   " + offset)

class LSystem:
    def __init__(self, directions=None, positions=None, first_letter=None, mass=0):
        self.positions = positions if positions else [(0,0)]
        self.first_letters = []
        self.directions = directions
        for dir in directions:
            self.first_letters.append(self.create_root(dir, mass))

    def create_root(self, dir=None, mass=0, tier=None, t=None):
        dir = dir if dir is not None else (0,1)
        next_tier = tier if tier else 0
        dic = tier_list[next_tier]

        basal_length = dic["max_length"]/10*2
        branching_length = dic["max_length"]/10*6
        apex_length = dic["max_length"]/10*2

        basal_duration = dic["duration"]/10*2
        branching_duration = dic["duration"]/10*6
        apex_duration = dic["duration"]/10*2

        apex = Letter(300, next_tier,self.get_random_dir(dic["tries"],dir), apex_length, mass + basal_duration + branching_duration,
                      mass + basal_duration + branching_duration + apex_duration, t=1)
        branching = Letter(200,next_tier, self.get_random_dir(dic["tries"],dir), branching_length, mass+basal_duration, mass+basal_duration+branching_duration,
                           max_branches=dic["max_branches"],branches=[apex], t=1)
        branching.branching_t.sort()
        basal = Letter(100,next_tier, self.get_random_dir(dic["tries"],dir), basal_length, mass, mass+basal_duration,
                      branches=[branching], t=t)
        return basal

    def update(self, mass):
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

        for branch in letter.branches:
            self.apply_rules(branch, mass)

    def create_branch(self, letter, mass):
        if letter.branching_t[0] < letter.length/letter.max_length:
            t = letter.branching_t.pop(0)
            branch = self.create_root(self.get_ortogonal(letter.dir), mass, tier=letter.tier + 1, t=t)
            apex = letter.branches.pop(-1)
            letter.branches.append(branch)
            segment = Letter(letter.id, letter.tier, self.get_random_dir(tier_list[letter.tier]["tries"],letter.dir),
                             letter.max_length-letter.length, mass, letter.mass_end,
                             letter.max_branches-len(letter.branches), [apex], t=1)
            segment.branching_t = letter.branching_t
            letter.branching_t = []
            letter.id = 99
            letter.branches.append(segment)

    def create_new_first_letter(self, dir, pos, mass):
        self.positions.append(pos)
        self.first_letters.append(self.create_root(dir, mass))

    def update_letter_length(self, letter, mass):
        if mass > letter.mass_start:
            letter.length = letter.max_length * min(1,(mass-letter.mass_start)/(letter.mass_end-letter.mass_start))
            #print(letter.length, letter.mass_start, letter.mass_end, mass)

    def get_random_dir(self, tries, growth_dir=None, down=(0, 1)):
        dir = (random.uniform(0, 2) - 1, random.uniform(0, 2) - 1)
        for i in range(0, tries):
            phi = random.uniform(0, 2 * math.pi)
            x = math.cos(phi)
            y = math.sin(phi/2)

            angle_down_xy = self.angle_between(down, (x, y))
            angle_down_dir = self.angle_between(down, dir)

            angle_growth_xy = 0
            angle_growth_dir = 0
            if growth_dir is not None:
                angle_growth_xy = self.angle_between(growth_dir, (x, y))
                angle_growth_dir = self.angle_between(growth_dir, dir)
            if (angle_down_xy + angle_growth_xy) / 2 < (angle_down_dir + angle_growth_dir) / 2:
                dir = (x, y)
            # if self.angle_between(down, (x, y)) < self.angle_between(down, dir):  # downward directions get promoted
            #    dir = (x, y)
        return dir

    def draw(self,screen):
        for i in range(0,len(self.first_letters)):
            self.first_letters[i].draw(screen, self.positions[i])

    def draw_highlighted(self, screen):
        for i in range(0, len(self.first_letters)):
            self.first_letters[i].draw_highlighted(screen, self.positions[i])

    def print(self):
        #print(self.first_letter.dir[0], self.first_letter.dir[1])
        for letter in self.first_letters:
            letter.print()

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_l:
            self.print()

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