import numpy as np
import pygame
from numpy import ndarray

MINIMUM_CELL_AMOUNT_TO_DRAW: int = 20
MAX_TO_DRAW: int = 20


class Grid:
    def __init__(
            self,
            pos: tuple[int, int] = (0, 900),
            grid_size: tuple[int, int] = (20, 6),
            max_cell: int = 100000
    ):

        self.pos = pos
        self.grid: ndarray = np.zeros(grid_size)
        self.max_cell = max_cell

        self.offset_grid: ndarray = np.random.randint(0, 90, (2, MAX_TO_DRAW, grid_size[0], grid_size[1]))
        self.grid_screen = pygame.Surface((1920, 1080), pygame.SRCALPHA)

    def draw(self, screen):
        """
            draws a grid of size width i : shape(0)-1, height j : shape(1)
            each cell contains k drops that vary in color
            the offset_grid provides random offsets for size: i,j and k drops in x and y dimensions
            """
        for i in range(0, self.grid.shape[0] - 1):
            for j in range(0, self.grid.shape[1]):
                cell = self.grid[i, j]

                if cell > MINIMUM_CELL_AMOUNT_TO_DRAW:
                    offset_x = self.offset_grid[0, 0, i, j]
                    offset_y = self.offset_grid[1, 0, i, j]
                    pygame.draw.circle(
                        surface=screen,
                        # color variations
                        color=(90, 40 + int(offset_x / 4), 10 + int(offset_y / 4)),
                        center=(
                            self.pos[0] + i * 100 + offset_x,
                            self.pos[1] + j * 100 + offset_y,
                        ),
                        radius=min(15,int(cell / (self.max_cell / 5) + int(offset_x/10))),
                    )

                    n_drops = min(MAX_TO_DRAW, int(cell / (self.max_cell / 20)))
                    for k in range(0, n_drops):
                        offset_x = self.offset_grid[0, k, i, j]
                        offset_y = self.offset_grid[1, k, i, j]
                        pygame.draw.circle(
                            surface=screen,
                            # color variations
                            color=(90, 40 + int(offset_x / 4), 10 + int(offset_y / 4)),
                            center=(
                                self.pos[0] + i * 100 + offset_x,
                                self.pos[1] + j * 100 + offset_y,
                            ),
                            radius=min(15, int(cell / (self.max_cell / 5) + int(offset_x/10))),
                        )
