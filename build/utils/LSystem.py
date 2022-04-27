import math
import random
import pygame
import numpy as np

# tier 1 roots
apply_gravity = False
# [1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40]
first_tier_root = {"growth_duration" : 5,
                   "max_branches" : 20,
                   "max_length_basal" : 30,
                   "max_length_branching" : 400,
                   "max_length_apex" : 40,
                   "initial_speed" : 30,
                   "max_tries": 8,
                   "branch_rate" : 50}
second_tier_root = {"growth_duration" : 10,
                   "max_branches" : 8,
                    "max_length_basal": 10,
                    "max_length_branching": 250,
                    "max_length_apex": 30,
                    "initial_speed": 30,
                    "max_tries" : 6,
                    "branch_rate" : 75}
third_tier_root = {"growth_duration" : 1,
                   "max_branches" : 0,
                   "max_length_basal": 5,
                   "max_length_branching": 15,
                   "max_length_apex": 5,
                   "initial_speed": 30,
                   "max_tries" : 2,
                   "branch_rate" : 100}
# depending on tier, sucessor get i+1 tier
root_tier = [first_tier_root, second_tier_root, third_tier_root]

# tier 2 roots

# tier 3 roots

class Letter:
    # letters can be: basal, branching, apex
    def __init__(self, id, tier, dir, init_dir, growth_start_time, grwoth_end_time, max_length, initial_speed, max_branches=0, branches=[], t=1, init_length=0, n_branches=0, branch_rate=80):
        # branches and follwing segments are held
        self.id = id
        self.tier = tier
        self.init_dir = init_dir
        self.dir = dir
        self.length = init_length
        self.growth_start_time = growth_start_time
        self.grwoth_end_time = grwoth_end_time
        self.max_length = max_length
        self.max_branches = max_branches
        self.initial_speed = initial_speed
        self.branches = branches
        self.n_branches = n_branches
        self.branch_rate = branch_rate
        self.t = t

    def print(self, offset=""):
        print(offset, self.id, self.tier, self.length, self.max_length, self.growth_start_time, self.grwoth_end_time)
        for branch in self.branches:
            branch.print(offset="   "+offset)

    def draw(self, screen, start_pos):
        end_pos = (start_pos[0]+self.dir[0]*self.length,start_pos[1]+self.dir[1]*self.length)
        pygame.draw.line(screen,(0,0,0),start_pos, end_pos, 6-self.tier)
        pygame.draw.line(screen,(255,255,255),start_pos, end_pos, 4-self.tier)
        for branch in self.branches:
            next_start_pos = (start_pos[0] + self.dir[0] * branch.t * self.length,
                              start_pos[1] + self.dir[1] * branch.t * self.length)
            # get t of branch, calc length
            branch.draw(screen, next_start_pos)


