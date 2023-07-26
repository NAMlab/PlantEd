import logging
import random
import string
from typing import Tuple, Optional

import pygame

import math
from pygame import Rect
from pygame.locals import *
import numpy as np

from PlantEd import config
from PlantEd.camera import Camera
from PlantEd.client.client import Client
from PlantEd.client.growth_rates import GrowthRates
from PlantEd.data import assets
from PlantEd.data.sound_control import SoundControl
from PlantEd.gameobjects.shop import FloatingShop
from PlantEd.utils.LSystem import DictToRoot, LSystem
from PlantEd.utils.animation import Animation
from PlantEd.utils.particle import ParticleSystem
from PlantEd.utils.spline import Cubic_Tree, Cubic

logger = logging.getLogger(__name__)

WIN = pygame.USEREVENT + 1
pivot_pos = [
    (286, 113),
    (76, 171),
    (254, 78),
    (19, 195),
    (271, 114),
    (47, 114),
]
leaves = [
    (assets.img("leaves/{index}.PNG".format(index=i)), pivot_pos[i])
    for i in range(0, 6)
]
flowers = [
    (assets.img("sunflowers/{index}.PNG".format(index=i), (64, 64)))
    for i in range(0, 3)
]

beans = [
    assets.img("bean_growth/{}.PNG".format(index), (150, 150))
    for index in range(0, 6)
]


def from_dict(plant_dict, camera=None):
    plant = Plant(
        pos = plant_dict["pos"],
        water_grid_shape=plant_dict["water_grid_shape"],
        water_grid_pos=plant_dict["water_grid_pos"],
        camera=camera
    )

    plant.organs[0].leaves = plant_dict["leaf"]["leaves"]
    print(plant_dict["leaf"]["leaves"])
    for leaf in plant.organs[0].leaves:
        leaf["image"] = leaves[int(random.random() * len(leaves))][0]
    plant.organs[0].update_image_size()
    branches: list[Cubic] = []
    branches_dict_list = plant_dict["stem"]["curve"]["branches"]
    for branch in branches_dict_list:
        print(branch["branch"])
        branches.append(Cubic(branch["branch"]))
    plant.organs[1].curve = Cubic_Tree(branches=branches)


    plant.organs[2].ls = DictToRoot().load_root_system(plant_dict["root"]["roots"])
    plant.organs[3].flowers = plant_dict["flower"]["flowers"]
    for flower in plant.organs[3].flowers:
        flower["image"] = flowers[int(random.random()*len(flowers))]
    return plant


