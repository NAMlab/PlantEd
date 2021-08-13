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
    LEAF = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4

    def __init__(self, pos, model):
        self.x = pos[0]
        self.y = pos[1]
        self.upgrade_points = 0
        self.model = model
        self.growth_rate = self.model.get_rates()[0]  # in seconds ingame second = second * 240
        organ_leaf = Leaf(self.x, self.y, "Leaves", self.LEAF, self.set_target_organ, self, leaves, mass=0, active=False)
        organ_stem = Stem(self.x, self.y, "Stem", self.STEM, self.set_target_organ, self, stem[0], stem[1], mass=0, leaf = organ_leaf, active=False)
        organ_root = Root(self.x, self.y, "Roots", self.ROOTS, self.set_target_organ, self, roots[0], roots[1], mass=5, active=True)
        self.organ_starch = Starch(self.x, self.y, "Starch", self.STARCH, self, None, None, mass=30, active=True)
        self.seedling = Seedling(self.x, self.y, beans, 6)
        self.organs = [organ_leaf, organ_stem, organ_root]
        self.target_organ = self.organs[2]
        # Fix env constraints

    def get_growth_rate(self):
        growth_rate = 0
        for i in range(0,3):
            growth_rate += self.organs[i].growth_rate
        return growth_rate

    def update_growth_rates(self, growth_rate):
        for organ in self.organs:
            organ.update_growth_rate(growth_rate[0])
        self.organ_starch.update_growth_rate(growth_rate[1])
        self.organ_starch.starch_intake = growth_rate[2]

    def get_biomass(self):
        biomass = 0
        for organ in self.organs:
            biomass += organ.mass
        return biomass

    # Projected Leaf Area (PLA)
    def get_PLA(self):
        # 0.03152043208186226
        return self.organs[0].get_mass() * 0.03152043208186226

    def grow(self):
        self.update_growth_rates(self.model.get_rates())
        for organ in self.organs:
            organ.grow()
        self.organ_starch.grow()
        self.organ_starch.drain()

    def set_target_organ(self, target):
        self.target_organ = self.organs[target - 1]

    def set_target_organ_leaf(self):
        self.target_organ = self.organs[0]

    def set_target_organ_stem(self):
        self.target_organ = self.organs[1]

    def set_target_organ_root(self):
        self.target_organ = self.organs[2]

    def set_target_organ_starch(self):
        self.target_organ = self.organ_starch

    def update(self):
        if self.get_biomass() > self.seedling.max-1 and not self.organs[1].active:
            self.organs[1].activate()
            if self.get_biomass() > self.seedling.max and not self.organs[0].active:
                self.organs[0].activate()

    def handle_event(self, event):
        for organ in self.organs:
            organ.handle_event(event)
        #self.organ_starch.handle_event(event) not necessary, no visible starch

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
        self.base_mass = 0.02
        self.growth_rate = growth_rate
        self.percentage = 0
        self.thresholds = thresholds
        self.active_threshold = 0
        self.level = 0
        self.update_image_size()

    def set_percentage(self, percentage):
        self.percentage = percentage

    def update_growth_rate(self, growth_rate):
        self.growth_rate = self.mass * gram_mol * growth_rate * self.percentage/100

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
        self.mass += self.growth_rate * GAME_SPEED
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


class Leaf(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, images, mass, active):
        self.leaves = []
        super().__init__(x, y, name, organ_type, plant=plant, mass=mass, active=active, thresholds=[1,2,3,4,5,6,7,8,9,10,20,30,40])
        self.callback = callback
        self.images = images
        self.can_add_leaf = False

    def activate_add_leaf(self):
        if not self.active_threshold >= len(self.leaves):
            return
        self.can_add_leaf = True

    def update_growth_rate(self, growth_rate):
        self.growth_rate = self.get_mass() * gram_mol * growth_rate * self.percentage/100

    def grow(self):
        growth_per_leaf = (self.growth_rate * GAME_SPEED)/len(self.leaves) if len(self.leaves) > 0 else 0
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
    def __init__(self, x, y, name, organ_type, callback, plant, image, mass, active):
        super().__init__(x, y, name, organ_type, callback, plant, image, mass=mass, active=active, thresholds=[30, 50, 80, 160, 320])
        self.starch_intake = 0
        self.toggle_button = None

    def grow(self):
        delta = self.growth_rate*GAME_SPEED
        if delta >= self.thresholds[self.active_threshold]:
            self.mass = self.thresholds[self.active_threshold]
        else:
            self.mass += delta

    def update_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate

    def drain(self):
        delta = self.mass - self.starch_intake * self.percentage/100
        if delta < 0:
            self.mass = 0
            self.toggle_button()
        else:
            self.mass = delta

    def get_intake(self):
        return self.starch_intake * self.percentage/100