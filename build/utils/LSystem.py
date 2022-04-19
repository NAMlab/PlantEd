import math
import random
import pygame
import numpy as np

# tier 1 roots

first_tier_root = {"growth_duration" : 1000*60*2,
                   "max_branches" : 10,
                   "max_length" : 500,
                   "initial_speed" : 10}
second_tier_root = {"growth_duration" : 1000*60,
                   "max_branches" : 5,
                    "max_length": 300,
                    "initial_speed": 5}
third_tier_root = {"growth_duration" : 1000*60,
                   "max_branches" : 0,
                   "max_length": 100,
                   "initial_speed": 1}
# depending on tier, sucessor get i+1 tier
root_tier = [first_tier_root, second_tier_root, third_tier_root]

# tier 2 roots

# tier 3 roots

class Letter:
    # letters can be: basal, branching, apex
    def __init__(self, id, tier, dir, growth_start_time, grwoth_end_time, max_length, initial_speed, max_branches=0, branches=[]):
        # branches and follwing segments are held
        self.id = id
        self.tier = tier
        self.dir = dir
        self.length = 0
        self.growth_start_time = growth_start_time
        self.grwoth_end_time = grwoth_end_time
        self.max_length = max_length
        self.initial_speed = initial_speed
        self.branches = branches

    def print(self):
        print(self.id, self.dir, self.grwoth_end_time)
        for branch in self.branches:
            branch.print()

    def draw(self, start_pos, screen):
        end_pos = (start_pos[0]+self.dir[0]*self.length,start_pos[1]+self.dir[1]*self.length)
        pygame.draw.line(screen,(255,255,255),start_pos, end_pos, 5-self.tier)
        for branch in self.branches:
            branch.draw(end_pos, screen)


class LSystem:
    def __init__(self, pos):
        self.pos = pos
        self.first_letter = self.create_root(tier=1)

    def handle_event(self,e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_i:
            self.apply_rules(self.first_letter)

    def create_root(self, tier):
        tier = root_tier[tier]
        # one root creates 3 letters
        # 100 -> basal
        # 200 -> branching -> can produce more 200 additional to branches
        # 300 -> apex
        time = pygame.time.get_ticks()
        apex = Letter(300, 0, self.get_random_direction(5), time, time + tier["growth_duration"], tier["max_length"], tier["initial_speed"])
        branching = Letter(200, 0, self.get_random_direction(5), time, time + tier["growth_duration"], tier["max_length"], tier["initial_speed"], tier["max_branches"], branches=[apex])
        basal = Letter(100, 0, self.get_random_direction(5),time, time + tier["growth_duration"], tier["max_length"], tier["initial_speed"], branches=[branching])
        return basal

    def apply_rules(self, letter):
        self.grow_section(letter)
        for branch in letter.branches:
            self.apply_rules(branch)

    def grow_section(self, letter):
        current_ticks = pygame.time.get_ticks()
        letter.length += self.grow_axial(letter.max_length, letter.initial_speed,current_ticks -letter.growth_start_time)
        print(letter.id, letter.tier, letter.length, letter.max_length, letter.initial_speed, current_ticks-letter.growth_start_time)

    def grow_axial(self, max_length, initial_speed, t):
        delta_length = max_length * (1 - math.exp(-1 * (initial_speed / max_length * t/10000)))
        return delta_length

    def create_branch(self, letter):
        if letter.tier < len(root_tier)-1:
            self.create_root(letter.tier + 1)

    def create_segment(self):
        # creates a new segment after branching
        pass

    def print(self):
        print(self.first_letter.dir[0], self.first_letter.dir[1])
        self.first_letter.print()

    def draw(self,screen):
        self.first_letter.draw(self.pos,screen)
        #self.first_letter

    def get_random_direction(self, tries, down=(0,1)):
        dir = (0, -1)  # up
        for i in range(0, tries):
            phi = random.uniform(0,2*math.pi)
            x = math.cos(phi)
            y = math.sin(phi)
            if self.angle_between(down, (x, y)) < self.angle_between(down, dir):  # downward directions get promoted
                dir = (x, y)
        return dir

    def unit_vector(self, vector):
        return vector / np.linalg.norm(vector)

    def angle_between(self, v1, v2):
        v1_u = self.unit_vector(v1)
        v2_u = self.unit_vector(v2)
        return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))