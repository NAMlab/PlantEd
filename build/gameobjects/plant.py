import random
import pygame
from data import assets
from utils.spline import Beziere, Cubic, Cubic_Tree
import config
import math
from utils.particle import ParticleSystem, Particle
from pygame import Rect
from utils.LSystem import LSystem, Letter
from pygame.locals import *
import numpy as np
from utils.gametime import GameTime

pygame.init()
gram_mol = 0.5124299411
WIN = pygame.USEREVENT+1
#pivot_pos = [(666, 299), (9, 358), (690, 222), (17, 592), (389, 553), (20, 891), (283, 767), (39, 931)]
pivot_pos = [(286,113),(76,171),(254,78),(19,195),(271,114),(47,114)]
leaves = [(assets.img("leaves/{index}.PNG".format(index=i)), pivot_pos[i]) for i in range(0, 6)]
flowers = [(assets.img("sunflowers/{index}.PNG".format(index=i),(64,64))) for i in range(0, 3)]
#flowers = [assets.img("flowers/flower.PNG",(64,64))]
#stem = (assets.img("stem.png"), (15, 1063))
#roots = (assets.img("roots.png"), (387, 36))

beans = [assets.img("bean_growth/{}.PNG".format(index),(150,150)) for index in range(0, 6)]
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
    FLOWER = 5

    def __init__(self, pos, model, camera, water_grid, growth_boost=1, upgrade_points=10):
        self.x = pos[0]
        self.y = pos[1]
        self.upgrade_points = upgrade_points
        self.model = model
        self.camera = camera
        self.water_grid = water_grid
        self.growth_boost = growth_boost
        self.danger_mode = False
        self.gametime = GameTime.instance()
        organ_leaf = Leaf(self.x, self.y, "Leaves", self.LEAF, self.set_target_organ_leaf, self, leaves, mass=0.1, active=False)
        organ_flower = Flower(self.x, self.y, "Roots", self.FLOWER, self.set_target_organ_flower, self, flowers, mass=0.1, active=False)
        organ_stem = Stem(self.x, self.y, "Stem", self.STEM, self.set_target_organ_stem, self, mass=0.1, leaf = organ_leaf, flower = organ_flower, active=False)
        organ_root = Root(self.x, self.y, "Roots", self.ROOTS, self.set_target_organ_root, self, mass=0.8, active=True)
        self.organ_starch = Starch(self.x, self.y, "Starch", self.STARCH, self, None, None, mass=1000000, active=True, model=self.model)
        self.seedling = Seedling(self.x, self.y, beans, 4)
        self.organs = [organ_leaf, organ_stem, organ_root, organ_flower]
        self.target_organ = self.organs[2]
        # Fix env constraints

    def check_organ_level(self):
        lvl = 0
        for organ in self.organs:
            lvl += organ.level


    # convert flux/mikromol to gramm
    def update_growth_rates(self, growth_rates):
        sum_rates = sum(growth_rates)
        if self.get_biomass() > 4 and sum_rates <= 0:
            self.danger_mode = True
        else:
            self.danger_mode = False
        for i in range(0, 3):
            self.organs[i].update_growth_rate((growth_rates[i]))
        self.organ_starch.update_growth_rate(growth_rates[3])
        self.organ_starch.starch_intake = growth_rates[4]
        self.organs[3].update_growth_rate(growth_rates[5])

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
        # 0.03152043208186226 as a factor to get are from dry mass
        return (self.organs[0].get_mass()+self.organs[0].base_mass) * 0.03152043208186226 if len(self.organs[0].leaves) > 0 else 0 #m^2

    def grow(self, dt):
        for organ in self.organs:
            organ.grow(dt)
        self.organ_starch.grow(dt)
        self.organ_starch.drain(dt)

    def set_target_organ_leaf(self):
        self.target_organ = self.organs[0]

    def set_target_organ_stem(self):
        self.target_organ = self.organs[1]

    def set_target_organ_root(self):
        self.target_organ = self.organs[2]
    def set_target_organ_flower(self):
        self.target_organ = self.organs[3]

    def set_target_organ_starch(self):
        self.target_organ = self.organ_starch

    def update(self, dt, photon_intake):
        # dirty Todo make beter
        self.grow(dt)
        if self.danger_mode:
            for organ in self.organs:
                organ.drain(0.00001,self.gametime.GAMESPEED, dt)
        if self.get_biomass() > self.seedling.max and not self.organs[1].active:
            self.organs[1].activate()
            self.organs[0].activate()
            #if self.get_biomass() > self.seedling.max and not self.organs[0].active:
        for organ in self.organs:
            organ.update(dt)
        self.organs[0].photon_intake = photon_intake

        self.organ_starch.update_starch_max(self.get_biomass()*1000+1000000)


    def handle_event(self, event):
        for organ in self.organs:
            organ.handle_event(event)
        #self.organ_starch.handle_event(event) not necessary, no visible starch

    def draw(self, screen):
        self.draw_seedling(screen)
        if self.get_biomass() < self.seedling.max:
            self.organs[2].draw(screen)
            return

        self.organs[2].draw(screen)
        self.organs[1].draw(screen)
        self.organs[0].draw(screen)
        self.organs[3].draw(screen)

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
        self.growth_rate = gram_mol * growth_rate

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

    def drain(self, rate, gamespeed, dt):
        if self.mass > 1:
            self.mass -= (rate + rate*0.01*self.mass) * dt * gamespeed

    def grow(self, dt):
        if not self.active:
            return
        self.mass += self.growth_rate*dt
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
        self.target_leaf = 0
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
        if self.type == self.plant.target_organ.type:
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                rects = self.get_rect()
                for i in range(len(rects)):
                    if rects[i].collidepoint(mouse_pos):
                        self.target_leaf = i
            if event.type == pygame.KEYDOWN and event.key == pygame.K_i:
                self.leaves.pop(self.target_leaf)

    def activate_add_leaf(self):
        self.can_add_leaf = True

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
        self.growth_rate = gram_mol * growth_rate

    def yellow_leaf(self, image, alpha):
        ghost_image = image.copy()
        ghost_image.fill((0, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        shaded_image = image.copy()
        shaded_image.blit(ghost_image, (0, 0))
        return shaded_image

    def grow(self, dt):
        if self.growth_rate <= 0:
            return
        # get leaf age, if too old -> stop growth, then die later
        growable_leaves = []
        for leaf in self.leaves:
            if leaf["lifetime"]>leaf["age"]:
                growable_leaves.append(leaf)
            # if max age*2 -> kill leaf

        growth_per_leaf = (self.growth_rate*dt)/len(growable_leaves) if len(growable_leaves) > 0 else 0
        for leaf in growable_leaves:
            leaf["mass"] += growth_per_leaf
            leaf["age"] += 1*dt #seconds

        # age 0
        # max_age 1000

        # if reached a certain mass, gain one exp point, increase threshold
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self):
        return sum([leaf["mass"] for leaf in self.leaves])+self.base_mass # basemass for seedling leaves

    def append_leaf(self, highlight):
        pos = highlight[0]
        dir = pos[0] - pygame.mouse.get_pos()[0]
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
                "t": (highlight[1],highlight[2]),
                "shadow_score": 1,
                "image": image[0],
                "offset_x": offset[0],
                "offset_y": offset[1],
                "mass": 0.0001,
                "base_image_id": image_id,
                "direction": dir,
                "age": 0,
                "lifetime": 60*60*24*10, # 10 days of liefetime to grow
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
            if self.photon_intake > 0 and self.plant.model.stomata_open:
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
        new_width = (threshold * factor) + base
        new_height = int(new_width * ratio)
        new_width = int(new_width)
        leaf["offset_x"] = base_offset[0] * (new_width / base_image.get_width())
        leaf["offset_y"] = base_offset[1] * (new_height / base_image.get_height())
        leaf["image"] = pygame.transform.scale(base_image, (new_width, new_height))

    def draw(self, screen):
        if self.can_add_leaf:
            x,y = pygame.mouse.get_pos()
            screen.blit(assets.img("leaf_small.PNG",(128,128)), (x,y-self.plant.camera.offset_y))

        for leaf in self.leaves:
            #image = self.yellow_leaf(leaf["image"], 128)
            screen.blit(leaf["image"], (leaf["x"]-leaf["offset_x"], leaf["y"]-leaf["offset_y"]))


        if self.type == self.plant.target_organ.type:
            rects = self.get_rect()
            outlines = self.get_outlines()
            for i in range(0,len(self.leaves)):
                s = pygame.Surface((64, 64),pygame.SRCALPHA)
                pygame.draw.lines(s, (255,255,255),True,outlines[i],2)
                #pygame.draw.rect(screen, (255, 255, 255), (rects[i][0],rects[i][1],rects[i][2],rects[i][3]), 2)
                screen.blit(s, (self.leaves[i]["x"]-self.leaves[i]["offset_x"], self.leaves[i]["y"]-self.leaves[i]["offset_y"]))

                '''#leave_details:
                mass_label = config.FONT.render("Mass: {0:.2f}".format(self.leaves[i]["mass"]),True,config.WHITE)
                age_label = config.FONT.render("Age: {0:.2f}".format(self.leaves[i]["age"]),True,config.WHITE)
                lifetime_label = config.FONT.render("Lifetime: {0:.2f}".format(self.leaves[i]["lifetime"]/(24*60*60)),True,config.WHITE)

                x = self.leaves[i]["x"]-self.leaves[i]["offset_x"]+self.leaves[i]["image"].get_width()
                y = self.leaves[i]["y"]-self.leaves[i]["offset_y"]
                pygame.draw.rect(screen,config.WHITE,(x,y,lifetime_label.get_width(),120),3,3)
                screen.blit(mass_label,(x,y))
                screen.blit(age_label,(x,y+30))
                screen.blit(lifetime_label,(x,y+60))'''


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
    def __init__(self, x, y, name, organ_type, callback, plant, image=None, pivot=None, mass=0.0, active=False):
        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active)
        #self.curves = [Beziere([(self.x, self.y), (self.x - 20, self.y + 50), (self.x + 70, self.y + 100)],color=config.WHITE, res=10, width=mass+5)]
        self.selected = 0
        #positions = [(x,y+45)]
        #directions = [(0,1)]
        root_grid = np.zeros(self.plant.water_grid.get_shape())
        water_grid_pos = self.plant.water_grid.pos

        self.ls = LSystem(root_grid, water_grid_pos)
        self.create_new_root(dir=(0, 1))

        self.tabroot = False # if not tabroot, its fibroot -> why skill it then?

    def grow_roots(self):
        pass

    def update_image_size(self, factor=5, base=25):
        super().update_image_size(factor, base)

    def get_outline(self):
        outlines = pygame.mask.from_surface(self.image).outline()
        return outlines

    def check_can_add_root(self):
        if self.active_threshold > len(self.ls.first_letters):
            return True
        else:
            return False

    def update(self, dt):
        self.ls.update(self.mass)
        #self.plant.model.apexes = self.ls.apexes
        #for curve in self.curves:
        #    curve.update(dt)

    def create_new_root(self, mouse_pos=None, dir=None):
        dist=None
        if mouse_pos:
            dist = math.sqrt(((mouse_pos[0]-self.x)**2+(mouse_pos[1]-self.y)**2))
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
    def __init__(self, x, y, name, organ_type, callback, plant, image=None, pivot=None, leaf=None, flower=None, mass=0.0, active=False):
        self.leaf = leaf
        self.flower = flower
        self.width = 15
        self.highlight = None
        self.sunpos = (0,0)
        self.curve = Cubic_Tree([Cubic([[955,900],[960,820],[940,750]])])
        self.gametime = GameTime.instance()
        self.timer = 0
        self.floating_shop = None
        self.dist_to_stem = 1000
        self.can_add_branch = False
        #self.add_branch(Cubic([[700,750],[880,710],[900,610]]))

        super().__init__(x, y, name, organ_type, callback, plant, image, pivot, mass=mass, active=active, base_mass=1)
        #self.curve = Beziere([(self.x-5, self.y+40), (self.x-5, self.y), (self.x - 15, self.y - 50), (self.x+13, self.y - 150), (self.x+3, self.y - 190)],res=20)
        #self.new_curve = Beziere([(self.x - 15, self.y - 50), (self.x+30, self.y - 150), (self.x+30, self.y - 190)],width=5, res=15)

    def update(self, dt):
        self.curve.update(dt)
        self.update_leaf_positions()
        self.update_flower_positions()

    def update_leaf_positions(self):
        for leaf in self.leaf.leaves:
            branch_id, point_id = leaf["t"]
            pos = self.curve.branches[branch_id].points[point_id]
            leaf["x"] = pos[0]
            leaf["y"] = pos[1]

    def update_flower_positions(self):
        for flower in self.flower.flowers:
            branch_id, point_id = flower["t"]
            pos = self.curve.branches[branch_id].points[point_id]
            flower["x"] = pos[0]
            flower["y"] = pos[1]

    def activate_add_branch(self):
        self.can_add_branch = True

    def reach_threshold(self):
        super().reach_threshold()
        self.curve.grow_all()

    def check_can_add_leaf(self):
        return True

    def handle_event(self, event):
        self.curve.handle_event(event)
        #self.new_curve.handle_event(event)
        if event.type == pygame.MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            y -= self.plant.camera.offset_y
            point, branch_id, point_id = self.curve.find_closest((x, y), True)
            if self.leaf.can_add_leaf:
                self.highlight = (point, branch_id, point_id)
            elif self.can_add_branch:
                self.highlight = (point, branch_id, point_id)
            elif self.flower.can_add_flower:
                self.highlight = (point, branch_id, point_id)
            else:
                self.highlight = None

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            rects = self.get_rect()
            if rects is not None:
                for rect in self.get_rect():
                    if rect.collidepoint((x,y)):
                        self.callback()
            if not self.can_add_branch or self.leaf.can_add_leaf:

                y -= self.plant.camera.offset_y
                point, branch_id, point_id = self.curve.find_closest((x, y), True)
                dist_to_stem = math.sqrt((x - point[0])**2 + (y - point[1])**2)
                if dist_to_stem < 20:
                    self.timer = self.gametime.get_time()

        if event.type == pygame.MOUSEBUTTONUP:
            if self.can_add_branch and self.dist_to_stem < 50:
                if self.highlight:
                    self.add_branch(pygame.mouse.get_pos(), self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[self.highlight[2]] = False
                    self.can_add_branch = False
            elif self.leaf.can_add_leaf and self.dist_to_stem < 50:
                if self.highlight:
                    self.leaf.append_leaf(self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[self.highlight[2]] = False
            elif self.flower.can_add_flower and self.dist_to_stem < 50:
                if self.highlight:
                    self.flower.append_flower(self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[self.highlight[2]] = False
            else:
                if self.gametime.get_time() - self.timer < 1000*120:
                    if self.floating_shop is not None:
                        self.floating_shop.activate(pygame.mouse.get_pos())

        if event.type == KEYDOWN and event.key == K_SPACE:
            self.curve.grow_all()
        if event.type == KEYDOWN and event.key == K_b:
            self.can_add_branch = True
        if event.type == KEYDOWN and event.key == K_m:
            self.curve.toggle_move()

    def update_image_size(self, factor=3, base=5):
        # there is no image, just beziere
        pass
        #super().update_image_size(factor, base)
        #if self.leaf:
            #for leaf in self.leaf.leaves:
                #self.reassign_leaf_x(leaf)

    def add_branch(self, highlight, mouse_pos):
        self.curve.add_branch(mouse_pos, highlight)

    '''def update_sunflower_position(self):
        if self.flower:
            pos = self.curve.get_point(1)
            self.sunflower_pos = (pos[0]-32,pos[1]-32)'''

    def get_local_pos(self, pos):
        return (int(pos[0]-(self.x-self.pivot[0])),int(pos[1]-(self.y-self.pivot[1])))

    def get_global_x(self, x):
        return int(x+self.x)

    def draw(self, screen):
        if self.plant.target_organ.type == self.type:
            #self.new_curve.draw_highlights(screen)
            #for branch in self.branches:
            #    branch.draw_highlights(screen)
            self.curve.draw(screen, True)
        else:
            self.curve.draw(screen)

        #self.new_curve.draw(screen)
        #for branch in self.branches:
        #    branch.draw(screen)

        if self.highlight:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mouse_y = mouse_y-self.plant.camera.offset_y
            self.dist_to_stem = math.sqrt((mouse_x - self.highlight[0][0])**2 + (mouse_y - self.highlight[0][1])**2)
            color = config.GRAY if self.dist_to_stem  > 50 else config.WHITE
            pygame.draw.line(screen, color, (self.highlight[0][0],self.highlight[0][1]),(mouse_x,mouse_y))
            pygame.draw.circle(screen, color, (int(self.highlight[0][0]), int(self.highlight[0][1])), 10)

        pygame.draw.circle(screen, config.GREEN, (self.x-5, self.y+40),10)

    def get_rect(self):
        return self.curve.get_rects()

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
                if (image.get_at((i, pos[1]))[3] != 0):
                    x = i
                    break
        elif pos[0] > middle: #and pos[0] < rect[2]:
            # right
            dir = 1
            for i in range(rect[2]-1, rect[0], -1):
                if (image.get_at((i, pos[1]))[3] != 0):
                    x = i
                    break
        return x, dir

class Starch(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, image, mass, active, model):
        super().__init__(x, y, name, organ_type, callback, plant, image, mass=mass, active=active, thresholds=[500])
        self.toggle_button = None
        self.model = model
        self.starch_intake = 0

    def grow(self,dt):
        delta = self.growth_rate*dt
        if delta >= self.thresholds[self.active_threshold]:
            self.mass = self.thresholds[self.active_threshold]
        else:
            self.mass += delta

    def update_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate

    def update_starch_max(self, max_pool):
        self.thresholds = [max_pool]
        if self.mass > max_pool:
            self.mass = max_pool

    def set_percentage(self, percentage):
        self.percentage = percentage
        if percentage < 0:
            self.model.activate_starch_resource(abs(percentage))
        else:
            self.model.deactivate_starch_resource()

    def drain(self, dt):
        delta = self.starch_intake*dt
        if self.mass - delta < 0:
            self.mass = 0
            # Todo deactivate start cons
        else:
            self.mass -= delta



class Flower(Organ):
    def __init__(self, x, y, name, organ_type, callback, plant, images, mass, active):
        self.flowers = []
        super().__init__(x, y, name, organ_type, plant=plant, mass=mass, active=active, thresholds=[1,2,3,10])
        self.callback = callback
        self.images = images
        self.base_mass = 1
        self.target_flower = 0
        self.can_add_flower = False
        self.pollinated = False
        self.flowering = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.callback()
        if self.type == self.plant.target_organ.type:
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                rects = self.get_rect()
                for i in range(len(rects)):
                    if rects[i].collidepoint(mouse_pos):
                        self.target_flower = i

    def activate_add_flower(self):
        if self.flowering:
            self.can_add_flower = True
        self.can_add_flower = True

    def start_flowering(self):
        if self.pollinated:
            self.flowering = True

    def pollinate(self):
        self.pollinated = True

    def get_random_flower(self):
        if len(leaves) > 0:
            return self.flowers[random.randint(0,len(self.flowers)-1)]
        else:
            return None

    def update_growth_rate(self, growth_rate):
        # Todo change gram_mol = flower mol
        self.growth_rate = gram_mol * growth_rate

    def grow(self, dt):
        if self.growth_rate <= 0 or not self.flowering:
            return
        # get leaf age, if too old -> stop growth, then die later
        growable_flowers = []
        for flower in self.flowers:
            id = int(flower["mass"]/flower["maximum_mass"]*(len(self.images)-1))
            flower["image"] = self.images[id]
            if flower["mass"] < flower["maximum_mass"]:
                growable_flowers.append(flower)
            # if max age*2 -> kill leaf

        growth_per_flower = (self.growth_rate*dt)/len(growable_flowers) if len(growable_flowers) > 0 else 0
        for flower in growable_flowers:
            flower["mass"] += growth_per_flower

        # age 0
        # max_age 1000

        # if reached a certain mass, gain one exp point, increase threshold
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self):
        return sum([leaf["mass"] for leaf in self.flowers])+self.base_mass  # basemass for seedling leaves

    def get_flowering_flowers(self):
        flowering_flowers = []
        if not self.flowering:
            return flowering_flowers
        for flower in self.flowers:
            if flower["mass"] < flower["maximum_mass"] and flower["flowering"]:
                flowering_flowers.append(flower)
        return flowering_flowers

    def append_flower(self, highlight):
        pos = highlight[0]
        image = self.images[0]
        offset = (image.get_width()/2, image.get_height()/2)
        flower = {"x": pos[0],
                "y": pos[1],
                "t": (highlight[1], highlight[2]),
                "offset_x": offset[0],
                "offset_y": offset[1],
                "image": image,
                "mass": 0.01,
                "flowering": True,
                "maximum_mass": self.thresholds[-1],
                "lifetime": 60*60*24*10, # 10 days of liefetime to grow
                "growth_index": self.active_threshold} # to get relative size, depending on current threshold - init threshold
        self.update_flower_image(flower, init=True)
        self.flowers.append(flower)
        self.can_add_flower = False

    def get_rect(self):
        return [flower["image"].get_rect(topleft=(flower["x"]-flower["offset_x"], flower["y"]-flower["offset_y"]+self.plant.camera.offset_y)) for flower in self.flowers]

    def update(self, dt):
        pass

    def update_image_size(self, factor=7, base=80):
        for flower in self.flowers:
            self.update_flower_image(flower, factor, base)

    def update_flower_image(self, flower, factor=7, base=80, init=False):
        pass

    def draw(self, screen):
        if self.can_add_flower:
            x,y = pygame.mouse.get_pos()
            screen.blit(assets.img("sunflowers/2.PNG",(128,128)), (x,y-self.plant.camera.offset_y))

        for flower in self.flowers:
            screen.blit(flower["image"], (flower["x"]-flower["offset_x"], flower["y"]-flower["offset_y"]))

        if self.type == self.plant.target_organ.type:
            rects = self.get_rect()
            outlines = self.get_outlines()
            for i in range(0,len(self.flowers)):
                s = pygame.Surface((64, 64),pygame.SRCALPHA)
                color = config.WHITE
                if self.flowers[i]["mass"] >= self.flowers[i]["maximum_mass"]:
                    color = config.GREEN
                pygame.draw.lines(s, color,True,outlines[i],3)
                #pygame.draw.rect(screen, (255, 255, 255), (rects[i][0],rects[i][1],rects[i][2],rects[i][3]), 2)
                screen.blit(s, (self.flowers[i]["x"]-flower["offset_x"], self.flowers[i]["y"]-flower["offset_y"]))

        # progress bar
        if self.flowering:
            for flower in self.flowers:
                if flower["mass"] < flower["maximum_mass"]:
                    width = flower["image"].get_width()
                    percentage = flower["mass"]/flower["maximum_mass"]
                    pygame.draw.rect(screen, config.WHITE, (flower["x"]-flower["offset_x"],flower["y"]-width/4-10-flower["offset_y"],width*percentage,width/4),border_radius=3)
                    pygame.draw.rect(screen, config.WHITE_TRANSPARENT, (flower["x"]-flower["offset_x"],flower["y"]-width/4-10-flower["offset_y"],width,width/4),2,3)
                    percentage_label = config.SMALL_FONT.render("{:.0f}".format(percentage*100),True,config.BLACK)
                    screen.blit(percentage_label, (flower["x"]-flower["offset_x"]+width/2-percentage_label.get_width()/2,flower["y"]-width/4-10-flower["offset_y"]))

    def get_outlines(self):
        outlines = []
        for flower in self.flowers:
            mask = pygame.mask.from_surface(flower["image"])
            outline = mask.outline()
            outlines.append(outline)
        return outlines
