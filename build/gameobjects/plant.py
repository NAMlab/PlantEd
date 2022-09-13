import cobra.test
import random
import pygame
from data import assets
from utils.spline import Beziere
import config
import math
from utils.particle import ParticleSystem, Particle
from pygame import Rect
from utils.LSystem import LSystem, Letter
from pygame.locals import *
import numpy as np

pygame.init()
gram_mol = 0.5124299411
WIN = pygame.USEREVENT+1
#pivot_pos = [(666, 299), (9, 358), (690, 222), (17, 592), (389, 553), (20, 891), (283, 767), (39, 931)]
pivot_pos = [(286,113),(76,171),(254,78),(19,195),(271,114),(47,114)]
leaves = [(assets.img("leaves/{index}.png".format(index=i)), pivot_pos[i]) for i in range(0, 6)]
#stem = (assets.img("stem.png"), (15, 1063))
#roots = (assets.img("roots.png"), (387, 36))

beans = [assets.img("bean_growth/{}.png".format(index),(150,150)) for index in range(0, 6)]
#beans = []
#for bean in beans_big:
#    beans.append(pygame.transform.scale(bean, (int(bean.get_width()/4), int(bean.get_height()/4))))
plopp = assets.sfx('plopp.wav')
plopp.set_volume(0.4)


class Plant:
    LEAF = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4

    def __init__(self, pos, model, camera, water_grid):
        self.x = pos[0]
        self.y = pos[1]
        self.upgrade_points = 10
        self.model = model
        self.camera = camera
        self.water_grid = water_grid
        organ_leaf = Leaf(self.x, self.y, "Leaves", self.LEAF, self.set_target_organ_leaf, self, leaves, mass=0.1, active=False)
        organ_stem = Stem(self.x, self.y, "Stem", self.STEM, self.set_target_organ_stem, self, mass=0.1, leaf = organ_leaf, active=False)
        organ_root = Root(self.x, self.y, "Roots", self.ROOTS, self.set_target_organ_root, self, mass=0.8, active=True)
        self.organ_starch = Starch(self.x, self.y, "Starch", self.STARCH, self, None, None, mass=20, active=True, model=self.model)
        self.seedling = Seedling(self.x, self.y, beans, 4)
        self.organs = [organ_leaf, organ_stem, organ_root]
        self.target_organ = self.organs[2]
        # Fix env constraints

    def get_growth_rate(self):
        growth_rate = 0.5 if self.get_biomass() < 4 else 0
        for i in range(0,3):
            growth_rate += self.organs[i].growth_rate
        return growth_rate

    def check_organ_level(self):
        lvl = 0
        for organ in self.organs:
            lvl += organ.level
        if lvl >= 20:
            pygame.event.post(pygame.event.Event(WIN))

    def update_growth_rates(self, growth_rates):
        for i in range(0,3):
            # Todo remove cheat
            if self.get_biomass() < 4:
                self.organs[i].update_growth_rate(growth_rates[i]+0.2)
            else:
                self.organs[i].update_growth_rate(growth_rates[i])
        self.organ_starch.update_growth_rate(growth_rates[3])
        self.organ_starch.starch_intake = growth_rates[4]

    def get_biomass(self):
        biomass = 0
        for organ in self.organs:
            biomass += organ.mass
        return biomass

    def get_percentages(self):
        return [organ.percentage for organ in self.organs]

    def get_level(self):
        return sum([organ.level for organ in self.organs])

    # Projected Leaf Area (PLA)
    def get_PLA(self):
        # 0.03152043208186226
        return (self.organs[0].get_mass() * 0.03152043208186226)+self.organs[0].base_mass if len(self.organs[0].leaves) > 0 else 0 #m^2

    def grow(self):
        self.update_growth_rates(self.model.get_rates())
        for organ in self.organs:
            organ.grow()
        self.organ_starch.grow()
        self.organ_starch.drain()

    def set_target_organ_leaf(self):
        self.target_organ = self.organs[0]

    def set_target_organ_stem(self):
        self.target_organ = self.organs[1]

    def set_target_organ_root(self):
        self.target_organ = self.organs[2]

    def set_target_organ_starch(self):
        self.target_organ = self.organ_starch

    def update(self, dt, photon_intake):
        # dirty Todo make beter
        if self.get_biomass() > self.seedling.max and not self.organs[1].active:
            self.organs[1].activate()
            self.organs[0].activate()
            self.organs[2].create_new_root(dir=(0,1))
            #if self.get_biomass() > self.seedling.max and not self.organs[0].active:
        for organ in self.organs:
            organ.update(dt)
        self.organs[0].photon_intake = photon_intake


    def handle_event(self, event):
        for organ in self.organs:
            organ.handle_event(event)
        #self.organ_starch.handle_event(event) not necessary, no visible starch

    def draw(self, screen):
        self.draw_seedling(screen)
        if self.get_biomass() < self.seedling.max:
            self.organs[2].draw(screen)
            return
        for organ in self.organs:
            organ.draw(screen)

    def draw_seedling(self, screen):
        self.seedling.draw(screen, self.get_biomass())


