import numpy as np
import pygame

from PlantEd import config
from PlantEd.constants import ROOT_GRID_SIZE


class RootStructureSmall:
    def __init__(
            self,
            id: int,
            start_mass: float,
            end_mass: float,
            segments_t: list[float],
            segments: list[tuple[float, float]],
            resolution: tuple[int, int] = None,
            start_pos: tuple[float, float] = (0, 0)
    ):
        self.id = id
        self.grid_size = ROOT_GRID_SIZE
        self.start_mass = start_mass
        self.end_mass = end_mass
        self.segments_t = segments_t
        self.segments = segments
        self.resolution = resolution
        self.start_pos = start_pos

    def draw(self, screen, mass):
        n, m = self.grid_size
        # if mass is smaller than end_mass -> only draw a part of the root
        if mass < self.end_mass:
            percentage = (mass - self.start_mass) / (self.end_mass - self.start_mass)
            points_to_draw = []
            for i, segment_t in enumerate(self.segments_t):
                if percentage < segment_t:
                    next_pos = self.segments[i]
                    previous_pos = self.segments[i - 1]
                    previous_segment_t = self.segments_t[i - 1]
                    percentage_segment = (percentage - previous_segment_t) / (segment_t - previous_segment_t)
                    x = (((next_pos[0] - previous_pos[0]) * percentage_segment + previous_pos[0]) * self.resolution[0] / n)
                    y = (((next_pos[1] - previous_pos[1]) * percentage_segment + previous_pos[1]) * self.resolution[1] / m) + self.start_pos[1]
                    end_pos = (x, y)
                    points_to_draw.append(end_pos)
                    break
                else:
                    points_to_draw.append(
                        ((self.segments[i][0] * self.resolution[0] / n), (self.segments[i][1] * self.resolution[1] / m) + self.start_pos[1]))
        else:
            points_to_draw = []
            for i, segment_t in enumerate(self.segments_t):
                points_to_draw.append(
                    ((self.segments[i][0] * self.resolution[0] / n), (self.segments[i][1] * self.resolution[1] / m) + self.start_pos[1]))
        pygame.draw.lines(screen, color=config.WHITE, closed=False, points=points_to_draw, width=3)


class RootDrawer:
    def __init__(
            self,
            resolution: tuple[int, int],
            start_pos: tuple[float, float] = (0, 0)
    ):
        self.resolution = resolution
        self.start_pos = start_pos
        self.root_grid_size = ROOT_GRID_SIZE
        self.roots: list[list[RootStructureSmall]] = []

    def add_root_grid(self, root_grid):
        self.root_grids.append(root_grid)

    def add_root_list(self, root: list[RootStructureSmall]):
        self.roots.append(root)

    def draw(self, screen, client_root_list):
        for i, root_list in enumerate(self.roots):
            for root in root_list:
                if root.start_mass <= client_root_list[i][1]:
                    root.draw(screen, mass=client_root_list[i][1])

    def generate_rootlist_from_dict(self, dic):
        self.roots = []
        for root_list_server in dic["roots"]:
            root_list_client = []
            for root_server in root_list_server:
                root_list_client.append(
                    RootStructureSmall(
                        id=root_server["id"],
                        start_mass=root_server["start_mass"],
                        end_mass=root_server["end_mass"],
                        segments_t=root_server["segments_t"],
                        segments=root_server["segments"],
                        start_pos=self.start_pos,
                        resolution=self.resolution
                    )
                )
            grid = np.zeros(self.root_grid_size)
            self.roots.append(root_list_client)
