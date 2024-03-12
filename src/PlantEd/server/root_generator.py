import math
import random
from typing import Union
import pygame
import numpy as np

from PlantEd import config


class RootGenerator:
    def __init__(
            self,
            root_grid_size: tuple[int, int] = (20, 6),
            resolution: tuple[int, int] = (1920, 1080)
    ):
        self.root_grid_size = root_grid_size
        self.resolution = resolution
        self.root_grid: np.array = np.zeros(root_grid_size)
        self.root_grid.fill(-1)
        self.FONT_24 = pygame.font.SysFont("timesnewroman", 18)
        self.roots: list[RootStructure] = []
        self.root_grid_mass_list: list[tuple[float, tuple[float, float]]] = []
        self.root_classes = [
            {
                "length": 0.8,
                "gravity_factor": 0,
                "n_branches": 12,
                "tries": 6,
                "mass_factor": 0.6,
                "n_segments": 4,
                "stop_upward": True
            },
            {
                "length": 0.3,  # factor of screen_height
                "gravity_factor": 1,
                "n_branches": 6,
                "tries": 6,
                "mass_factor": 0.35,
                "n_segments": 5,
                "stop_upward": True
            },
            {
                "length": 0.05,
                "gravity_factor": 0,
                "n_branches": 0,
                "tries": 3,
                "mass_factor": 0.05,
                "n_segments": 4,
                "stop_upward": False
            }
        ]
        self.generate_root()

    def delete_roots(self):
        self.roots = []

    def generate_root(self, tier=0, start_mass=1.0, end_mass=10.0, start_pos=(400, 250), direction=(0, 1)):
        root_structure: RootStructure = RootStructure(
            root_grid=self.root_grid.copy(),
            resolution=self.resolution,
            tier=tier,
            tries=self.root_classes[tier]["tries"],
            gravity_effect=self.root_classes[tier]["gravity_factor"],
            start_mass=start_mass,
            end_mass=start_mass + (end_mass - start_mass) * self.root_classes[tier]["mass_factor"],
            start_pos=start_pos,
            length=self.root_classes[tier]["length"] * self.resolution[1],
            direction=direction,
            n_branches=self.root_classes[tier]["n_branches"],
            n_segments=self.root_classes[tier]["n_segments"],
            stop_upward=self.root_classes[tier]["stop_upward"],
        )

        self.roots.append(root_structure)
        for t in root_structure.branches_t:
            self.generate_root(
                tier=root_structure.tier + 1,
                start_mass=start_mass + (end_mass - start_mass) * t,
                end_mass=end_mass,
                direction=get_ortogonal(root_structure.direction),
                start_pos=root_structure.get_pos_at_t(t_branch=t),
            )

    def draw(self, screen, mass):
        for root in self.roots:
            if root.start_mass <= mass:
                root.draw(screen, mass)


