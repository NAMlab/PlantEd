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
from PlantEd import constants
from PlantEd.client.camera import Camera
from PlantEd.constants import START_SUM_BIOMASS_GRAM
from PlantEd.data.assets import AssetHandler
from PlantEd.data.sound_control import SoundControl
from PlantEd.client.gameobjects.shop import FloatingShop
from PlantEd.server.lsystem import DictToRoot
from PlantEd.client.utils.particle import ParticleSystem
from PlantEd.client.utils.spline import Cubic_Tree, Cubic

logger = logging.getLogger(__name__)

WIN = pygame.USEREVENT + 1


class Plant:
    LEAF = 1
    STEM = 2
    ROOTS = 3
    STARCH = 4
    FLOWER = 5

    @staticmethod
    def from_dict(plant_dict, camera=None):
        asset_handler = AssetHandler.instance()
        pivot_pos = [
            (286, 113),
            (76, 171),
            (254, 78),
            (19, 195),
            (271, 114),
            (47, 114),
        ]
        leaves = [
            (asset_handler.img("leaves/{index}.PNG".format(index=i)))
            for i in range(0, 6)
        ]
        flowers = [
            (asset_handler.img("sunflowers/{index}.PNG".format(index=i), (64, 64)))
            for i in range(0, 3)
        ]
        sound_control = SoundControl()
        plant = Plant(
            pos=plant_dict["pos"],
            water_grid_shape=plant_dict["water_grid_shape"],
            water_grid_pos=plant_dict["water_grid_pos"],
            sound_control=sound_control,
            camera=camera
        )

        plant.organs[0].mass = plant_dict["leaf"]["mass"]
        plant.organs[0].leaves = plant_dict["leaf"]["leaves"]
        for leaf in plant.organs[0].leaves:
            leaf["image"] = leaves[int(random.random() * len(leaves))]
            plant.organs[0].update_leaf_image(leaf)
        branches: list[Cubic] = []
        branches_dict_list = plant_dict["stem"]["curve"]["branches"]
        for branch in branches_dict_list:
            branches.append(Cubic(branch["branch"]))
        plant.organs[1].mass = plant_dict["stem"]["mass"]
        plant.organs[1].curve = Cubic_Tree(branches=branches)

        plant.organs[2].mass = plant_dict["root"]["mass"]
        plant.organs[2].ls = DictToRoot().load_root_system(plant_dict["root"]["ls"])
        plant.organs[3].mass = plant_dict["flower"]["mass"]
        plant.organs[3].flowers = plant_dict["flower"]["flowers"]
        for flower in plant.organs[3].flowers:
            flower["image"] = flowers[int(random.random() * len(flowers))]
        return plant

    def __init__(
            self,
            pos: tuple[float, float],
            water_grid_shape: tuple[int, int],
            water_grid_pos: tuple[float, float],
            upgrade_points: int = 20,
            sound_control: SoundControl = None,
            camera: Camera = None
    ):
        self.x: float = pos[0]
        self.y: float = pos[1]
        self.asset_handler = AssetHandler.instance()
        self.water_grid_shape = water_grid_shape
        self.water_grid_pos = water_grid_pos
        self.max_water_pool = 1
        self.water_pool = 1
        self.sound_control = sound_control
        self.upgrade_points: int = upgrade_points
        self.camera: Camera = camera
        self.danger_mode: bool = False

        pivot_pos = [
            (286, 113),
            (76, 171),
            (254, 78),
            (19, 195),
            (271, 114),
            (47, 114),
        ]
        leaves = [
            (self.asset_handler.img("leaves/{index}.PNG".format(index=i)))
            for i in range(0, 6)
        ]
        flowers = [
            (self.asset_handler.img("sunflowers/{index}.PNG".format(index=i), (64, 64)))
            for i in range(0, 3)
        ]

        organ_leaf = Leaf(
            x=self.x,
            y=self.y,
            name="Leaves",
            organ_type=self.LEAF,
            callback=self.set_target_organ_leaf,
            images=leaves,
            pivot_positions = pivot_pos,
            hover_leaf = self.asset_handler.img("leaf_small.PNG", (128, 128)),
            mass=constants.START_LEAF_BIOMASS_GRAM,
            active=False,
            camera=self.camera,
            play_reward=self.sound_control.play_reward_sfx,
        )
        organ_flower = Flower(
            x=self.x,
            y=self.y,
            name="Flower",
            organ_type=self.FLOWER,
            callback=self.set_target_organ_flower,
            images=flowers,
            hover_image=self.asset_handler.img("sunflowers/2.PNG", (128, 128)),
            mass=constants.START_SEED_BIOMASS_GRAM,
            active=False,
            camera=self.camera,
            play_reward=self.sound_control.play_reward_sfx,
        )
        organ_stem = Stem(
            x=self.x,
            y=self.y,
            name="Stem",
            organ_type=self.STEM,
            callback=self.set_target_organ_stem,
            mass=constants.START_STEM_BIOMASS_GRAM,
            leaf=organ_leaf,
            flower=organ_flower,
            active=False,
            camera=self.camera,
            play_reward=self.sound_control.play_reward_sfx,
        )
        organ_root = Root(
            x=self.x,
            y=self.y,
            name="Roots",
            organ_type=self.ROOTS,
            callback=self.set_target_organ_root,
            mass=constants.START_ROOT_BIOMASS_GRAM,
            active=True,
            water_grid_shape=water_grid_shape,
            water_grid_pos=water_grid_pos,
            camera=self.camera,
            play_reward=self.sound_control.play_reward_sfx,
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
            camera=self.camera
        )

        beans = [
            self.asset_handler.img("bean_growth/{}.PNG".format(index), (150, 150))
            for index in range(0, 6)
        ]

        self.seedling = Seedling(self.x, self.y, beans, START_SUM_BIOMASS_GRAM)
        self.organs = [organ_leaf, organ_stem, organ_root, organ_flower]
        # Fix env constraints

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

    def get_stomata_open(self) -> bool:
        return self.organs[0].stomata_open

    def update_organ_masses(self, organ_masses):
        self.organs[0].update_masses(organ_masses["leafs"])
        self.organs[1].update_mass(organ_masses["stem_mass"])
        self.organs[2].update_mass(organ_masses["root_mass"])
        self.organs[3].update_masses(organ_masses["seed_mass"])
        # self.organ_starch.starch_intake = growth_rates.starch_intake * growth_boost

    def get_biomass(self):
        biomass = 0
        for organ in self.organs:
            biomass += organ.mass
        return biomass

    # Todo dirty to reduce mass like this
    def eat_stem(self, rate, dt):
        pass

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

    def update(self, dt):
        if self.get_biomass() > self.seedling.max and not self.organs[1].active:
            self.organs[1].activate()
            self.organs[0].activate()
        for organ in self.organs:
            organ.update(dt)

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

    def save_image(self, path_to_logs):
        temp_surface = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        self.organs[2].draw(temp_surface)
        self.organs[1].draw(temp_surface)
        self.organs[0].draw(temp_surface)
        self.organs[3].draw(temp_surface)

        pygame.image.save(temp_surface, path_to_logs + "/plant.jpeg")

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
            image: pygame.Surface = None,
            pivot: tuple[float, float] = None,
            mass: float = 1,
            active: bool = False,
            target: bool = False,
            play_reward: callable = None,
            camera: Camera = None,
    ):
        self.x = x
        self.y = y
        self.callback = callback
        self.base_image = image
        self.image = image
        self.pivot = pivot
        self.active = active
        self.name = name
        self.type = organ_type
        self.mass = mass
        self.percentage = 0
        self.update_image_size()
        self.play_reward = play_reward
        self.skills = []
        self.target = target
        self.camera = camera
        self.blocked_growth = False

    def update(self, dt):
        pass

    def set_percentage(self, percentage):
        self.percentage = percentage

    def get_organ_amount(self):
        return 1

    def mass_to_grow(self):
        return 1

    def get_maximum_growable_mass(self):
        return 1

    def get_mass(self):
        return 1

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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            for rect in self.get_rect():
                if rect.collidepoint(event.pos):
                    self.callback()

    """
    Not all organs are active at the start of the game
    """

    def activate(self):
        self.active = True

    """
    Basic draw of an image
    More complex organs need to override this
    """

    def draw(self, screen):
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
        # Todo find new way
        pass
        '''if self.image:
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
            )'''


