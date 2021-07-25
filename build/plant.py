import cobra.test
import random
import numpy as np
import pygame

GAME_SPEED = 1
gram_mol = 0.5124299411
WIN = 1
pivot_pos = [(666, 299), (9, 358), (690, 222), (17, 592), (389, 553), (20, 891), (283, 767), (39, 931)]
leaves = [(pygame.image.load("../assets/leaves/leaf_{index}.png".format(index=i)), pivot_pos[i]) for i in range(0, 7)]
stem = (pygame.image.load("../assets/stem.png"),(15,1063))
roots = (pygame.image.load("../assets/roots.png"),(387, 36))

beans = [pygame.image.load("../assets/bean_growth/bean_{}.png".format(index)) for index in range(0,5)]

from collections import namedtuple
Leave = namedtuple("leave", "x, y, image, offset_x, offset_y")

class Plant:
    LEAVES = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4

    def __init__(self, pos, soil_moisture=100, model=cobra.io.read_sbml_model("whole_plant.sbml"), biomass=0.1):
        self.x = pos[0]
        self.y = pos[1]
        self.model = model
        self.model.objective = "leaf_AraCore_Biomass_tx"
        self.growth_rate = 0
        self.soil_moisture = soil_moisture
        self.upgrade_points = 0
        organ_leaf = Leaf(self.x, self.y, "Leaves", self.LEAVES, self.set_target_organ, leaves, mass=0.01)
        organ_stem = Stem(self.x, self.y, "Stem", self.STEM, self.set_target_organ, stem[0], stem[1], mass=0.01, leaf = organ_leaf)
        organ_root = Root(self.x, self.y, "Roots", self.ROOTS, self.set_target_organ, roots[0], roots[1], mass=1)
        organ_starch = Starch(self.x, self.y, "Starch", self.STARCH, self.deactivate_starch_resource, None)
        organ_starch.mass = 100
        self.seedling = Seedling(self.x, self.y, beans, 6)
        self.organs = [organ_leaf, organ_stem, organ_root, organ_starch]
        self.organs[1].update_image_size(2,10)
        self.organs[2].update_image_size(3,20)
        #self.organs[1].targets = [(699, 821), (713, 801), (706, 778), (709, 741)]    # set up initial growth targets for STEM
        self.target_organ = self.organs[0]
        self.produce_biomass = True
        self.use_starch = False
        self.action = Action(select_organ=self.set_target_organ, add_leave=self.organs[0].activate_add_leaf, add_stem=None)
        self.recalc_growth_rate()
        # Fix env constraints
        self.model.reactions.get_by_id("leaf_Photon_tx").bounds = (0,self.get_leaf_photon())

        # Autotroph environment
        '''
        ATP = (
                0.0049 * self.model.reactions.get_by_id("leaf_Photon_tx").upper_bound
                + 2.7851
        )
        # Creating Constraint object
        NGAM = self.model.problem.Constraint(
            (
                    model.reactions.get_by_id("leaf_ATPase_tx").flux_expression
                    + model.reactions.get_by_id("root_ATPase_tx").flux_expression
                    + model.reactions.get_by_id("stem_ATPase_tx").flux_expression
            ),
            ub=ATP,
            lb=ATP,
        )
        #self.model.add_cons_vars([NGAM])
        '''

    def get_maintainance_cost_hour(self):
        # 1000ms ingame are 4 min realtime  -> factor 240
        # use fixed until working numbers
        #NADPH_cost_gramm = 2.56 * 0.50718 * self.get_biomass()
        #ATP_cost_gramm = 7.27 * 0.744416 * self.get_biomass()

        #cost_day = NADPH_cost_gramm + ATP_cost_gramm
        # use fixed until model is right
        maintenance = 0.0049 * self.model.reactions.get_by_id("leaf_Photon_tx").upper_bound + 2.7851
        return 0.01

    def set_reaction_bound(self, reaction, ub, lb):
        self.model.reactions.get_by_id(reaction).bounds = (ub, lb)

    def get_growth_rate(self):
        growth_rate = 0
        for i in range(0,3):
            print(i)
            growth_rate += self.organs[i].growth_rate
        return growth_rate

    def get_leaf_photon(self):
        # Projected Leaf Area (PLA) translates to mass
        max_mass = self.organs[0].thresholds[-1]
        photon = self.organs[0].mass/max_mass * 0.2 # 200 is arbitrary
        return photon

    # growth rate = starch in pool rate
    def activate_starch_objective(self):
        # switches the objective function to burn starch
        if self.produce_biomass:
            self.produce_biomass = False
            self.model.objective = "root_Starch_out_tx"
            self.model.reactions.get_by_id("root_Starch_out_tx").bounds = (0, 1000)
            # make biomass irreversivble
            self.recalc_growth_rate()
        else:
            pass

    # get resources from  starch pool
    # necessary?
    def activate_starch_resource(self):
        # Todo check number max Starch consumption
        max_starch_out = self.organs[3].max_drain
        self.use_starch = True
        self.model.reactions.get_by_id("root_Starch_in_tx").bounds = (0, max_starch_out)
        self.recalc_growth_rate()

    def deactivate_starch_resource(self):
        self.use_starch = False
        self.model.reactions.get_by_id("root_Starch_in_tx").bounds = (0, 0)
        self.recalc_growth_rate()

    # growth rate = biomass in organs
    def activate_biomass_objective(self):
        if self.produce_biomass:
            pass
        else:
            self.produce_biomass = True
            self.model.objective = "leaf_AraCore_Biomass_tx"
            self.model.reactions.get_by_id("root_Starch_out_tx").bounds = (0, 0)
            # make biomass reversible

    def get_biomass(self):
        biomass = 0
        for organ in self.organs:
            biomass += organ.mass
        return biomass - self.organs[3].mass

    def recalc_growth_rate(self):

        self.set_reaction_bound('leaf_Photon_tx', 0, self.get_leaf_photon())

        '''
        MAINTAINANCE GETS BIGGER WITH MASS
        :return:
        '''
        '''
        medium = self.model.medium
        # adjust photon lvl --> leaf_Photon_tx
        x = 196.7 / self.y  # factor to get lumen from y -> y * x = Lumen
        lumen = self.organs[0].get_mean_leaf_height() * x
        # medium['leaf_Photon_tx'] = lumen   # currently no other source of energy

        # adjust soil moistureness --> root_H2O
        root_h2o = 120/100*self.soil_moisture   # gamevalue_max, modelvalue_max, actual gamevalue
        medium['root_H2O_tx'] = root_h2o

        # adjust carbondioxide --> leaf_CO2, root_CO2
        medium['leaf_CO2_tx'] = 20
        medium['root_CO2_tx'] = 0   # Todo ask about how to inspect the flow better, by how much can root_CO2 replace leaf_CO2

        # adjust NO3 --> root_Nitrate
        medium['root_Nitrate_tx'] = 0.5

        # adjust Water --> root_H2O, leaf_H2O
        medium['root_H2O_tx'] = 18.2
        self.model.medium = medium

        # get constraints - mean light lvl, nutrition
        
        Sensitivity Analysis
        --> check biomass function for compounds, remove unnecessary ones from both tx and biomass
        use this to model    {'leaf_Photon_tx': 1000.0,  0 .. 1000 linear, dpeending on height
         'leaf_CO2_tx': 1000.0,     0 .. 120max .. 1000
         'leaf_O2_tx': 1000.0,      no impact
         'root_Ca_tx': 1000.0,      no impact, high humidity or cold temperatures, can induce calcium deficiency
        use this to model    'root_H2O_tx': 1000.0,     0 .. 110max .. 1000, dry days reduce water
         'root_CO2_tx': 1000.0,     no impact
         'root_O2_tx': 1000.0,      0 .. 1max .. 1000
         'root_Pi_tx': 1000.0,      no impact, Phosphate, only source --> no need maybe in biomass
         'root_Mg_tx': 1000.0,      no impact
         'root_Nitrate_tx': 1000.0, no impact
         'root_SO4_tx': 1000.0,     no impact
         'root_NH4_tx': 1000.0,     0 .. 1max .. 1000
         'root_K_tx': 1000.0}       no impact
        :return:
        '''

        # model solution fba
        #  Todo check if slim_optimize is sufficient
        solution = self.model.slim_optimize()
        # growth rate in hours
        self.growth_rate = solution/60/60*240

        # grwoth_rate in seconds to fit the ingame timer, current facor 240 ingame to real time
        #growth_rate = self.growth_rate / 3600 * 240
        # --> use fixed until model is fine
        maintainance_cost_sec = (self.get_maintainance_cost_hour()/60/60*240)
        self.growth_rate = self.growth_rate - maintainance_cost_sec
        #print('GROWTH_RATE_1:', self.growth_rate, ' MAINTAIN: ', maintainance_cost_sec, self.get_leaf_photon())

        if self.use_starch:
            self.growth_rate += self.organs[3].max_drain * self.organs[3].percentage/100

        #print('GROWTH_RATE_2:', self.growth_rate, ' MAINTAIN: ', maintainance_cost_sec)

        for organ in self.organs:
            organ.recalc_growth_rate(self.growth_rate)

    def grow(self):
        if self.use_starch:
            self.organs[3].drain()
        for i in range(0,3):
            self.organs[i].grow()

    def set_target_organ(self, target):
        self.target_organ = self.organs[target-1]
        self.recalc_growth_rate()

    def set_target_organ_leaf(self):
        self.target_organ = self.organs[0]
        self.recalc_growth_rate()

    def set_target_organ_stem(self):
        self.target_organ = self.organs[1]
        self.recalc_growth_rate()

    def set_target_organ_root(self):
        self.target_organ = self.organs[2]
        self.recalc_growth_rate()

    def set_target_organ_starch(self):
        self.target_organ = self.organs[3]
        self.recalc_growth_rate()

    def get_actions(self):
        return self.action

    def update(self):
        self.upgrade_points = 0
        for organ in self.organs:
            self.upgrade_points += organ.upgrade_points
        if self.upgrade_points > 10:
            pygame.time.set_timer(pygame.event.Event(WIN, message="You Won", duration=1), 500, True)

    def handle_event(self, event):
        for organ in self.organs:
            organ.handle_event(event)

    def draw(self, screen):
        self.draw_seedling(screen)
        if self.get_biomass() > self.seedling.max:
            self.organs[1].draw(screen)
            self.organs[2].draw(screen)

    def draw_seedling(self, screen):
        self.seedling.draw(screen, self.get_biomass())

