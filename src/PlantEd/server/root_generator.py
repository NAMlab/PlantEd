import math
import random
from typing import Union
import numpy as np

from PlantEd.constants import MAXIMUM_ROOT_BIOMASS_GRAM, ROOT_GRID_SIZE


class RootGenerator:
    def __init__(
            self,
            start_pos: tuple[int, int] = (10, 0),
            delta_mass_to_get_grid: float = MAXIMUM_ROOT_BIOMASS_GRAM/20
    ):
        self.start_pos = start_pos
        self.delta_mass_to_get_grid = delta_mass_to_get_grid
        self.root_grid_size = ROOT_GRID_SIZE
        self.root_grids: list[np.array] = []
        self.current_grid: np.array = None
        self.current_grid_mass: float = 0
        self.roots: list[list[RootStructure]] = []
        self.root_classes = [
            {
                "length": 0.2,
                "gravity_factor": 0,
                "n_branches": 6,
                "tries": 9,
                "mass_factor": 0.7,
                "n_segments": 6,
                "stop_upward": True
            },
            {
                "length": 0.05,  # factor of screen_height
                "gravity_factor": 1,
                "n_branches": 6,
                "tries": 4,
                "mass_factor": 0.35,
                "n_segments": 4,
                "stop_upward": True
            },
            {
                "length": 0.01,
                "gravity_factor": 0,
                "n_branches": 0,
                "tries": 3,
                "mass_factor": 0.05,
                "n_segments": 3,
                "stop_upward": False
            }
        ]

    def to_dict(self, root_ids: list[int]) -> dict:
        root_lists_to_send = []
        for id in root_ids:
            for root_list in self.roots:
                if root_list[0].root_id == id:
                    root_lists_to_send.append(root_list)
        return {
            "start_pos": self.start_pos,
            "root_grid_size": self.root_grid_size,
            "roots": [[root.to_dict() for root in root_list] for root_list in root_lists_to_send]
        }

    def get_matrix_at_mass(self, mass_list: list[float]) -> np.array:
        combined_grid = self.current_grid

        if sum(mass_list) - self.current_grid_mass > self.delta_mass_to_get_grid or self.current_grid is None:
            combined_grid = np.zeros(self.root_grid_size)
            for x in range(self.root_grid_size[0]):
                for y in range(self.root_grid_size[1]):
                    for grid, mass in zip(self.root_grids, mass_list):
                        if grid[x, y] <= mass and grid[x, y] != -1:
                            combined_grid[x, y] = 1
            #print(f"for a mass of: {mass_list}")
            #print(f"the grid looks like: {combined_grid}")
            self.current_grid = combined_grid
            self.current_grid_mass = sum(mass_list)
        return combined_grid

    def delete_roots(self):
        self.roots = []
        self.root_grids = []

    def generate_root_list(self, id, direction=(0, 1), start_mass=0):
        root_list = self.generate_root(id, direction=direction, start_mass=start_mass)
        self.roots.append(root_list)
        grid = np.zeros(self.root_grid_size)
        grid.fill(100)
        self.root_grids.append(grid)
        for root in self.roots[id]:
            root.add_mass_to_root_grid(self.root_grids[id])

    def generate_root(
            self,
            root_id=None,
            root_list=None,
            tier=0,
            start_mass=0.0,
            end_mass=None,
            direction=(0, 1),
            start_pos=None,
    ):
        if end_mass is None:
            end_mass = MAXIMUM_ROOT_BIOMASS_GRAM + start_mass
        if root_id is None:
            root_id = len(self.roots)
        if root_list is None:
            root_list = []
        if start_pos is None:
            start_pos = self.start_pos
        root_structure: RootStructure = RootStructure(
            root_id=root_id,
            tier=tier,
            tries=self.root_classes[tier]["tries"],
            gravity_effect=self.root_classes[tier]["gravity_factor"],
            start_mass=start_mass,
            end_mass=start_mass + (end_mass - start_mass) * self.root_classes[tier]["mass_factor"],
            start_pos=start_pos,
            length=self.root_classes[tier]["length"] * self.root_grid_size[0],
            direction=direction,
            n_branches=self.root_classes[tier]["n_branches"],
            n_segments=self.root_classes[tier]["n_segments"],
            stop_upward=self.root_classes[tier]["stop_upward"],
        )

        root_list.append(root_structure)
        for t in root_structure.branches_t:
            self.generate_root(
                root_list=root_list,
                root_id=root_id,
                tier=root_structure.tier + 1,
                start_mass=start_mass + (end_mass - start_mass) * t,
                end_mass=root_structure.end_mass,
                direction=get_ortogonal(root_structure.direction),
                start_pos=root_structure.get_pos_at_t(t_branch=t),
            )
        return root_list

    def draw(self, screen, mass):

        '''for grid in self.root_grids:
            n, m = grid.shape
            for x in range(n):
                for y in range(m):
                    if grid[x, y] > 0:
                        pygame.draw.rect(screen, config.WHITE_TRANSPARENT, (
                            x / n * self.resolution[0], y / m * self.resolution[1], self.resolution[0] / n,
                            self.resolution[1] / m))

                        mass_label = self.FONT_24.render(f"{grid[x, y]:.2f}", True, config.BLACK)
                        screen.blit(mass_label, (x/n*self.resolution[0], y/m*self.resolution[1]))'''

        for root_list in self.roots:
            for root in root_list:
                if root.start_mass <= mass:
                    root.draw(screen, mass)


class RootStructure:
    def __init__(
            self,
            root_id: int,
            tier: int,
            tries: int,
            gravity_effect: float,
            start_mass: float,
            end_mass: float,
            start_pos: tuple[float, float],
            length: float,
            direction: tuple[float, float],
            n_branches: int = 0,
            n_segments: int = 5,
            stop_upward: bool = True,
    ):
        self.root_id = root_id
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

        self.branches_t: list[float] = [random.random() for _ in range(n_branches)]
        self.segments_t: list[float] = [random.random() for _ in range(n_segments)]
        self.segments_t.sort()
        self.segments_t.append(1)  # add ending
        self.segments: list[tuple[float, float]] = [self.start_pos]
        self.generate_segments()
        self.segments_t.insert(0, 0)

    def to_dict(self) -> dict:
        return {
            "id": self.root_id,
            "start_mass": self.start_mass,
            "end_mass": self.end_mass,
            "segments_t": self.segments_t,
            "segments": self.segments
        }

    def add_mass_to_root_grid(self, root_grid) -> np.array:
        n, m = root_grid.shape

        for i in range(1, len(self.segments)):
            x1 = self.segments[i - 1][0]
            y1 = (self.segments[i - 1][1])
            x2 = self.segments[i][0]
            y2 = (self.segments[i][1])

            prev_t = self.segments_t[i - 1]
            next_t = self.segments_t[i]

            dx = x2 - x1
            dy = y2 - y1
            steps = max(abs(dx), abs(dy))

            if steps == 0:  # If the points are the same, return just the starting point
                return [(x1, y1)]

            step_x = dx / steps
            step_y = dy / steps

            for j in range(int(steps) + 1):
                x = x1 + step_x * j
                y = y1 + step_y * j
                percentage_line = (x1 - x) / dx if dx != 0 else (y1 - y) / dy
                t = prev_t + (next_t - prev_t) * percentage_line

                mass_at_point = self.start_mass + (self.end_mass - self.start_mass) * t

                if 0 <= x < n and 0 <= y < m:
                    if mass_at_point < root_grid[int(x), int(y)]:
                        root_grid[int(x), int(y)] = mass_at_point
        return root_grid

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