class RootStructure:
    def __init__(
            self,
            tier: int,
            tries: int,
            gravity_effect: float,
            start_mass: float,
            end_mass: float,
            start_pos: tuple[float, float],
            length: float,
            direction: tuple[float, float],
            root_grid: np.array,
            resolution: tuple[int, int],
            n_branches: int = 0,
            n_segments: int = 5,
            stop_upward: bool = True,
    ):
        self.tier = tier
        self.tries = tries
        self.gravity_effect = gravity_effect
        self.start_mass = start_mass
        self.end_mass = end_mass
        self.start_pos = start_pos
        self.length = length
        self.direction = normalize_vector(direction)
        self.n_segments = n_segments
        self.n_branches = n_branches
        self.stop_upward = stop_upward
        self.root_grid = root_grid
        self.resolution = resolution

        self.branches_t: list[float] = [random.random() for _ in range(n_branches)]
        self.segments_t: list[float] = [random.random() for _ in range(n_segments)]
        self.segments_t.sort()
        self.segments_t.append(1)  # add ending
        self.segments: list[tuple[float, float]] = [self.start_pos]
        self.generate_segments()
        self.segments_t.insert(0, 0)
        self.add_mass_to_root_grid()

    def add_mass_to_root_grid(self):

        n, m = self.root_grid.shape
        for i in range(1, len(self.segments)):
            previous_point = self.segments[i - 1]
            current_point = self.segments[i]

            # normalize to fit matrix
            x1 = previous_point[0] / self.resolution[0] * n
            y1 = previous_point[1] / self.resolution[1] * m
            x2 = current_point[0] / self.resolution[0] * n
            y2 = current_point[1] / self.resolution[1] * m

            dx = x2 - x1
            dy = y2 - y1

            x = x1
            y = y1

            if abs(dx) > abs(dy):
                steps = abs(dx)
            else:
                steps = abs(dy)
            print(f"steps: {steps}")

            x_increment = dx / steps
            y_increment = dy / steps

            print(f"y_inc: {y_increment}, x_inc: {x_increment}")

            length = max(abs(dx), abs(dy))

            for _ in range(int(steps) + 1):
                print(f"in loop: x: {x}, y: {y}")
                if 0 <= x < n and 0 <= y < m:
                    print(f"dist: delta_x: {abs(x-x1)}, delty_y: {abs(y-y1)}, lenght: {length}")
                    percentage = max(abs(x - x1), abs(y - y1))/length
                    self.root_grid[int(x), int(y)] = percentage
                x += x_increment
                y += y_increment

    def get_pos_at_t(self, t_branch) -> tuple[float, float]:
        pos_at_t = (0, 0)
        # find the segment for the branch
        # get % of the segment length
        for i, segment_t in enumerate(self.segments_t):
            if t_branch <= segment_t:
                next_pos = self.segments[i]
                previous_pos = self.segments[i - 1]
                previous_segment_t = self.segments_t[i - 1]
                percentage = (t_branch - previous_segment_t) / (segment_t - previous_segment_t)
                x = (next_pos[0] - previous_pos[0]) * percentage + previous_pos[0]
                y = (next_pos[1] - previous_pos[1]) * percentage + previous_pos[1]
                pos_at_t = (x, y)
                break

        return pos_at_t

    def generate_segments(self):
        previous_pos = self.start_pos
        t_sum_previous = 0
        for i, segment_t in enumerate(self.segments_t):
            delta_t = segment_t - t_sum_previous
            length = delta_t * self.length
            # random_point = self.generate_random_point(length)

            random_direction = semi_random_vector(
                previous_direction=self.direction,
                gravity_effect=self.gravity_effect,
                num_tries=self.tries,
                stop_upwards=self.stop_upward)
            random_point = (random_direction[0] * length, random_direction[1] * length)

            next_pos = (random_point[0] + previous_pos[0], random_point[1] + previous_pos[1])
            self.segments.append(next_pos)

            previous_pos = next_pos
            t_sum_previous += delta_t

    def draw(self, screen, mass):
        percentage = 1
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
                    x = (next_pos[0] - previous_pos[0]) * percentage_segment + previous_pos[0]
                    y = (next_pos[1] - previous_pos[1]) * percentage_segment + previous_pos[1]
                    end_pos = (x, y)

                    points_to_draw.append(end_pos)
                    break
                else:
                    points_to_draw.append(self.segments[i])
        else:
            points_to_draw = self.segments
        pygame.draw.lines(screen, color=config.WHITE, closed=False, points=points_to_draw, width=3)


def get_ortogonal(v1):
    flip = random.randint(0, 1) * 2 - 1
    orthogonal_vector = (-v1[1] * flip, v1[0])
    return orthogonal_vector

def add_vector(vector_a: tuple[float, float], vector_b: tuple[float, float]) -> tuple[float, float]:
    return vector_a[0] + vector_b[0], vector_a[1] + vector_b[1]


def semi_random_vector(previous_direction: tuple[float, float], gravity_effect: float, num_tries: int,
                       stop_upwards: bool = False) -> Union[None, tuple[float, float]]:
    # Normalize the desired direction
    gravity_vector = (0, gravity_effect)
    previous_direction = normalize_vector(previous_direction)
    desired_direction = add_vector(previous_direction, gravity_vector)
    # Initialize variables to keep track of the closest vector and its angle difference
    closest_vector = None
    min_angle_diff = float('inf')

    # Iterate for the specified number of tries
    for _ in range(num_tries):
        # Generate a random 2D vector
        if stop_upwards:
            random_vector = [random.uniform(-1, 1), random.uniform(0, 1)]
        else:
            random_vector = [random.uniform(-1, 1), random.uniform(-1, 1)]
        random_vector = normalize_vector(random_vector)

        # Calculate the angle between the random vector and the desired direction
        angle = angle_between_vectors(random_vector, desired_direction)

        # Update closest vector if this random vector has a smaller angle difference
        if angle < min_angle_diff:
            min_angle_diff = angle
            closest_vector = random_vector
    return closest_vector


def normalize_vector(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)
    return vector[0] / length, vector[1] / length if length != 0 else [0, 0]


def angle_between_vectors(vec1: tuple[float, float], vec2: tuple[float, float]) -> float:
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
    magnitude_product = math.sqrt(vec1[0] ** 2 + vec1[1] ** 2) * math.sqrt(vec2[0] ** 2 + vec2[1] ** 2)
    angle = math.acos(dot_product / magnitude_product)
    return angle


def get_direction_from_points(point_a: tuple[float, float], point_b: tuple[float, float]) -> tuple[float, float]:
    x = point_b[0] - point_a[0]
    y = point_b[1] - point_a[1]
    return normalize_vector((x, y))