class Seedling:
    def __init__(self, x, y, images, max):
        self.x = x - 256
        self.y = y - 685
        self.images = images
        self.max = max

    def draw(self, screen, mass):
        index = int(len(self.images)/self.max * mass)
        if index >= len(self.images):
            index = len(self.images)-1
        screen.blit(self.images[index], (self.x, self.y))

class Organ:
    def __init__(self, x, y, name, organ_type,callback=None, image=None, pivot=None, mass=1.0, growth_rate=0, thresholds=None, rect=None):
        if thresholds is None:
            thresholds = [10, 15, 20, 25, 30, 35, 40]
        self.x = x
        self.y = y
        self.starch = 100
        self.callback = callback
        self.image = image
        self.pivot = pivot
        self.name = name
        self.type = organ_type
        self.mass = mass
        self.growth_rate = growth_rate
        self.percentage = 0
        self.thresholds = thresholds
        self.active_threshold = 0
        self.upgrade_points = 0
        self.targets = []
        self.rect = rect

    def set_percentage(self, percentage):
        self.percentage = percentage

    def recalc_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate * self.percentage/100

    def add_growth_target(self, point=None):
        if point is None:
            point = (random.randint(-10, 10), random.randint(1, 10))
        # no duplicate y allowed
        for target in self.targets:
            if point[1] >= target[1]:
                return False
        self.targets.append(point)
        return True

    def get_rect(self):
        if self.image:
            x = self.x - self.pivot[0] if self.pivot else self.x
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(x, y, self.image.get_width(), self.image.get_height())
        else:
            rect = pygame.Rect(0,0,0,0)
        return [rect]

    def grow(self):
        '''
        growthrate -> sliderval
        '''
        self.mass += self.growth_rate * gram_mol * self.mass * GAME_SPEED
        # if reached a certain mass, gain one exp point, increase threshold
        if self.mass > self.thresholds[self.active_threshold]:
            #self.add_growth_target()
            self.reach_threshold()
            #self.active_threshold = self.thresholds[self.thresholds.index(self.active_threshold) + 1]

    def reach_threshold(self):
        self.upgrade_points += 1
        if self.active_threshold >= len(self.thresholds):
            return
        else:
            self.update_image_size()
            pygame.mixer.music.play(0)
            self.active_threshold += 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            # point = (event.pos[0] - (root_size / 2) - (root_size / 10), event.pos[1])
            # print("point:", event.pos, " rect:", rect, "rootS:", root_size)
            # If the rect collides with the mouse pos.
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    self.callback(self.type)

    def get_threshold(self):
        return self.thresholds[self.active_threshold]

    def add_target(self, pos):
        self.targets.append((pos[0], pos[1]))

    def draw(self, screen):
        if not self.pivot:
            self.pivot = (0,0)
        if self.image:
            screen.blit(self.image,(self.x - self.pivot[0], self.y - self.pivot[1]))

    def update_image_size(self, factor=3, base=20):
        if self.image:
            old_size = self.image.get_size()
            organ_size_ratio = old_size[1] / old_size[0]
            image_size = int((self.active_threshold + factor) * base)
            scaled_image = pygame.transform.scale(self.image, (image_size, int(image_size * organ_size_ratio)))
            new_size = scaled_image.get_size()
            old_new_ratio = (new_size[0] / old_size[0], new_size[1] / old_size[1])
            self.pivot = (self.pivot[0] * old_new_ratio[0], self.pivot[1] * old_new_ratio[1])
            self.image = scaled_image