class Seedling:
    def __init__(self, x, y, images, max):
        self.x = x -100
        self.y = y -20
        self.images = images
        self.max = max

    def draw(self, screen, mass):
        index = int(len(self.images)/self.max * (mass))-1
        if index >= len(self.images):
            index = len(self.images)-1
        screen.blit(self.images[index], (self.x, self.y))


class Organ:
    def __init__(self, x, y, name, organ_type,callback=None, plant=None, image=None, pivot=None, mass=1, growth_rate=0, thresholds=None, rect=None, active=False, base_mass=1):
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
        self.base_mass = base_mass
        self.growth_rate = growth_rate
        self.percentage = 0
        self.thresholds = thresholds
        self.active_threshold = 0
        self.level = 0
        self.update_image_size()
        self.skills = []

    def update(self, dt):
        pass

    def set_percentage(self, percentage):
        self.percentage = percentage

    def update_growth_rate(self, growth_rate):
        self.growth_rate = self.mass * gram_mol * growth_rate

    def get_rate(self):
        return self.growth_rate

    def get_rect(self):
        if self.image:
            x = self.x - self.pivot[0] if self.pivot else self.x
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(x, y+self.plant.camera.offset_y, self.image.get_width(), self.image.get_height())
        else:
            rect = pygame.Rect(0,0,0,0)
        return [rect]

    def grow(self):
        if not self.active:
            return
        self.mass += self.growth_rate
        # if reached a certain mass, gain one exp point, increase threshold
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def reach_threshold(self):
        if self.active_threshold >= len(self.thresholds)-1:
            return
        self.plant.upgrade_points += 1
        self.level += 1
        self.plant.check_organ_level()
        self.update_image_size()
        pygame.mixer.Sound.play(plopp)
        self.active_threshold += 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    self.callback()

    def get_threshold(self):
        return self.thresholds[self.active_threshold]

    def activate(self):
        if self.mass < self.base_mass:
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
        self.photon_intake = 0
        self.base_mass = 1
        self.can_add_leaf = False
        self.particle_system = (
            ParticleSystem(20, spawn_box=Rect(500, 500, 50, 20), lifetime=8, color=config.YELLOW,
                           apply_gravity=False,
                           speed=[0, -1], spread=[1, -1], active=False))
        self.particle_systems = []

    def handle_event(self, event):
        '''if event.type == pygame.KEYDOWN and event.key == pygame.K_u:
            self.particle_system.activate()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_j:
            self.particle_system.deactivate()'''
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.callback()

    def activate_add_leaf(self):
        self.can_add_leaf = True

    def check_can_add_leaf(self):
        if len(self.leaves) <= self.active_threshold:
            return True

    def remove_leaf(self, leaf=None):
        if not leaf:
            leaf = self.get_random_leave()
        self.leaves.remove(leaf)


    def get_random_leave(self):
        if len(leaves) > 0:
            return self.leaves[random.randint(0,len(self.leaves)-1)]
        else:
            return None

    def update_growth_rate(self, growth_rate):
        self.growth_rate = self.get_mass() * gram_mol * growth_rate

    def grow(self):
        if self.growth_rate <= 0:
            return
        # get leaf age, if too old -> stop growth, then die later
        growable_leaves = []
        for leaf in self.leaves:
            if leaf["lifetime"]>leaf["age"]:
                growable_leaves.append(leaf)
            # if max age*2 -> kill leaf

        growth_per_leaf = self.growth_rate/len(growable_leaves) if len(growable_leaves) > 0 else 0
        for leaf in growable_leaves:
            leaf["mass"] += growth_per_leaf
            leaf["age"] += 1 #seconds

        #print(leaf["age"],leaf["lifetime"])

        # age 0
        # max_age 1000

        # if reached a certain mass, gain one exp point, increase threshold
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self):
        return sum([leaf["mass"] for leaf in self.leaves])+self.base_mass # basemass for seedling leaves

    def append_leaf(self, highlight):
        time = pygame.time.get_ticks()
        pos = (highlight[0], highlight[1])
        dir = highlight[0] - pygame.mouse.get_pos()[0]
        if dir > 0:
            image_id = random.randrange(0,len(leaves)-1,2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]
        else:
            image_id = random.randrange(1,len(leaves),2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]
        leaf = {"x": pos[0],
                "y": pos[1],
                "t": highlight[2],
                "image": image[0],
                "offset_x": offset[0],
                "offset_y": offset[1],
                "mass": 0.0001,
                "base_image_id": image_id,
                "direction": dir,
                "age": 0,
                "lifetime": 60*60*24/240,
                "growth_index": self.active_threshold} # to get relative size, depending on current threshold - init threshold
        self.update_leaf_image(leaf, init=True)
        self.particle_systems.append(ParticleSystem(20, spawn_box=Rect(leaf["x"], leaf["y"], 0, 0),
                                                    lifetime=6, color=config.YELLOW, apply_gravity=False,
                                                    speed=[0, -5], spread=[5, 5], active=False))
        self.leaves.append(leaf)
        self.can_add_leaf = False

    def get_rect(self):
        return [leaf["image"].get_rect(topleft=(leaf["x"]-leaf["offset_x"], leaf["y"]-leaf["offset_y"]+self.plant.camera.offset_y)) for leaf in self.leaves]

    # depending on the mean height of all leaves, 0 .. 1000, -> TODO: mass to PLA better
    def get_mean_leaf_height(self):
        return sum(self.y - leaf["y"] for leaf in self.leaves)/len(self.leaves) if len(self.leaves) > 0 else 0

    def update(self, dt):
        for system in self.particle_systems:
            system.update(dt)
        for i in range(0, len(self.leaves)):
            box = self.particle_systems[i].spawn_box
            size = self.leaves[i]["image"].get_size()
            offset_x = self.leaves[i]["offset_x"]
            offset_y = self.leaves[i]["offset_y"]
            self.particle_systems[i].spawn_box = (int(self.leaves[i]["x"]-offset_x+size[0]/2),
                                                  int(self.leaves[i]["y"]-offset_y+size[1]/2), 0, 0)
            if self.photon_intake > 0:
                adapted_pi = self.photon_intake/50*3 + 5
                self.particle_systems[i].lifetime=adapted_pi
                self.particle_systems[i].activate()
            else:
                self.particle_systems[i].deactivate()


    def update_image_size(self, factor=7, base=80):
        for leaf in self.leaves:
            self.update_leaf_image(leaf, factor, base)

    def update_leaf_image(self, leaf, factor=7, base=80, init=False):
        base_image = leaves[leaf["base_image_id"]][0]
        base_offset = leaves[leaf["base_image_id"]][1]
        ratio = base_image.get_height() / base_image.get_width()
        threshold = self.active_threshold - leaf["growth_index"] #if not init else 0
        print(threshold)
        new_width = (threshold * factor) + base
        new_height = int(new_width * ratio)
        new_width = int(new_width)
        leaf["offset_x"] = base_offset[0] * (new_width / base_image.get_width())
        leaf["offset_y"] = base_offset[1] * (new_height / base_image.get_height())
        leaf["image"] = pygame.transform.scale(base_image, (new_width, new_height))

    def draw(self, screen):
        if self.can_add_leaf:
            x,y = pygame.mouse.get_pos()
            screen.blit(assets.img("leaf_small.png",(128,128)), (x,y-self.plant.camera.offset_y))

        for leaf in self.leaves:
            screen.blit(leaf["image"], (leaf["x"]-leaf["offset_x"], leaf["y"]-leaf["offset_y"]))

        if self.type == self.plant.target_organ.type:
            rects = self.get_rect()
            outlines = self.get_outlines()
            for i in range(0,len(self.leaves)):
                s = pygame.Surface((64, 64),pygame.SRCALPHA)
                pygame.draw.lines(s, (255,255,255),True,outlines[i],2)
                #pygame.draw.rect(screen, (255, 255, 255), (rects[i][0],rects[i][1],rects[i][2],rects[i][3]), 2)
                screen.blit(s, (self.leaves[i]["x"]-self.leaves[i]["offset_x"], self.leaves[i]["y"]-self.leaves[i]["offset_y"]))

        for system in self.particle_systems:
            system.draw(screen)

    def get_outlines(self):
        outlines = []
        for leaf in self.leaves:
            mask = pygame.mask.from_surface(leaf["image"])
            #mask.fill()
            outline = mask.outline()
            outlines.append(outline)
        return outlines


