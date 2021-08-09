import cobra.test
import random
import pygame

pygame.init()
GAME_SPEED = 1
gram_mol = 0.5124299411
WIN = 1
pivot_pos = [(666, 299), (9, 358), (690, 222), (17, 592), (389, 553), (20, 891), (283, 767), (39, 931)]
leaves = [(pygame.image.load("../assets/leaves/leaf_{index}.png".format(index=i)), pivot_pos[i]) for i in range(0, 7)]
stem = (pygame.image.load("../assets/stem.png"),(15,1063))
roots = (pygame.image.load("../assets/roots.png"),(387, 36))

beans_big = [pygame.image.load("../assets/bean_growth/bean_{}.png".format(index)) for index in range(0,6)]
beans = []
for bean in beans_big:
    beans.append(pygame.transform.scale(bean, (int(bean.get_width()/3), int(bean.get_height()/3))))
plopp = pygame.mixer.Sound('../assets/plopp.wav')


class Plant:
    LEAVES = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4

    def __init__(self, pos, soil_moisture=100, model=cobra.io.read_sbml_model("whole_plant.sbml")):
        self.x = pos[0]
        self.y = pos[1]
        self.model = model
        self.model.objective = "leaf_AraCore_Biomass_tx"
        self.growth_rate = 0
        self.soil_moisture = soil_moisture
        self.upgrade_points = 0
        organ_leaf = Leaf(self.x, self.y, "Leaves", self.LEAVES, self.set_target_organ, self, leaves, mass=0, active=False)
        organ_stem = Stem(self.x, self.y, "Stem", self.STEM, self.set_target_organ, self, stem[0], stem[1], mass=0, leaf = organ_leaf, active=False)
        organ_root = Root(self.x, self.y, "Roots", self.ROOTS, self.set_target_organ, self, roots[0], roots[1], mass=5, active=True)
        organ_starch = Starch(self.x, self.y, "Starch", self.STARCH, self.deactivate_starch_resource, self, None, mass=30, active=True)
        self.seedling = Seedling(self.x, self.y, beans, 6)
        self.organs = [organ_leaf, organ_stem, organ_root, organ_starch]
        self.target_organ = self.organs[2]
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
            growth_rate += self.organs[i].growth_rate
        return growth_rate

    def get_leaf_photon(self):
        # Projected Leaf Area (PLA) translates to mass
        max_mass = self.organs[0].thresholds[-1]
        photon = self.organs[0].mass/max_mass * 0.2 # 0.2 is arbitrary max
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

        # MAINTAINANCE HAS TO GET BIGGER WITH MASS
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
        '''

        # model solution fba
        solution = self.model.slim_optimize()

        self.growth_rate = solution/60/60*240   # growth rate in hours

        # grwoth_rate in seconds to fit the ingame timer, current facor 240 ingame to real time
        # --> use fixed until model is fine
        maintainance_cost_sec = (self.get_maintainance_cost_hour()/60/60*240)
        self.growth_rate = self.growth_rate - maintainance_cost_sec

        if self.use_starch:
            self.growth_rate += self.organs[3].max_drain * self.organs[3].percentage/100
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
        #if self.upgrade_points > 10:
        #    pygame.time.set_timer(pygame.event.Event(WIN, message="You Won", duration=1), 500, True)
        if self.get_biomass() > self.seedling.max-1 and not self.organs[1].active:
            self.organs[1].activate()
            if self.get_biomass() > self.seedling.max and not self.organs[0].active:
                self.organs[0].activate()

    def handle_event(self, event):
        for organ in self.organs:
            organ.handle_event(event)

    def draw(self, screen):
        self.draw_seedling(screen)
        if self.get_biomass() < self.seedling.max:
            return
        for organ in self.organs:
            organ.draw(screen)

    def draw_seedling(self, screen):
        self.seedling.draw(screen, self.get_biomass())

class Seedling:
    def __init__(self, x, y, images, max):
        self.x = x -88
        self.y = y -200
        self.images = images
        self.max = max

    def draw(self, screen, mass):
        index = int(len(self.images)/self.max * mass)
        if index >= len(self.images):
            index = len(self.images)-1
        screen.blit(self.images[index], (self.x, self.y))


class Organ:
    def __init__(self, x, y, name, organ_type,callback=None, plant=None, image=None, pivot=None, mass=1.0, growth_rate=0, thresholds=None, rect=None, active=False):
        if thresholds is None:
            thresholds = [1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40]
        self.x = x
        self.y = y
        self.callback = callback
        self.plant = plant
        self.base_image = image
        self.image = image
        self.pivot = pivot
        self.active = active
        self.name = name
        self.type = organ_type
        self.mass = mass
        self.base_mass = 1
        self.growth_rate = growth_rate
        self.percentage = 0
        self.thresholds = thresholds
        self.active_threshold = 0
        self.level = 0
        self.targets = []
        self.rect = rect
        self.update_image_size()

    def set_percentage(self, percentage):
        self.percentage = percentage

    def recalc_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate * self.percentage/100

    def get_rect(self):
        if self.image:
            x = self.x - self.pivot[0] if self.pivot else self.x
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(x, y, self.image.get_width(), self.image.get_height())
        else:
            rect = pygame.Rect(0,0,0,0)
        return [rect]

    def grow(self):
        if not self.active:
            return
        self.mass += self.growth_rate * gram_mol * self.mass * GAME_SPEED
        # if reached a certain mass, gain one exp point, increase threshold
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def reach_threshold(self):
        if self.active_threshold >= len(self.thresholds)-1:
            return
        self.plant.upgrade_points += 1
        self.level += 1
        self.update_image_size()
        pygame.mixer.Sound.play(plopp)
        self.active_threshold += 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    self.callback(self.type)

    def get_threshold(self):
        return self.thresholds[self.active_threshold]

    def add_target(self, pos):
        self.targets.append((pos[0], pos[1]))

    def activate(self):
        self.mass = self.base_mass
        self.active = True

    def draw(self, screen):
        if not self.pivot:
            self.pivot = (0,0)
        if self.image and self.active:
            screen.blit(self.image,(self.x - self.pivot[0], self.y - self.pivot[1]))

    def update_image_size(self, factor=5, base=40):
        if self.image:
            ratio = self.image.get_height()/self.image.get_width()
            width = (self.active_threshold + factor) * base
            height = int(width * ratio)
            width = int(width)
            self.pivot = (self.pivot[0] * (width/self.image.get_width()), self.pivot[1] * (height/self.image.get_height()))
            self.image = pygame.transform.scale(self.base_image, (width, height))

    '''def add_growth_target(self, point=None):    # unused
            if point is None:
                point = (random.randint(-10, 10), random.randint(1, 10))
            for target in self.targets:
                if point[1] >= target[1]:   # no duplicate y allowed
                    return False
            self.targets.append(point)
            return True'''


class Leaf(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, images, mass, active):
        self.leaves = []
        super().__init__(x, y, name, organ_type, plant=plant, mass=mass, active=active, thresholds=[1,2,3,4,5,6,7,8,9,10,20,30,40])
        self.callback = callback
        self.images = images
        self.can_add_leaf = False

    def activate_add_leaf(self):
        if not self.active_threshold >= len(self.targets):
            return
        self.can_add_leaf = True

    def grow(self):
        growth_per_leaf = (self.growth_rate * gram_mol * self.get_mass() * GAME_SPEED)/len(self.leaves) if len(self.leaves) > 0 else 0
        for leaf in self.leaves:
            leaf["mass"] += growth_per_leaf
        # if reached a certain mass, gain one exp point, increase threshold
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self):
        return sum([leaf["mass"] for leaf in self.leaves])+self.base_mass # basemass for seedling leaves

    def append_leaf(self, highlight):
        pos = (highlight[0], highlight[1])
        dir = highlight[2]
        if dir < 0:
            image_id = random.randrange(0,len(leaves)-1,2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]
        else:
            image_id = random.randrange(1,len(leaves),2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]
        leaf = {"x": pos[0],
                "y": pos[1],
                "image": image[0],
                "offset_x": offset[0],
                "offset_y": offset[1],
                "mass": 0.0001,
                "base_image_id": image_id,
                "direction": dir,
                "growth_index": self.active_threshold} # to get relative size, depending on current threshold - init threshold
        self.update_leaf_image(leaf, init=True)
        self.leaves.append(leaf)
        self.can_add_leaf = False

    def get_rect(self):
        return [leaf["image"].get_rect(topleft=(leaf["x"], leaf["y"])) for leaf in self.leaves]

    # depending on the mean height of all leaves, 0 .. 1000, -> TODO: mass to PLA better
    def get_mean_leaf_height(self):
        return sum(self.y - leaf["y"] for leaf in self.leaves)/len(self.leaves) if len(self.leaves) > 0 else 0

    def update_image_size(self, factor=10, base=30):
        if not self.leaves:
            return
        for leaf in self.leaves:
            self.update_leaf_image(leaf, factor, base)

    def update_leaf_image(self, leaf, factor=10, base=30, init=False):
        base_image = leaves[leaf["base_image_id"]][0]
        base_offset = leaves[leaf["base_image_id"]][1]
        ratio = base_image.get_height() / base_image.get_width()
        threshold = self.active_threshold - leaf["growth_index"] if not init else 0
        new_width = (threshold * factor) + base
        new_height = int(new_width * ratio)
        new_width = int(new_width)
        leaf["offset_x"] = base_offset[0] * (new_width / base_image.get_width())
        leaf["offset_y"] = base_offset[1] * (new_height / base_image.get_height())
        leaf["image"] = pygame.transform.scale(base_image, (new_width, new_height))

    def draw(self, screen):
        for leaf in self.leaves:
            screen.blit(leaf["image"], (leaf["x"]-leaf["offset_x"], leaf["y"]-leaf["offset_y"]))


class Root(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, image, pivot, mass, active):
        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active)

    def update_image_size(self, factor=5, base=25):
        super().update_image_size(factor, base)

class Stem(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, image, pivot, leaf, mass, active):
        self.leaf = leaf
        self.highlight = None
        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            if self.leaf.can_add_leaf:
                mouse_pos = pygame.mouse.get_pos()
                if self.get_rect()[0].collidepoint(mouse_pos):
                    global_x, global_y = pygame.mouse.get_pos()
                    global_pos = (global_x, global_y)
                    x, dir = self.get_image_mask_x(self.get_local_pos(global_pos), self.image)
                    if x is not None:
                        x = self.get_global_x(x)
                        if self.pivot:
                            print("pivot", self.pivot)
                            x -= self.pivot[0]
                        self.highlight = [x, global_y, dir]
            else:
                self.highlight = None
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    if self.leaf.can_add_leaf:
                        self.plant.upgrade_points -= 1
                        if self.highlight:
                            self.leaf.append_leaf(self.highlight)
                        return
                    self.callback(self.type)

    def update_image_size(self, factor=3, base=5):
        super().update_image_size(factor, base)
        if self.leaf:
            for leaf in self.leaf.leaves:
                self.reassign_leaf_x(leaf)

    def get_local_pos(self, pos):
        return (int(pos[0]-(self.x-self.pivot[0])),int(pos[1]-(self.y-self.pivot[1])))

    def get_global_x(self, x):
        return int(x+self.x)

    def reassign_leaf_x(self, leaf):
        global_pos = (leaf["x"], leaf["y"])
        dir = leaf["direction"]
        rect = self.image.get_rect()
        init_x = 0
        if dir > 0:
            init_x = rect[2]-1
        local_pos = self.get_local_pos(global_pos)
        x, dir = self.get_image_mask_x((init_x, local_pos[1]), self.image)
        if x:
            leaf["x"] = self.get_global_x(x)-self.pivot[0]


    def draw(self, screen):
        super().draw(screen)
        pygame.draw.rect(screen, (0,0,0), self.get_rect()[0], width=2)
        if self.highlight:
            size = 10
            pygame.draw.circle(screen, (255,255,255, 180),(int(self.highlight[0]-size/2), int(self.highlight[1]-size/2)), size, width=int(size/3))
            pygame.draw.circle(screen, (255,255,255, 180),(int(self.highlight[0]-size/2), int(self.highlight[1]-size/2)), size/3)



    def get_rect(self):
        if self.image:
            x = (self.x - self.pivot[0] if self.pivot else self.x) -15
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(x, y, self.image.get_width()+30, self.image.get_height())
        else:
            rect = pygame.Rect(0,0,0,0)
        return [rect]

    # buffer is useful for a bigger hitbox, with same img borders
    def get_image_mask_x(self, pos, image):
        x = None
        dir = 0
        rect = image.get_rect()
        middle = int(rect[2]/2)
        i = 0
        if pos[0] < middle: # and pos[0] > 0:
            # left
            dir = -1
            for i in range(rect[0], rect[2]-1, 1):
                #print(i, pos[1], ' image: ', image.get_rect(), image.get_at((i, pos[1])))
                if (image.get_at((i, pos[1]))[3] != 0):
                    x = i
                    break
        elif pos[0] > middle: #and pos[0] < rect[2]:
            # right
            dir = 1
            for i in range(rect[2]-1, rect[0], -1):
                #print(i, pos[1], ' image: ', image.get_rect(), image.get_at((i, pos[1])))
                if (image.get_at((i, pos[1]))[3] != 0):
                    x = i
                    break
        return x, dir

class Starch(Organ):
    '''
    @thresholds are capacities at given lvl
    '''
    def __init__(self, x, y, name, organ_type, callback, plant, image, mass, active):
        super().__init__(x, y, name, organ_type, callback, plant, image, mass=mass, active=active, thresholds=[30, 50, 80, 160, 320])
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

    def draw(self, screen):
        pass

# looks stupid
class Action:
    def __init__(self, select_organ, add_stem, add_leave):
        self.select_organ = select_organ
        self.add_stem = add_stem
        self.add_leave = add_leave