class LSystem:
    def __init__(self, positions, directions=None):
        self.positions = positions
        self.directions = directions
        if directions:
            self.first_letters = [self.create_root(tier=0,dir=self.directions[i]) for i in range(0,len(self.positions))]
        else:
            self.first_letters = [self.create_root(tier=0,dir=(0,1))]

    def update(self, dt):
        for letter in self.first_letters:
            self.apply_rules(letter)

    def handle_event(self,e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_i:
            self.apply_rules(self.first_letter)
            self.first_letter.print()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_b:
            self.create_branch(self.first_letter)

    def create_root(self, tier, dir=None, t=1, growth_offset=None, init_length=0):
        tier_init = root_tier[tier]
        init_dir = dir if dir is not None else (0, 1)
        # one root creates 3 letters
        # 1 -> segment, that doesn't grow anymore
        # 100 -> basal
        # 200 -> branching -> can produce more 200 additional to branches
        # 300 -> apex
        # basel grows first, then branching, then apex. Once apex is done, branches start to grow
        time = growth_offset if growth_offset else pygame.time.get_ticks()
        apex = Letter(300, tier, self.get_random_direction(tier_init["max_tries"], init_dir), init_dir, time + tier_init["growth_duration"]*2,
                      time + tier_init["growth_duration"]*3, tier_init["max_length_apex"], tier_init["initial_speed"])
        branching = Letter(200, tier, self.get_random_direction(tier_init["max_tries"], init_dir), init_dir, time + tier_init["growth_duration"],
                           time + tier_init["growth_duration"]*2, tier_init["max_length_branching"], tier_init["initial_speed"],
                           tier_init["max_branches"], branches=[apex], branch_rate=tier_init["branch_rate"])
        basal = Letter(100, tier, init_dir, init_dir,time, time + tier_init["growth_duration"],
                       tier_init["max_length_basal"], tier_init["initial_speed"], branches=[branching], t=t,
                       init_length=init_length, branch_rate=tier_init["branch_rate"])
        return basal

    def apply_rules(self, letter):
        current_time = pygame.time.get_ticks()
        if letter.id > 99:
            self.grow_section(letter)
        # random branching
        for branch in letter.branches:
            self.apply_rules(branch)
        if letter.tier > 1:
            print(letter.growth_start_time, letter.grwoth_end_time, current_time, letter.length, letter.max_length)
        if letter.id == 200 and letter.growth_start_time*1.05 < current_time:
            if random.uniform(0,100) > letter.branch_rate:
                self.create_branch(letter)
            if random.uniform(0,100) > 90 and letter.length < letter.max_length:
                self.create_segment(letter)


    def create_segment(self, letter):
        # stop letter growth, keep branches, append segment branch before apex, pass remaining time, max_len
        tier_init = root_tier[letter.tier]
        segment = Letter(letter.id, letter.tier, self.get_random_direction(tier_init["max_tries"],letter.init_dir), letter.init_dir,
                           letter.growth_start_time,
                           letter.grwoth_end_time, letter.max_length-letter.length,
                           letter.initial_speed,
                           tier_init["max_branches"], branches=[letter.branches[-1]], n_branches=letter.n_branches)
        if letter.n_branches > 0:
            letter.branches.pop(len(letter.branches)-1)
            letter.branches.append(segment)
        letter.id = 1


    def grow_section(self, letter):
        current_ticks = pygame.time.get_ticks()
        #print(letter.tier, letter.id, current_ticks, letter.growth_start_time, letter.grwoth_end_time)
        # max length reached
        if letter.length >= letter.max_length:
            letter.length = letter.max_length
            return
        # not started growing
        if letter.growth_start_time > current_ticks:
            return
        # growth time finished
        if letter.grwoth_end_time < current_ticks:
            return
        letter.length += self.grow_axial(letter.max_length, letter.initial_speed,current_ticks -letter.growth_start_time)
        #print(letter.id, letter.tier, letter.length, letter.max_length, letter.initial_speed, current_ticks-letter.growth_start_time)

    def grow_axial(self, max_length, initial_speed, t):
        delta_length = max_length * (1 - math.exp(-1 * (initial_speed / max_length * t/10000)))
        return delta_length

    def create_branch(self, letter):
        if letter.tier < len(root_tier)-1 and letter.n_branches <= letter.max_branches:
            dir = self.get_ortogonal(letter.dir)
            if letter.max_length > 0:
                current_t = letter.length/letter.max_length
            else:
                current_t = random.uniform(0,1)
            # branches start growing when this one is finished
            growth_offset = letter.branches[-1].grwoth_end_time
            branch = self.create_root(letter.tier+1,t=current_t, dir=dir, growth_offset=growth_offset, init_length=0)
            letter.branches.insert(0,branch) #put in first
            letter.n_branches += 1

    def print(self):
        print(self.first_letter.dir[0], self.first_letter.dir[1])
        self.first_letter.print()

    def draw(self,screen):
        for i in range(0,len(self.first_letters)):
            self.first_letters[i].draw(screen, self.positions[i])
        #self.first_letter.draw(screen, self.pos)
        #self.first_letter

    def get_random_direction(self, tries, growth_dir=None, down=(0,1)):
        dir = (random.uniform(0,2)-1,random.uniform(0,2)-1)
        for i in range(0, tries):
            phi = random.uniform(0,2*math.pi)
            x = math.cos(phi)
            y = math.sin(phi)

            angle_down_xy = self.angle_between(down, (x, y))
            angle_down_dir = self.angle_between(down, dir)

            angle_growth_xy = 0
            angle_growth_dir = 0
            if growth_dir is not None:
                angle_growth_xy = self.angle_between(growth_dir, (x, y))
                angle_growth_dir = self.angle_between(growth_dir, dir)

            if (angle_down_xy + angle_growth_xy)/2 < (angle_down_dir+angle_growth_dir)/2:
                dir = (x,y)
            #if self.angle_between(down, (x, y)) < self.angle_between(down, dir):  # downward directions get promoted
            #    dir = (x, y)
        return dir

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