class Plant:
    LEAF = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4
    FLOWER = 5

    def __init__(
            self,
            pos: tuple[float, float],
            water_grid_shape: tuple[int, int],
            water_grid_pos: tuple[float, float],
            sound_control: SoundControl = None,
            client: Client = None,
            upgrade_points: int = 1,
            camera: Camera = None
    ):
        self.x: float = pos[0]
        self.y: float = pos[1]
        self.water_grid_shape = water_grid_shape
        self.water_grid_pos = water_grid_pos
        self.client: Client = client
        self.upgrade_points: int = upgrade_points
        self.sound_control: SoundControl = sound_control
        play_level_up_sfx = None
        play_reward_sfx = None
        if self.sound_control is not None:
            play_level_up_sfx = self.sound_control.play_level_up_sfx
            play_reward_sfx = self.sound_control.play_reward_sfx
        self.use_starch: bool = True
        self.camera: Camera = camera
        self.danger_mode: bool = False
        organ_leaf = Leaf(
            x=self.x,
            y=self.y,
            name="Leaves",
            organ_type=self.LEAF,
            callback=self.set_target_organ_leaf,
            images=leaves,
            mass=0.1,
            active=False,
            play_level_up=play_level_up_sfx,
            play_reward=play_reward_sfx,
            camera=self.camera,
            level_up=self.level_up
        )
        organ_flower = Flower(
            x=self.x,
            y=self.y,
            name="Flower",
            organ_type=self.FLOWER,
            callback=self.set_target_organ_flower,
            images=flowers,
            mass=0.1,
            active=False,
            play_reward=play_reward_sfx,
            camera=self.camera,
        )
        organ_stem = Stem(
            x=self.x,
            y=self.y,
            name="Stem",
            organ_type=self.STEM,
            callback=self.set_target_organ_stem,
            mass=0.1,
            leaf=organ_leaf,
            flower=organ_flower,
            active=False,
            play_level_up=play_level_up_sfx,
            play_reward=play_reward_sfx,
            camera=self.camera,
            level_up=self.level_up
        )
        organ_root = Root(
            x=self.x,
            y=self.y,
            name="Roots",
            organ_type=self.ROOTS,
            callback=self.set_target_organ_root,
            mass=4,
            active=True,
            water_grid_shape=water_grid_shape,
            water_grid_pos=water_grid_pos,
            play_level_up=play_level_up_sfx,
            play_reward=play_reward_sfx,
            camera=self.camera,
            level_up=self.level_up
        )
        self.organ_starch = Starch(
            x=self.x,
            y=self.y,
            name="Starch",
            organ_type=self.STARCH,
            callback=self,
            image=None,
            mass=1000000,
            active=True,
            client=client,
            camera=self.camera
        )

        self.seedling = Seedling(self.x, self.y, beans, 4)
        self.organs = [organ_leaf, organ_stem, organ_root, organ_flower]
        # Fix env constraints
        config.write_dict(self.to_dict(), "plant")


    def to_dict(self) -> dict:

        plant_dict = {
            "pos": (self.x, self.y),
            "water_grid_shape": self.water_grid_shape,
            "water_grid_pos": self.water_grid_pos,
            "leaf": self.organs[0].to_dict(),
            "stem": self.organs[1].to_dict(),
            "root": self.organs[2].to_dict(),
            "flower": self.organs[3].to_dict()
        }
        return plant_dict

    def level_up(self):
        self.upgrade_points += 1

    def get_stomata_open(self) -> bool:
        return self.organs[0].stomata_open

    def check_organ_level(self):
        lvl = 0
        for organ in self.organs:
            lvl += organ.level

    # convert flux/mikromol to gramm
    def update_growth_rates(self, growth_rates: GrowthRates):
        sum_rates = (
                growth_rates.leaf_rate
                + growth_rates.stem_rate
                + growth_rates.root_rate
                + growth_rates.starch_rate
                + growth_rates.seed_rate
        )

        logger.debug(f"Sum of GrowthRates is {sum_rates}")
        logger.debug(f"Delta is as follows IN PLANT RATES ARE: {str(growth_rates)}")

        growth_boost = 200
        if self.get_biomass() > 4:
            growth_boost = 100
            if sum_rates <= 0:
                self.danger_mode = True
            else:
                self.danger_mode = False

        self.organs[0].update_growth_rate(growth_rates.leaf_rate * growth_boost)
        self.organs[1].update_growth_rate(growth_rates.stem_rate * growth_boost)
        self.organs[2].update_growth_rate(growth_rates.root_rate * growth_boost)

        self.organ_starch.update_growth_rate(
            growth_rates.starch_rate * growth_boost
        )
        self.organ_starch.starch_intake = growth_rates.starch_intake * growth_boost
        self.organs[3].update_growth_rate(growth_rates.seed_rate * growth_boost * 10)

    def get_biomass(self):
        biomass = 0
        for organ in self.organs:
            biomass += organ.mass
        return biomass

    def get_level(self):
        return sum([organ.level for organ in self.organs])

    # Projected Leaf Area (PLA)
    def get_PLA(self):
        # 0.03152043208186226 as a factor to get are from dry mass
        return self.organs[0].get_pla()  # m^2

    # Todo dirty to reduce mass like this
    def eat_stem(self, rate, dt):
        self.organs[1].mass -= rate * dt

    def grow(self, dt):
        for organ in self.organs:
            organ.grow(dt)
        self.organ_starch.grow(dt)
        self.organ_starch.drain(dt, 0, 0)

    def set_target_organ_leaf(self):
        for organ in self.organs:
            organ.target = False
        self.organs[0].target = True

    def set_target_organ_stem(self):
        for organ in self.organs:
            organ.target = False
        self.organs[1].target = True

    def set_target_organ_root(self):
        for organ in self.organs:
            organ.target = False
        self.organs[2].target = True

    def set_target_organ_flower(self):
        for organ in self.organs:
            organ.target = False
        self.organs[3].target = True

    def update(self, dt, photon_intake):
        self.check_organ_level()
        self.grow(dt)
        if self.danger_mode:
            for organ in self.organs:
                # Todo make it more scientifically accurate
                organ.drain(0.00001, dt)
        if self.get_biomass() > self.seedling.max and not self.organs[1].active:
            self.organs[1].activate()
            self.organs[0].activate()
            # if self.get_biomass() > self.seedling.max and not self.organs[0].active:
        for organ in self.organs:
            organ.update(dt)
        self.organs[0].photon_intake = photon_intake

    def handle_event(self, event: pygame.event.Event):
        for organ in self.organs:
            organ.handle_event(event)

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
        self.x: float = x - 100
        self.y: float = y - 20
        self.images: list[pygame.Surface] = images
        self.max: float = max

    def draw(self, screen, mass):
        index = int(len(self.images) / self.max * (mass)) - 1
        if index >= len(self.images):
            index = len(self.images) - 1
        screen.blit(self.images[index], (self.x, self.y))