class Leaf(Organ):
    def __init__(self, x, y, name, organ_type, callback, images, mass):
        super().__init__(x, y, name, organ_type, mass=mass)
        self.leaves = []
        self.callback = callback
        self.images = images
        self.can_add_leaf = False

    def activate_add_leaf(self):
        if not self.active_threshold >= len(self.targets):
            return
        self.can_add_leaf = True

    def append_leaf(self, pos):
        if not self.active_threshold >= len(self.targets):
            return
        if pos[0] - self.x -   10 < 0:
            random_int = random.randrange(0,len(leaves)-1,2)
            image = leaves[random_int]
            offset = pivot_pos[random_int]
        else:
            random_int = random.randrange(1,len(leaves),2)
            image = leaves[random_int]
            offset = pivot_pos[random_int]
        self.leaves.append(Leave(pos[0], pos[1], image[0], offset[0], offset[1]))
        self.can_add_leaf = False

    def get_rect(self):
        return [leave.image.get_rect(topleft=(leave.x, leave.y)) for leave in self.leaves]

    # depending on the mean height of all leaves, 0 .. 1000
    def get_mean_leaf_height(self):
        return sum(self.y - leaf.y for leaf in self.leaves)/len(self.leaves) if len(self.leaves) > 0 else 0

    def update_image_size(self, factor=8, base=3):
        leave_size = int((self.active_threshold + base) * factor)
        for leave in self.leaves:
            old_size = leave.image.get_rect(topleft=(leave.x, leave.y))
            scaled_leaf = pygame.transform.scale(leave.image, (leave_size, leave_size))
            new_size = scaled_leaf.get_rect(topleft=(leave.x, leave.y))
            ratio = (new_size[2] / old_size[2], new_size[3] / old_size[3])
            leave.offset_x = leave.offset_x * ratio[0]
            leave.offset_y = leave.offset_y * ratio[1]
            leave.image = scaled_leaf

    def draw(self, screen):
        for leaf in self.leaves:
            screen.blit(leaf.image, (leaf.x-leaf.offset_x, leaf.y-leaf.offset_y))