class Leaf(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            images: list[pygame.Surface],
            pivot_positions: list[Tuple[float, float]],
            hover_leaf: pygame.Surface,
            mass: float,
            active: bool,
            play_reward: callable,
            camera: Camera = None,
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
            camera=camera,
            play_reward=play_reward,
        )
        self.callback = callback
        self.images = images
        self.pivot_positions = pivot_positions
        self.hover_leaf = hover_leaf
        self.photon_intake: float = 0
        self.target_leaf: int = 0
        self.can_add_leaf: bool = False

        self.particle_systems: list[ParticleSystem] = []
        self.shadow_map: np.ndarray = None
        self.shadow_resolution: int = 0
        self.max_shadow: int = 0
        self.stomata_open = False
        self.blocked_growth = False
        self.growth_intervals = [0.1, 0.2, 0.3, 0.4, 0.5]

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

    def activate_add_leaf(self):
        self.can_add_leaf = True

    def to_dict(self) -> dict:
        cleared_leaves = self.leaves.copy()
        for leaf in cleared_leaves:
            leaf.pop("image")
        leaf_dict = {
            "mass": self.get_mass(),
            "leaves": cleared_leaves
        }
        return leaf_dict

    def get_shadowscore(self):
        # shadow scores are 0 for no shadow to 1 for full shadow. 1 - to get a factor
        return (
            sum([1 - leaf["shadow_score"] for leaf in self.leaves])
            / len(self.leaves)
            if len(self.leaves) > 0
            else 0
        )

    def update_masses(self, new_leaf_mass):
        delta_mass = new_leaf_mass - self.get_mass()
        if delta_mass <= 0 or len(self.leaves) <= 0:
            return
        growable_leaves = []
        for leaf in self.leaves:
            if leaf["mass"] < leaf["maximum_mass"]:
                growable_leaves.append(leaf)
        n_leaves_to_grow = len(growable_leaves)
        if n_leaves_to_grow <= 0:
            return
        delta_each_leaf = delta_mass / n_leaves_to_grow
        growable_leaves.sort(key=lambda leaf: leaf["mass"])
        for leaf in growable_leaves:
            if leaf["mass"] + delta_each_leaf > leaf["maximum_mass"]:
                overflow_mass = leaf["maximum_mass"] - leaf["mass"] + delta_each_leaf
                n_leaves_to_grow -= 1
                if n_leaves_to_grow <= 0:
                    break
                delta_each_leaf = (delta_mass + overflow_mass) / n_leaves_to_grow

            else:
                leaf["mass"] += delta_each_leaf

        # adjust image sizes
        for leaf in self.leaves:
            relative_mass = leaf["mass"] / leaf["maximum_mass"]
            if relative_mass*10 > leaf["size"]:
                leaf["size"] += 1
                self.update_leaf_image(leaf)

    def get_organ_amount(self):
        return len(self.leaves)

    def mass_to_grow(self):
        return self.get_maximum_growable_mass() - self.get_mass()

    def get_maximum_growable_mass(self):
        return (
            sum([leaf["maximum_mass"] for leaf in self.leaves])
        )

    def get_mass(self):
        return (
            sum([leaf["mass"] for leaf in self.leaves])
        )

    def append_leaf(self, highlight: Tuple[list[int], int, int]):
        self.play_reward()
        pos = highlight[0]
        dir = pos[0] - pygame.mouse.get_pos()[0]
        if dir > 0:
            image_id = random.randrange(0, len(self.images) - 1, 2)
            image = self.images[image_id]
            offset = self.pivot_positions[image_id]
        else:
            image_id = random.randrange(1, len(self.images), 2)
            image = self.images[image_id]
            offset = self.pivot_positions[image_id]

        leaf = {
            "id": 0,
            "x": pos[0],
            "y": pos[1],
            "t": (highlight[1], highlight[2]),
            "shadow_score": 0,
            "image": image,
            "offset_x": offset[0],
            "offset_y": offset[1],
            "mass": constants.START_LEAF_BIOMASS_GRAM,
            "maximum_mass": constants.MAXIMUM_LEAF_BIOMASS_GRAM,
            "base_image_id": image_id,
            "direction": dir,
            "size": 0,
        }

        self.update_leaf_image(leaf)
        self.particle_systems.append(
            ParticleSystem(
                20,
                spawn_box=Rect(leaf["x"], leaf["y"], 0, 0),
                lifetime=6,
                color=config.YELLOW,
                vel=(0, -5),
                spread=(5, 5),
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

    def update(self, dt):
        if self.mass_to_grow() <= 0:
            self.blocked_growth = True
        else:
            self.blocked_growth = False

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
                adapted_pi = min(10, int(self.photon_intake / 50 * 3 + 5))
                self.particle_systems[i].lifetime = adapted_pi
                self.particle_systems[i].activate()
            else:
                self.particle_systems[i].deactivate()

    # Todo make new after server mass limit
    def update_leaf_image(self, leaf, factor=7, base=80):
        base_image = self.images[leaf["base_image_id"]]
        base_offset = self.pivot_positions[leaf["base_image_id"]]
        ratio = base_image.get_height() / base_image.get_width()
        new_width = (leaf["size"] * factor) + base
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
        if self.can_add_leaf:
            x, y = pygame.mouse.get_pos()
            screen.blit(
                self.hover_leaf,
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
            play_reward: callable = None,
            camera: Camera = None,

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
            play_reward=play_reward,
            camera=camera,
        )
        self.selected = 0
        #root_grid: np.array = np.zeros(water_grid_shape)
        #water_grid_pos: tuple[float, float] = water_grid_pos

        self.ls = None #LSystem = LSystem(root_grid, water_grid_pos)
        self.new_roots = []

    def to_dict(self) -> dict:
        root_dict = {
            "mass": self.mass,
            "ls": self.ls.to_dict() if self.ls else None
        }
        return root_dict

    def check_can_add_root(self):
        return True

    def update(self, dt):
        pass

    def pop_new_root(self) -> dict:
        if len(self.new_roots) > 0:
            new_roots_dic = {
                "directions": self.new_roots
            }
            self.new_roots = []
            return new_roots_dic
        else:
            return None

    def get_organ_amount(self):
        if self.ls is not None:
            return len(self.ls.first_letters)
        else:
            return 0

    def mass_to_grow(self):
        return self.get_maximum_growable_mass() - self.get_mass()

    def get_maximum_growable_mass(self):
        return (
            constants.MAXIMUM_ROOT_BIOMASS_GRAM * max(1,self.get_organ_amount())
        )

    def get_mass(self):
        return self.mass

    def update_mass(self, mass):
        self.mass = mass

    def create_new_root(self, mouse_pos=None, dir=None):
        if self.play_reward is not None:
            self.play_reward()
        if not dir and mouse_pos:
            dir = (mouse_pos[0] - self.x, mouse_pos[1] - (self.y + 45))
        self.new_roots.append(dir)

    def get_root_grid(self):
        return self.ls.root_grid if self.ls else None

    def handle_event(self, event):
        pass

    def draw(self, screen):
        if self.ls is not None:
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
            play_reward: callable = None,
            camera: Camera = None,
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

        super().__init__(
            x=x,
            y=y,
            name=name,
            organ_type=organ_type,
            callback=callback,
            image=image,
            mass=mass,
            active=active,
            play_reward=play_reward,
            camera=camera,
        )

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

    # Todo find out why always true is return
    def check_can_add_leaf(self):
        return True

    def get_organ_amount(self):
        return len(self.curve.branches)

    def mass_to_grow(self):
        return self.get_maximum_growable_mass() - self.get_mass()

    def get_maximum_growable_mass(self):
        return (
            sum([branch.maximum_mass for branch in self.curve.branches])
        )

    def update_mass(self, new_stem_mass):
        delta_mass = new_stem_mass - self.get_mass()
        if delta_mass <= 0 or len(self.curve.branches) <= 0:
            return
        growable_branches = []
        for branch in self.curve.branches:
            if branch.mass < branch.maximum_mass:
                growable_branches.append(branch)
        n_branches_to_grow = len(growable_branches)
        if n_branches_to_grow <= 0:
            return
        delta_each_branch = delta_mass / n_branches_to_grow
        growable_branches.sort(key=lambda branch: branch.mass)
        for branch in growable_branches:
            if branch.mass + delta_each_branch > branch.maximum_mass:
                overflow_mass = branch.maximum_mass - branch.mass + delta_each_branch

                n_branches_to_grow -= 1
                if n_branches_to_grow <= 0:
                    break
                delta_each_branch = (delta_mass + overflow_mass) / n_branches_to_grow

            else:
                branch.mass += delta_each_branch

        # adjust image sizes
        for branch in self.curve.branches:
            relative_mass = branch.mass / branch.maximum_mass
            if relative_mass * 10 > branch.size:
                branch.size += 1
                self.curve.grow(branch)


    def get_mass(self):
        return sum([branch.mass for branch in self.curve.branches])

    def to_dict(self) -> dict:
        stem_dict = {
            "mass": self.mass,
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
                if pygame.time.get_ticks() - self.timer < 300:
                    x, y = pygame.mouse.get_pos()
                    y -= self.camera.offset_y
                    # check how many free spots the stem hast, adapt shop accordingly
                    # no spots -> if flower selected -> flower option
                    # no spots, no flower -> nothing
                    # 1 spot, flower -> all
                    # 1 spot, no flower -> all but flower option

                    free_spots = self.curve.get_free_spots()
                    if free_spots > 0:
                        if self.floating_shop is not None:
                            self.floating_shop.activate(pygame.mouse.get_pos())

    def update_image_size(self, factor=3, base=5):
        pass

    def add_branch(self, highlight, mouse_pos):
        self.play_reward()
        self.curve.add_branch(mouse_pos, highlight)

    def draw(self, screen):
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
            camera=camera
        )
        self.toggle_button = None
        self.starch_intake = 0
        self.max_pool = self.mass

    def update_mass(self, mass):
        self.mass = mass

    def set_percentage(self, percentage):
        self.percentage = percentage
        logger.debug(f" Starch percentage in UI set to {self.percentage}")


class Flower(Organ):
    def __init__(
            self,
            x: float,
            y: float,
            name: string,
            organ_type: int,
            callback: callable,
            images: list[pygame.Surface],
            hover_image: pygame.Surface,
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
            play_reward=play_reward,
            camera=camera,
        )
        self.callback = callback
        self.images = images
        self.asset_handler = AssetHandler.instance()
        self.hover_image = hover_image
        self.can_add_flower: bool = False
        self.target_flower = None

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
                        self.target_flower = i

    def activate_add_flower(self):
        self.can_add_flower = True

    def to_dict(self) -> dict:
        cleared_flowers = self.flowers.copy()
        for flower in cleared_flowers:
            flower.pop("image")

        flower_dict = {
            "mass": sum([flower["mass"] for flower in self.flowers]),
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

    def update_masses(self, mass):
        delta_mass = mass - self.get_mass()
        if delta_mass <= 0 or len(self.flowers) <= 0:
            return
        growable_flowers = []
        for flower in self.flowers:
            if flower["mass"] < flower["maximum_mass"]:
                growable_flowers.append(flower)
        n_flowers_to_grow = len(growable_flowers)
        if n_flowers_to_grow <= 0:
            return
        delta_each_flower = delta_mass / n_flowers_to_grow
        growable_flowers.sort()
        for flower in growable_flowers:
            if flower["mass"] + delta_each_flower > flower["maximum_mass"]:
                overflow_mass = flower["maximum_mass"] - flower["mass"] + delta_each_flower

                n_flowers_to_grow -= 1
                if n_flowers_to_grow <= 0:
                    break
                delta_each_flower = (delta_mass + overflow_mass) / n_flowers_to_grow

            else:
                flower["mass"] += delta_each_flower
        # update image according to mass
        for flower in self.flowers:
            id = min(
                int(
                    flower["mass"]
                    /flower["maximum_mass"]
                    *len(self.images)-1),
                len(self.images)-1)
            flower["image"] = self.images[id]

    def get_random_flower_pos(self):
        viable_flowers = []
        for flower in self.flowers:
            if (
                    not flower["pollinated"]
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
            if flower["mass"] < flower["maximum_mass"]:
                growing_flowers.append(flower)
        # add all seed producing flowrs
        return growing_flowers

    # Todo make correct maxima
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
            "mass": constants.START_SEED_BIOMASS_GRAM,
            "maximum_mass": constants.MAXIMUM_SEED_BIOMASS_GRAM,

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

    def get_organ_amount(self):
        return len(self.flowers)

    def mass_to_grow(self):
        return self.get_maximum_growable_mass() - self.get_mass()

    def get_maximum_growable_mass(self):
        return (
            sum([flower["maximum_mass"] for flower in self.flowers])
        )

    def get_mass(self):
        return (
            sum([flower["mass"] for flower in self.flowers])
        )

    def update(self, dt):
        if self.mass_to_grow() <= 0:
            self.blocked_growth = True
        else:
            self.blocked_growth = False

    def update_image_size(self, factor=7, base=80):
        pass

    def draw(self, screen):
        if self.can_add_flower:
            x, y = pygame.mouse.get_pos()
            screen.blit(
                self.hover_image,
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
                        self.flowers[i]["x"] - self.flowers[i]["offset_x"],
                        self.flowers[i]["y"] - self.flowers[i]["offset_y"],
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
                percentage_label = self.asset_handler.SMALL_FONT.render(
                    "{:.3f}".format(flower["mass"]), True, config.BLACK
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
            '''if True:
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
                mass_label = config.SMALL_FONT.render(
                    "{:.2f}".format(flower["mass"]), True, config.BLACK
                )
                screen.blit(
                    mass_label,
                    (
                        flower["x"]
                        - flower["offset_x"]
                        + width / 2
                        - mass_label.get_width() / 2,
                        flower["y"] - width / 4 - 10 - flower["offset_y"],
                    ),
                )'''

    def get_outlines(self):
        outlines = []
        for flower in self.flowers:
            mask = pygame.mask.from_surface(flower["image"])
            outline = mask.outline()
            outlines.append(outline)
        return outlines

    """
    Override organ function
    Flowers should not provide green thumbs
    since they are sinks and only increase the score
    """

    def reach_threshold(self):
        pass