class Organ:
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            client: Client = None,
            image: pygame.Surface = None,
            pivot: tuple[float, float] = None,
            mass: float = 1,
            growth_rate: float = 0,
            thresholds: list[int] = None,
            active: bool = False,
            base_mass: float = 0.9,
            play_level_up: callable = None,
            play_reward: callable = None,
            target: bool = False,
            camera: Camera = None,
            level_up: callable = None
    ):
        if thresholds is None:
            thresholds = [1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40]
        self.x = x
        self.y = y
        self.client = client
        self.callback = callback
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
        self.play_level_up = play_level_up
        self.play_reward = play_reward
        self.target = target
        self.camera = camera
        self.level_up = level_up
        level_up_animation_images: list[pygame.Surface] = Animation.generate_rising_animation(
            "{} Level Up!".format(self.name), config.WHITE)
        self.animation: Animation = Animation(level_up_animation_images, 0.3, running=False, once=True)

    def update(self, dt):
        self.animation.update(dt)

    def set_percentage(self, percentage):
        self.percentage = percentage

    def update_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate * 2

    def get_rect(self) -> list[pygame.Rect]:
        if self.image:
            x = self.x - self.pivot[0] if self.pivot else self.x
            y = self.y - self.pivot[1] if self.pivot else self.y
            rect = pygame.Rect(
                x,
                y + self.camera.offset_y,
                self.image.get_width(),
                self.image.get_height(),
            )
        else:
            rect = pygame.Rect(0, 0, 0, 0)
        return [rect]

    def drain(self, rate, dt):
        if self.mass > 1:
            self.mass -= (rate + rate * 0.01 * self.mass) * dt

    def grow(self, dt):
        if not self.active:
            return
        self.mass += self.growth_rate * dt
        # if reached a certain mass, gain one exp point, increase threshold
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    """
    Organ has reached enough mass to level up
    Player gets rewarded with a green thumb + sound and animation
    """

    def reach_threshold(self):
        if self.active_threshold >= len(self.thresholds) - 1:
            return
        self.level_up()
        self.level += 1
        self.update_image_size()
        self.play_level_up()
        self.animation.start((config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT / 2))
        self.active_threshold += 1

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    self.callback()

    def get_threshold(self):
        return self.thresholds[self.active_threshold]

    """
    Not all organs are active at the start of the game
    Once activated, their base mass gets applied to fasten growth
    """

    def activate(self):
        if self.mass < self.base_mass:
            self.mass = self.base_mass
        self.active = True

    """
    Basic draw of an image
    More complex organs need to override this
    """

    def draw(self, screen):
        self.animation.draw(screen)
        if not self.pivot:
            self.pivot = (0, 0)
        if self.image and self.active:
            screen.blit(
                self.image, (self.x - self.pivot[0], self.y - self.pivot[1])
            )

    """
    Basic increase of organ image
    More complex structures need to override
    """

    def update_image_size(self, factor=5, base=40):
        if self.image:
            ratio = self.image.get_height() / self.image.get_width()
            width = (self.active_threshold + factor) * base
            height = int(width * ratio)
            width = int(width)
            self.pivot = (
                self.pivot[0] * (width / self.image.get_width()),
                self.pivot[1] * (height / self.image.get_height()),
            )
            self.image = pygame.transform.scale(
                self.base_image, (width, height)
            )