class Root(Organ):
    def __init__(self, x, y, name, organ_type, callback, image, pivot, mass):
        super().__init__(x, y, name, organ_type, callback, image, pivot, mass=mass)


class Stem(Organ):
    def __init__(self, x, y, name, organ_type, callback, image, pivot, leaf, mass):
        super().__init__(x, y, name, organ_type, callback, image, pivot, mass=mass)
        self.leaf = leaf

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            # point = (event.pos[0] - (root_size / 2) - (root_size / 10), event.pos[1])
            # print("point:", event.pos, " rect:", rect, "rootS:", root_size)
            # If the rect collides with the mouse pos.
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    if self.leaf.can_add_leaf:
                        self.leaf.append_leaf(event.pos)
                        return
                    self.callback(self.type)  # Call the function.

class Starch(Organ):
    '''
    @thresholds are capacities at given lvl
    '''
    def __init__(self, x, y, name, organ_type, callback, image):
        super().__init__(x, y, name, organ_type, callback, image, thresholds=[100, 200, 300, 400])
        self.max_drain = 0.1
        self.toggle_button = None

    def grow(self):
        delta = self.mass + self.growth_rate*GAME_SPEED
        if delta >= self.thresholds[self.active_threshold]:
            self.mass = self.thresholds[self.active_threshold]
            pass
        else:
            self.mass += self.growth_rate * GAME_SPEED

    def recalc_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate

    def drain(self):
        delta = self.mass - self.max_drain * self.percentage/100
        if delta < 0:
            self.toggle_button.deactivate()
        else:
            self.mass = delta

    def get_rate(self):
        return self.max_drain * self.percentage/100


class Action:
    def __init__(self, select_organ, add_stem, add_leave):
        self.select_organ = select_organ
        self.add_stem = add_stem
        self.add_leave = add_leave