class Root(Organ):

    def __init__(self, x, y, name, organ_type, callback, plant, image=None, pivot=None, mass=0, active=False):
        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active)
        #self.curves = [Beziere([(self.x, self.y), (self.x - 20, self.y + 50), (self.x + 70, self.y + 100)],color=config.WHITE, res=10, width=mass+5)]
        self.selected = 0
        self.root_tier = 0
        #positions = [(x,y+45)]
        #directions = [(0,1)]
        root_grid = np.zeros(self.plant.water_grid.get_shape())
        water_grid_pos = self.plant.water_grid.pos

        self.ls = LSystem(root_grid, water_grid_pos)

        self.tabroot = False # if not tabroot, its fibroot -> why skill it then?

    def grow_roots(self):
        pass

    def update_image_size(self, factor=5, base=25):
        super().update_image_size(factor, base)

    def get_outline(self):
        outlines = pygame.mask.from_surface(self.image).outline()
        return outlines

    def update(self, dt):
        self.ls.update(self.mass)
        self.plant.model.apexes = self.ls.apexes
        #for curve in self.curves:
        #    curve.update(dt)

    def create_new_root(self, mouse_pos=None, dir=None):
        dist=None
        if mouse_pos:
            dist = math.sqrt(((mouse_pos[0]-self.x)**2+(mouse_pos[1]-self.y)**2))
            print(dist)
        pos = (self.x-5,self.y+40)
        if not dir and mouse_pos:
            dir = (mouse_pos[0] - self.x, mouse_pos[1]-(self.y+45))
        self.ls.create_new_first_letter(dir, pos, self.mass, dist=dist)

    '''def set_root_tier(self, root_tier=1):
        self.ls.set_root_tier(root_tier)'''

    def get_root_grid(self):
        return self.ls.root_grid

    def handle_event(self, event):
        self.ls.handle_event(event)

        #if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
        #    self.ls.create_new_first_letter((-1,0),pygame.mouse.get_pos(), self.mass)

    def reach_threshold(self):
        super().reach_threshold()

    def draw(self, screen):
        if self.type == self.plant.target_organ.type:
            #pygame.draw.line(screen, config.WHITE, (self.x + 1, self.y + 30), (self.x, self.y + 45), 8)
            self.ls.draw_highlighted(screen)
        else:
            self.ls.draw(screen)
        #pygame.draw.line(screen, config.BLACK, (self.x + 1, self.y + 30), (self.x, self.y + 45), 6)
        #pygame.draw.line(screen, config.WHITE, (self.x + 1, self.y + 30), (self.x, self.y + 45), 4)
        #for curve in self.curves:
        #    curve.draw(screen)
        '''if not self.pivot:
            self.pivot = (0,0)
        
            outlines = self.get_outline()
            s = pygame.Surface((self.image.get_width(),self.image.get_height()),pygame.SRCALPHA)
            pygame.draw.lines(s,config.WHITE, True,outlines,2)
            screen.blit(s,(self.x - self.pivot[0], self.y - self.pivot[1]))

        if self.image and self.active:
            screen.blit(self.image,(self.x - self.pivot[0], self.y - self.pivot[1]))
'''