class Leaf(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            images: list[pygame.Surface],
            mass: float,
            active: bool,
            play_level_up: callable = None,
            play_reward: callable = None,
            camera: Camera = None,
            level_up: callable = None
    ):
        self.leaves = []
        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            mass=mass,
            active=active,
            play_level_up=play_level_up,
            play_reward=play_reward,
            camera=camera,
            level_up=level_up
        )
        self.callback = callback
        self.images = images
        self.photon_intake: float = 0
        self.base_mass: float = 0.9
        self.target_leaf: int = 0
        self.can_add_leaf: bool = False
        self.particle_system: ParticleSystem = ParticleSystem(
            20,
            spawn_box=Rect(500, 500, 50, 20),
            lifetime=8,
            color=config.YELLOW,
            apply_gravity=False,
            speed=[0, -1],
            spread=[1, -1],
            active=False,
        )
        self.particle_systems: list[ParticleSystem] = []
        self.shadow_map: np.ndarray = None
        self.shadow_resolution: int = 0
        self.max_shadow: int = 0
        self.play_reward: callable = play_reward
        self.stomata_open = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.callback()
        if self.target:
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

    def to_dict(self) -> dict:
        # factor 7, base 80
        cleared_leaves = self.leaves.copy()
        for leaf in cleared_leaves:
            leaf.pop("image")
        leaf_dict = {
            "leaves": cleared_leaves
        }
        return leaf_dict

    def get_pla(self):
        return (
            (self.mass + self.base_mass)
            * 0.03152043208186226
            * self.get_shadowscore()
            if len(self.leaves) > 0
            else 0
        )

    def get_shadowscore(self):
        # shadow scores are 0 for no shadow to 1 for full shadow. 1 - to get a factor
        return (
            sum([1 - leaf["shadow_score"] for leaf in self.leaves])
            / len(self.leaves)
            if len(self.leaves) > 0
            else 0
        )

    def grow(self, dt):
        if self.growth_rate <= 0:
            return
        # get leaf age, if too old -> stop growth, then die later
        growable_leaves = []
        for leaf in self.leaves:
            if leaf["lifetime"] > leaf["age"]:
                growable_leaves.append(leaf)
            # if max age*2 -> kill leaf

        growth_per_leaf = (
            (self.growth_rate * dt) / len(growable_leaves)
            if len(growable_leaves) > 0
            else 0
        )
        for leaf in growable_leaves:
            leaf["mass"] += growth_per_leaf
            leaf["age"] += 1 * dt  # seconds

        # if reached a certain mass, gain one exp point, increase threshold
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self):
        return (
                sum([leaf["mass"] for leaf in self.leaves]) + self.base_mass
        )

    def append_leaf(self, highlight: Tuple[list[int], int, int]):
        self.play_reward()
        pos = highlight[0]
        dir = pos[0] - pygame.mouse.get_pos()[0]
        if dir > 0:
            image_id = random.randrange(0, len(leaves) - 1, 2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]
        else:
            image_id = random.randrange(1, len(leaves), 2)
            image = leaves[image_id]
            offset = pivot_pos[image_id]

        leaf = {
            "x": pos[0],
            "y": pos[1],
            "t": (highlight[1], highlight[2]),
            "shadow_score": 0,
            "image": image[0],
            "offset_x": offset[0],
            "offset_y": offset[1],
            "mass": 0.0001,
            "base_image_id": image_id,
            "direction": dir,
            "age": 0,
            "lifetime": 60 * 60 * 24 * 10,  # 10 days of liefetime to grow
            "growth_index": self.active_threshold,
        }

        self.update_leaf_image(leaf, init=True)
        self.particle_systems.append(
            ParticleSystem(
                20,
                spawn_box=Rect(leaf["x"], leaf["y"], 0, 0),
                lifetime=6,
                color=config.YELLOW,
                apply_gravity=False,
                speed=[0, -5],
                spread=[5, 5],
                active=False,
            )
        )
        self.leaves.append(leaf)
        self.can_add_leaf = False

    def get_rect(self):
        return [
            leaf["image"].get_rect(
                topleft=(
                    leaf["x"] - leaf["offset_x"],
                    leaf["y"] - leaf["offset_y"] + self.camera.offset_y,
                )
            )
            for leaf in self.leaves
        ]

    # depending on the mean height of all leaves, 0 .. 1000, -> TODO: mass to PLA better
    def get_mean_leaf_height(self):
        return (
            sum(self.y - leaf["y"] for leaf in self.leaves) / len(self.leaves)
            if len(self.leaves) > 0
            else 0
        )

    def update(self, dt):
        self.animation.update(dt)
        # apply shadow penalty to leaves
        if self.shadow_map is not None:
            for leaf in self.leaves:
                x = int(
                    (leaf["x"] - leaf["offset_x"]) / self.shadow_resolution
                )
                y = int(
                    (leaf["y"] - leaf["offset_y"]) / self.shadow_resolution
                )

                width = int(leaf["image"].get_width() / self.shadow_resolution)
                height = int(
                    leaf["image"].get_height() / self.shadow_resolution
                )
                dots = width * height * self.max_shadow
                shadow_dots = 0
                for i in range(x, x + width):
                    for j in range(y, y + height):
                        shadow_dots += self.shadow_map[i, j]
                leaf["shadow_score"] = shadow_dots / dots
        else:
            for leaf in self.leaves:
                leaf["shadow_score"] = 0

        for system in self.particle_systems:
            system.update(dt)
        for i in range(0, len(self.leaves)):
            box = self.particle_systems[i].spawn_box
            size = self.leaves[i]["image"].get_size()
            offset_x = self.leaves[i]["offset_x"]
            offset_y = self.leaves[i]["offset_y"]
            self.particle_systems[i].spawn_box = (
                int(self.leaves[i]["x"] - offset_x + size[0] / 2),
                int(self.leaves[i]["y"] - offset_y + size[1] / 2),
                0,
                0,
            )
            if self.photon_intake > 0 and self.stomata_open:
                adapted_pi = self.photon_intake / 50 * 3 + 5
                self.particle_systems[i].lifetime = adapted_pi
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
        threshold = (
                self.active_threshold - leaf["growth_index"]
        )  # if not init else 0
        new_width = (threshold * factor) + base
        new_height = int(new_width * ratio)
        new_width = int(new_width)
        leaf["offset_x"] = base_offset[0] * (
                new_width / base_image.get_width()
        )
        leaf["offset_y"] = base_offset[1] * (
                new_height / base_image.get_height()
        )
        leaf["image"] = pygame.transform.scale(
            base_image, (new_width, new_height)
        )

    def draw(self, screen):
        self.animation.draw(screen)
        if self.can_add_leaf:
            x, y = pygame.mouse.get_pos()
            screen.blit(
                assets.img("leaf_small.PNG", (128, 128)),
                (x, y - self.camera.offset_y),
            )

        for leaf in self.leaves:
            # image = self.yellow_leaf(leaf["image"], 128)
            screen.blit(
                leaf["image"],
                (leaf["x"] - leaf["offset_x"], leaf["y"] - leaf["offset_y"]),
            )

        if self.target:
            outlines = self.get_outlines()
            for i in range(0, len(self.leaves)):
                s = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.lines(s, (255, 255, 255), True, outlines[i], 2)
                screen.blit(
                    s,
                    (
                        self.leaves[i]["x"] - self.leaves[i]["offset_x"],
                        self.leaves[i]["y"] - self.leaves[i]["offset_y"],
                    ),
                )
        for system in self.particle_systems:
            system.draw(screen)

    def get_outlines(self):
        outlines = []
        for leaf in self.leaves:
            mask = pygame.mask.from_surface(leaf["image"])
            outline = mask.outline()
            outlines.append(outline)
        return outlines


