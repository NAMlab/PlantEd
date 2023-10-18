import pygame
from pygame import Rect
from pygame.locals import *

from PlantEd_Server import config
from PlantEd_Server.config import NITRATE_FILL_CELL
from PlantEd_Server.data import assets
from PlantEd_Server.client.utils.particle import ParticleSystem

class Blue_grain:
    def __init__(self,
                 pos,
                 amount: int = 50000,
                 play_sound=None,
                 nitrate_grid=None
                 ):
        self.image = assets.img("blue_grain_bag.PNG", (128, 128))
        self.pos = pos
        self.amount = amount
        self.play_sound = play_sound
        self.active = False
        self.nitrate_grid = nitrate_grid
        self.particle_system = ParticleSystem(
            80,
            spawn_box=Rect(self.pos[0], self.pos[1], 50, 50),
            boundary_box=Rect(
                0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT - 220
            ),
            lifetime=25,
            size=10,
            color=config.NITRATE_BROWN,
            apply_gravity=True,
            speed=[20, 70],
            spread=[60, 10],
            active=False,
            once=True,
            color_spectrum=10,
            size_over_lifetime=False,
        )

    def activate(self, pos=None):
        pos = pos if pos else pygame.mouse.get_pos()
        self.pos = (
            (
                int(pos[0] - self.image.get_width() / 2),
                int(pos[1] - self.image.get_height() / 2),
            )
            if pos
            else (0, 0)
        )
        self.active = True
        pygame.mouse.set_visible(False)

    def deactivate(self):
        self.active = False
        pygame.mouse.set_visible(True)

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x + 120, y + 120)
        if e.type == MOUSEBUTTONDOWN:
            self.particle_system.spawn_box = Rect(
                self.pos[0], self.pos[1], 20, 20
            )
            self.play_sound()
            self.particle_system.activate()
            if self.nitrate_grid is not None:
                lower_limit_grid = max(0, int(self.pos[0]/100)-3)
                upper_limit_grid = max(0, int(self.pos[0]/100)+3)
                # (x,y,value)
                cells_to_fill = []
                for i in range(lower_limit_grid, upper_limit_grid):
                    cells_to_fill.append((i, 0, NITRATE_FILL_CELL))
                self.nitrate_grid.fertilize(cells_to_fill)
                print(cells_to_fill)
            self.deactivate()

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            screen.blit(self.image, self.pos)
