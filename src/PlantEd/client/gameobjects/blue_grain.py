import pygame
from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN

from PlantEd import config
from PlantEd.constants import NITRATE_FERTILIZE_AMOUNT
from PlantEd.data.assets import AssetHandler
from PlantEd.client.utils.particle import ParticleSystem


class Blue_grain:
    def __init__(
        self,
        screen_size: tuple[int, int],
        pos,
        check_refund: callable,
        finalize_shop_transaction: callable,
        cost: int,
        amount: int = NITRATE_FERTILIZE_AMOUNT,
        play_sound=None,
        nitrate_grid=None,
    ):
        self.screen_size = screen_size
        self.asset_handler = AssetHandler.instance()
        self.image = self.asset_handler.img("blue_grain_bag.PNG", (128, 128))
        self.pos = pos
        self.check_refund = check_refund
        self.finalize_shop_transaction = finalize_shop_transaction
        self.cost = cost
        self.amount = amount
        self.play_sound = play_sound
        self.active = False
        self.nitrate_grid = nitrate_grid
        self.particle_system = ParticleSystem(
            80,
            spawn_box=Rect(self.pos[0], self.pos[1], 50, 50),
            boundary_box=Rect(0, 0, self.screen_size[0], self.screen_size[1]),
            lifetime=2,
            size=10,
            color=config.NITRATE_BROWN,
            gravity=500,
            vel=(-50, -150),
            spread=(450, 50),
            active=False,
            once=True,
        )

    def activate(self, pos=None):
        pos = pos if pos else pygame.mouse.get_pos()
        self.pos = pos

        self.active = True
        pygame.mouse.set_visible(False)

    def deactivate(self):
        self.active = False
        self.finalize_shop_transaction()
        pygame.mouse.set_visible(True)

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x, y)
        if e.type == MOUSEBUTTONDOWN:
            if self.check_refund(self.pos, self.cost):
                self.deactivate()
                return
            self.particle_system.spawn_box = Rect(self.pos[0], self.pos[1], 20, 20)
            self.play_sound()
            self.particle_system.deactivate()
            self.particle_system.activate()
            if self.nitrate_grid is not None:
                lower_limit_grid = max(
                    0, int(self.pos[0] / (self.screen_size[0] / 10)) + 3
                )
                upper_limit_grid = max(
                    0, int(self.pos[0] / (self.screen_size[0] / 10)) + 8
                )
                print(f"LOWER IM: {lower_limit_grid}, UPPER LIM: {upper_limit_grid}")
                # (x,y,value)
                cells_to_fill = []
                for i in range(lower_limit_grid, upper_limit_grid):
                    n_cells = upper_limit_grid - lower_limit_grid
                    cells_to_fill.append((i, 0, 1 / n_cells))
                self.nitrate_grid.fertilize(cells_to_fill)
            self.deactivate()

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            pygame.draw.circle(screen, config.WHITE, self.pos, radius=10)
            screen.blit(self.image, self.pos)