class Root(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            image: pygame.Surface = None,
            pivot: tuple[float, float] = None,
            mass: float = 0.0,
            active: bool = False,
            water_grid_shape: tuple[int, int] = None,
            water_grid_pos: tuple[float, float] = None,
            play_level_up: callable = None,
            play_reward: callable = None,
            camera: Camera = None,
            level_up: callable = None
    ):
        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            image=image,
            pivot=pivot,
            mass=mass,
            active=active,
            play_level_up=play_level_up,
            play_reward=play_reward,
            camera=camera,
            level_up=level_up
        )
        # self.curves = [Beziere([(self.x, self.y), (self.x - 20, self.y + 50), (self.x + 70, self.y + 100)],color=config.WHITE, res=10, width=mass+5)]
        self.selected = 0
        root_grid: np.array = np.zeros(water_grid_shape)
        water_grid_pos: tuple[float, float] = water_grid_pos

        self.ls: LSystem = LSystem(root_grid, water_grid_pos)
        self.create_new_root(dir=(0, 1))
        self.play_reward = play_reward

    # Todo make root outlines
    def get_outline(self):
        pass

    def to_dict(self) -> dict:
        root_dict = {
            "roots": self.ls.to_dict()
        }
        return root_dict

    def check_can_add_root(self):
        if self.active_threshold > len(self.ls.first_letters):
            return True
        else:
            return False

    def update(self, dt):
        self.ls.update(self.mass)
        self.animation.update(dt)

    def create_new_root(self, mouse_pos=None, dir=None):
        if self.play_reward is not None:
            self.play_reward()
        dist = None
        if mouse_pos:
            dist = math.sqrt(
                ((mouse_pos[0] - self.x) ** 2 + (mouse_pos[1] - self.y) ** 2)
            )
        pos = (self.x - 5, self.y + 40)
        if not dir and mouse_pos:
            dir = (mouse_pos[0] - self.x, mouse_pos[1] - (self.y + 45))
        self.ls.create_new_first_letter(dir, pos, self.mass, dist=dist)

    def get_root_grid(self):
        return self.ls.root_grid

    def handle_event(self, event):
        pass

    def draw(self, screen):
        self.animation.draw(screen)
        if self.target:
            # pygame.draw.line(screen, config.WHITE, (self.x + 1, self.y + 30), (self.x, self.y + 45), 8)
            self.ls.draw_highlighted(screen)
        else:
            self.ls.draw(screen)