class Stem(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, image=None, pivot=None, leaf=None, mass=0, active=False):
        self.leaf = leaf
        self.width = 15
        self.highlight = None
        self.flower = False
        self.sunpos = (0,0)
        self.sunflower = assets.img("sunflower.png",(64,64))
        self.sunflower_pos = (0,0)
        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active, base_mass=1)
        self.curve = Beziere([(self.x-5, self.y+40), (self.x-5, self.y), (self.x - 15, self.y - 50), (self.x+13, self.y - 150), (self.x+3, self.y - 190)])

    def update(self, dt):
        self.curve.update(dt)
        self.update_leaf_positions()
        self.update_sunflower_position()

    def reach_threshold(self):
        super().reach_threshold()
        tip = self.curve.get_point(1)
        if self.active_threshold > 1 and self.flower == False:
            self.flower = True
            self.update_sunflower_position()
        self.curve.grow_point((tip[0]+(random.randint(0,2)-1)*50,tip[1]+(-1*random.randint(40,60))))
        self.curve.width += 1

    def add_thorn(self, pos, dir):
        if dir > 0:
            image = thorn_r
        else:
            image = thorn_l
        self.thorns.append({"position": pos,
                            "image" : image})

    def handle_event(self, event):
        self.curve.handle_event(event)
        if event.type == KEYDOWN and event.key == pygame.K_o:
            self.curve.update_tip(point=self.sunpos)
        if event.type == pygame.MOUSEMOTION:
            if self.leaf.can_add_leaf:
                x,y = pygame.mouse.get_pos()
                y -= self.plant.camera.offset_y
                t = self.curve.find_closest((x,y))
                point = self.curve.get_point(t)
                self.highlight = (point[0],point[1],t)
            else:
                self.highlight = None
        if event.type == pygame.MOUSEBUTTONUP:
            width = self.width+25 if self.leaf.can_add_leaf else self.width + 5
            for rect in self.curve.get_rects(width, self.plant.camera.offset_y):
                if rect.collidepoint(pygame.mouse.get_pos()):
                    if self.highlight:
                        self.leaf.append_leaf(self.highlight)
                        return
                    self.callback()

    def update_image_size(self, factor=3, base=5):
        # there is no image, just beziere
        pass
        #super().update_image_size(factor, base)
        #if self.leaf:
            #for leaf in self.leaf.leaves:
                #self.reassign_leaf_x(leaf)

    def update_sunflower_position(self):
        if self.flower:
            pos = self.curve.get_point(1)
            self.sunflower_pos = (pos[0]-32,pos[1]-32)

    def update_leaf_positions(self):
        for leaf in self.leaf.leaves:
            leaf["x"],leaf["y"] = self.curve.get_point(leaf["t"])

    def get_local_pos(self, pos):
        return (int(pos[0]-(self.x-self.pivot[0])),int(pos[1]-(self.y-self.pivot[1])))

    def get_global_x(self, x):
        return int(x+self.x)

    def reassign_leaf_x(self, leaf):
        global_pos = (leaf["x"], leaf["y"])
        dir = leaf["direction"]
        rect = self.get_rect()
        rects = self.curve.get_rects()
        init_x = 0
        if dir > 0:
            init_x = rect[2]-1
        local_pos = self.get_local_pos(global_pos)
        x, dir = self.get_image_mask_x((init_x, local_pos[1]), self.image)
        if x:
            leaf["x"] = self.get_global_x(x)-self.pivot[0]


    def draw(self, screen):
        if self.plant.target_organ.type == self.type:
            self.curve.draw_highlighted(screen)
        else:
            self.curve.draw(screen)
        if self.highlight:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mouse_y = mouse_y-self.plant.camera.offset_y
            dist_to_stem = math.sqrt((mouse_x - self.highlight[0])**2 + (mouse_y - self.highlight[1])**2)
            color = config.GRAY if dist_to_stem > 20 else config.WHITE
            pygame.draw.line(screen, color, (self.highlight[0],self.highlight[1]),(mouse_x,mouse_y))
            pygame.draw.circle(screen, color, (int(self.highlight[0]), int(self.highlight[1])), 10)
        if self.flower:
            screen.blit(self.sunflower,self.sunflower_pos)

    def get_rect(self):
        if self.image:
            x = (self.x - self.pivot[0] if self.pivot else self.x) -15
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(x, y+self.plant.camera.offset_y, self.image.get_width()+30, self.image.get_height())
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
    def __init__(self, x, y, name, organ_type, callback, plant, image, mass, active, model):
        super().__init__(x, y, name, organ_type, callback, plant, image, mass=mass, active=active, thresholds=[50,100,500,1000])
        self.toggle_button = None
        self.model = model

    def grow(self):
        delta = self.growth_rate
        if delta >= self.thresholds[self.active_threshold]:
            self.mass = self.thresholds[self.active_threshold]
        else:
            self.mass += delta

    def update_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate

    def drain(self):
        delta = self.mass - self.model.get_rates()[4] * 0.3
        if delta < 0:
            self.mass = 0
            self.toggle_button.deactivate()
        else:
            self.mass = delta