class Stem(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            image: pygame.Surface = None,
            leaf: Leaf = None,
            flower=None,
            mass: float = 0.0,
            active: bool = False,
            play_level_up: callable = None,
            play_reward: callable = None,
            camera: Camera = None,
            level_up: callable = None
    ):
        self.leaf = leaf
        self.flower = flower
        self.width: float = 15
        self.highlight: Optional[Tuple[list[int], int, int]] = None
        self.curve = Cubic_Tree(
            [Cubic([[955, 900], [960, 820], [940, 750]])], camera
        )
        self.timer: float = 0
        self.floating_shop: FloatingShop = None
        self.dist_to_stem: float = 1000
        self.can_add_branch: bool = False
        self.play_reward: callable = play_reward
        self.play_level_up: callable = play_level_up

        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            image=image,
            mass=mass,
            active=active,
            base_mass=1,
            play_level_up=play_level_up,
            play_reward=play_reward,
            camera=camera,
            level_up=level_up
        )

    def update(self, dt):
        self.animation.update(dt)
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

    # Todo find out why always true is return
    def check_can_add_leaf(self):
        return True

    def to_dict(self) -> dict:
        stem_dict = {
            "curve": self.curve.to_dict()
        }
        return stem_dict

    def handle_event(self, event):
        self.curve.handle_event(event)
        if event.type == pygame.MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            y -= self.camera.offset_y
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
                    if rect.collidepoint((x, y)):
                        self.callback()
            if not self.can_add_branch or self.leaf.can_add_leaf:
                y -= self.camera.offset_y
                point, branch_id, point_id = self.curve.find_closest(
                    (x, y), False
                )
                dist_to_stem = math.sqrt(
                    (x - point[0]) ** 2 + (y - point[1]) ** 2
                )
                if dist_to_stem < 20:
                    self.timer = pygame.time.get_ticks()

        if event.type == pygame.MOUSEBUTTONUP:
            if self.can_add_branch and self.dist_to_stem < 50:
                if self.highlight:
                    self.add_branch(pygame.mouse.get_pos(), self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[
                        self.highlight[2]
                    ] = config.BRANCH_SPOT
                    self.can_add_branch = False
            elif self.leaf.can_add_leaf and self.dist_to_stem < 50:
                if self.highlight:
                    self.leaf.append_leaf(self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[
                        self.highlight[2]
                    ] = config.LEAF_SPOT
            elif self.flower.can_add_flower and self.dist_to_stem < 50:
                if self.highlight:
                    self.flower.append_flower(self.highlight)
                    self.curve.branches[self.highlight[1]].free_spots[
                        self.highlight[2]
                    ] = config.FLOWER_SPOT
            else:
                print(self.timer, pygame.time.get_ticks(), pygame.time.get_ticks()-self.timer)
                if pygame.time.get_ticks() - self.timer < 300:
                    x, y = pygame.mouse.get_pos()
                    y -= self.camera.offset_y
                    # check how many free spots the stem hast, adapt shop accordingly
                    # no spots -> if flower selected -> flower option
                    # no spots, no flower -> nothing
                    # 1 spot, flower -> all
                    # 1 spot, no flower -> all but flower option

                    show_items = False
                    show_flower = False
                    point, branch_id, point_id = self.curve.find_closest((x, y), False)
                    if self.curve.branches[branch_id].free_spots[point_id] == config.FLOWER_SPOT:
                        if len(self.flower.flowers) > 0:
                            for flower in self.flower.flowers:
                                if branch_id == (flower["t"][0]
                                                 and point_id == flower["t"][1]
                                                 and flower["pollinated"]
                                                 and not flower["flowering"]):
                                    show_flower = True

                    else:
                        free_spots = self.curve.get_free_spots()
                        if free_spots > 0:
                            show_items = True
                    if self.floating_shop is not None and (show_flower or show_items):
                        self.floating_shop.activate(pygame.mouse.get_pos(), show_items, show_flower)

        if event.type == KEYDOWN and event.key == K_SPACE:
            self.curve.grow_all()
        if event.type == KEYDOWN and event.key == K_b:
            self.can_add_branch = True
        if event.type == KEYDOWN and event.key == K_m:
            self.curve.toggle_move()

    def update_image_size(self, factor=3, base=5):
        pass

    def add_branch(self, highlight, mouse_pos):
        self.play_reward()
        self.curve.add_branch(mouse_pos, highlight)

    def draw(self, screen):
        self.animation.draw(screen)
        if self.target:
            self.curve.draw(screen, True)
        else:
            self.curve.draw(screen)
        if self.highlight:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            mouse_y = mouse_y - self.camera.offset_y
            self.dist_to_stem = math.sqrt(
                (mouse_x - self.highlight[0][0]) ** 2
                + (mouse_y - self.highlight[0][1]) ** 2
            )
            color = config.GRAY if self.dist_to_stem > 50 else config.WHITE
            pygame.draw.line(
                screen,
                color,
                (self.highlight[0][0], self.highlight[0][1]),
                (mouse_x, mouse_y),
            )
            pygame.draw.circle(
                screen,
                color,
                (int(self.highlight[0][0]), int(self.highlight[0][1])),
                10,
            )
        pygame.draw.circle(screen, config.GREEN, (self.x - 5, self.y + 40), 10)

    def get_rect(self):
        return self.curve.get_rects()


class Starch(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            image: pygame.Surface,
            mass: float,
            active: bool,
            client: Client,
            camera: Camera = None
    ):
        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            image=image,
            mass=mass,
            active=active,
            thresholds=[500],
            client=client,
            camera=camera
        )
        self.toggle_button = None
        self.starch_intake = 0

    def grow(self, dt):
        return

    def update_growth_rate(self, growth_rate):
        self.growth_rate = growth_rate * 2
        logger.debug(f" Starch usage in UI set to {self.growth_rate}")

    def update_starch_max(self, max_pool):
        self.thresholds = [max_pool]
        logger.debug(f" Starch max in UI set to {self.thresholds}")
        if self.mass > max_pool:
            self.mass = max_pool

    def set_percentage(self, percentage):
        self.percentage = percentage
        logger.debug(f" Starch percentage in UI set to {self.percentage}")
        if percentage < 0:
            self.client.activate_starch_resource(abs(percentage))
        else:
            self.client.deactivate_starch_resource()

    def drain(self, rate, dt, gamespeed):
        return


class Flower(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            images: pygame.Surface,
            mass: float,
            active: bool,
            play_reward,
            camera: Camera = None
    ):
        self.flowers = []
        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            mass=mass,
            active=active,
            thresholds=[1, 2, 3, 10],
            play_reward=play_reward,
            camera=camera
        )
        self.callback = callback
        self.images = images
        self.base_mass: float = 0.1
        self.target_flower: int = 0
        self.can_add_flower: bool = False
        self.flowering: bool = False
        self.seed_popped: bool = False
        self.pop_seed_particles: list[ParticleSystem] = []
        self.pop_all_seeds_timer: float = 0
        self.interval: float = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            pass
            # self.pop_seed()
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(pygame.mouse.get_pos()):
                    self.callback()
        if self.target:
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = pygame.mouse.get_pos()
                rects = self.get_rect()
                for i in range(len(rects)):
                    if rects[i].collidepoint(mouse_pos):
                        self.target_flower = i

    def activate_add_flower(self):
        self.can_add_flower = True

    def to_dict(self) -> dict:
        cleared_flowers = self.flowers.copy()
        for flower in cleared_flowers:
            flower.pop("image")
        flower_dict = {
            "flowers": cleared_flowers
        }
        return flower_dict

    def flower_flower(self, flower):
        flower["flowering"] = True

    def get_closest_flower(self, pos, flowering=False):
        min_dist = 10000
        closest_flower = None
        for flower in self.flowers:
            dist = math.sqrt(
                (pos[0] - flower["x"]) * (pos[0] - flower["x"]) + (pos[1] - flower["y"]) * (pos[1] - flower["y"]))
            if dist < min_dist and flower["flowering"] == flowering:
                closest_flower = flower
                min_dist = dist
        return closest_flower

    def start_flowering_closest(self, pos):
        flower = self.get_closest_flower(pos)
        if flower:
            self.flower_flower(flower)

    def start_flowering(self):
        self.flowering = True

    def pollinate(self, i):
        self.flowers[i]["pollinated"] = True

    def grow(self, dt):
        if self.growth_rate <= 0:
            return
        # get leaf age, if too old -> stop growth, then die later
        growable_flowers = []
        for flower in self.flowers:
            id = min(
                int(
                    flower["mass"]
                    / flower["maximum_mass"]
                    * (len(self.images) - 1)
                ),
                len(self.images) - 1,
            )
            flower["image"] = self.images[id]
            if flower["mass"] < flower["maximum_mass"]:
                growable_flowers.append(flower)
            # if max age*2 -> kill leaf

        for flower in self.flowers:
            if (
                    flower["flowering"]
                    and flower["seed_mass"] < flower["maximum_seed_mass"]
            ):
                growable_flowers.append(flower)

        growth_per_flower = (
            (self.growth_rate * dt) / len(growable_flowers)
            if len(growable_flowers) > 0
            else 0
        )
        for flower in growable_flowers:
            if flower["mass"] >= flower["maximum_mass"]:
                flower["seed_mass"] += growth_per_flower
            else:
                flower["mass"] += growth_per_flower
        self.mass = self.get_mass()
        if self.mass > self.thresholds[self.active_threshold]:
            self.reach_threshold()

    def get_mass(self) -> float:
        return (
                sum([leaf["mass"] for leaf in self.flowers]) + self.base_mass
        )  # basemass for seedling leaves

    def get_random_flower_pos(self):
        viable_flowers = []
        for flower in self.flowers:
            if (
                    not flower["pollinated"]
                    and flower["mass"] >= flower["maximum_mass"]
            ):
                viable_flowers.append(flower)
        if len(viable_flowers) > 0:
            i = int(random.random() * len(viable_flowers))
            pos = (
                viable_flowers[i]["x"] + viable_flowers[i]["offset_x"] / 2,
                viable_flowers[i]["y"]
                + viable_flowers[i]["offset_y"] / 2
                - 20,
            )
            target_flower_id = self.flowers.index(viable_flowers[i])
            return pos, target_flower_id
        else:
            return None, None

    def get_growing_flowers(self) -> list[dict]:
        growing_flowers = []
        # flowering can be central activated to enable all pollinated flowers to produce seeds
        # add all growing flowers
        for flower in self.flowers:
            if (
                    flower["mass"] < flower["maximum_mass"]
                    or (flower["flowering"]
                        and flower["seed_mass"] < flower["maximum_seed_mass"]
            )
            ):
                growing_flowers.append(flower)
        # add all seed producing flowrs
        return growing_flowers

    """
    Pop all seeds one after another
    given a timeframe, calculate the intervals to pop each seed
    
    Args:
        timeframe
    """

    def pop_all_seeds(self, timeframe):
        self.pop_all_seeds_timer = timeframe
        self.interval = timeframe / len(self.flowers)

    def pop_seed(self, flower):
        self.seed_popped = True
        self.pop_seed_particles.append(
            ParticleSystem(
                max_particles=(30 + int(flower["mass"]) * 10),
                spawn_box=(flower["x"], flower["y"], 0, 0),
                lifetime=15,
                color=(int(255 * random.random()), int(255 * random.random()), int(255 * random.random())),
                apply_gravity=2,
                speed=[(random.random() - 0.5) * 20, -80 * random.random()],
                spread=[50, 30],
                active=True,
                size_over_lifetime=True,
                size=10,
                once=True,
            )
        )

    def append_flower(self, highlight):
        pos = highlight[0]
        image = self.images[0]
        offset = (image.get_width() / 2, image.get_height() / 2)
        flower = {
            "x": pos[0],
            "y": pos[1],
            "t": (highlight[1], highlight[2]),
            "offset_x": offset[0],
            "offset_y": offset[1],
            "image": image,
            "mass": 0.01,
            "seed_mass": 0,
            "maximum_seed_mass": 1,
            "pollinated": False,
            "flowering": False,
            "maximum_mass": self.thresholds[-1],
            "lifetime": 60 * 60 * 24 * 10,  # 10 days of liefetime to grow
            "growth_index": self.active_threshold,
        }  # to get relative size, depending on current threshold - init threshold
        self.flowers.append(flower)
        self.can_add_flower = False
        self.play_reward()

    def get_rect(self):
        return [
            flower["image"].get_rect(
                topleft=(
                    flower["x"] - flower["offset_x"],
                    flower["y"]
                    - flower["offset_y"]
                    + self.camera.offset_y,
                )
            )
            for flower in self.flowers
        ]

    def update(self, dt):
        self.animation.update(dt)
        if self.seed_popped:
            for particle in self.pop_seed_particles:
                particle.update(dt)
        if self.pop_all_seeds_timer > 0:
            self.timeframe -= dt
            len(self.flowers)

    def update_image_size(self, factor=7, base=80):
        pass

    def draw(self, screen):
        self.animation.draw(screen)
        if self.can_add_flower:
            x, y = pygame.mouse.get_pos()
            screen.blit(
                assets.img("sunflowers/2.PNG", (128, 128)),
                (x, y - self.camera.offset_y),
            )

        for flower in self.flowers:
            screen.blit(
                flower["image"],
                (
                    flower["x"] - flower["offset_x"],
                    flower["y"] - flower["offset_y"],
                ),
            )

        if self.target:
            outlines = self.get_outlines()
            for i in range(0, len(self.flowers)):
                s = pygame.Surface((64, 64), pygame.SRCALPHA)
                color = config.WHITE
                if self.flowers[i]["mass"] >= self.flowers[i]["maximum_mass"]:
                    color = config.GREEN
                pygame.draw.lines(s, color, True, outlines[i], 3)
                screen.blit(
                    s,
                    (
                        self.flowers[i]["x"] - flower["offset_x"],
                        self.flowers[i]["y"] - flower["offset_y"],
                    ),
                )

        # progress bar
        for flower in self.flowers:
            if flower["mass"] < flower["maximum_mass"]:
                width = flower["image"].get_width()
                percentage = flower["mass"] / flower["maximum_mass"]
                pygame.draw.rect(
                    screen,
                    config.WHITE,
                    (
                        flower["x"] - flower["offset_x"],
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                        width * percentage,
                        width / 4,
                    ),
                    border_radius=3,
                )
                pygame.draw.rect(
                    screen,
                    config.WHITE_TRANSPARENT,
                    (
                        flower["x"] - flower["offset_x"],
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                        width,
                        width / 4,
                    ),
                    2,
                    3,
                )
                percentage_label = config.SMALL_FONT.render(
                    "{:.0f}".format(percentage * 100), True, config.BLACK
                )
                screen.blit(
                    percentage_label,
                    (
                        flower["x"]
                        - flower["offset_x"]
                        + width / 2
                        - percentage_label.get_width() / 2,
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                    ),
                )
            if flower["flowering"]:
                width = flower["image"].get_width()
                pygame.draw.rect(
                    screen,
                    config.WHITE,
                    (
                        flower["x"] - flower["offset_x"],
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                        width,
                        width / 4,
                    ),
                    border_radius=3,
                )
                seed_mass_label = config.SMALL_FONT.render(
                    "{:.2f}".format(flower["seed_mass"]), True, config.BLACK
                )
                screen.blit(
                    seed_mass_label,
                    (
                        flower["x"]
                        - flower["offset_x"]
                        + width / 2
                        - seed_mass_label.get_width() / 2,
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                    ),
                )

        for particle in self.pop_seed_particles:
            particle.draw(screen)

    def get_outlines(self):
        outlines = []
        for flower in self.flowers:
            mask = pygame.mask.from_surface(flower["image"])
            outline = mask.outline()
            outlines.append(outline)
        return outlines

    """
    Override organ function
    Flowrs should not provide green thumbs
    since they are sinks and only increase the score
    """

    def reach_threshold(self):
        pass
