import pygame
from pygame import Rect

from PlantEd import config
from PlantEd.client.utils.particle import ParticleSystem


class Root_Item:
    def __init__(
            self,
            screen_size: tuple[int, int],
            callback: callable,
            plant,
            check_refund: callable,
            finalize_shop_transaction: callable,
            cost=1
    ):  # take from config

        self.screen_size = screen_size
        self.callback = callback
        self.plant = plant
        self.check_refund = check_refund
        self.finalize_shop_transaction = finalize_shop_transaction
        self.dir = [0, 0]
        self.cost = cost
        self.active = False
        self.particle_system = ParticleSystem(
            100,
            spawn_box=Rect(self.plant.x, self.plant.y + 45, 0, 0),
            lifetime=1,
            size_over_lifetime=True,
            color=config.WHITE,
            vel=(200, 200),
            spread=(-400, -400),
            active=False,
            once=True,
        )

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if self.active:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.check_refund(mouse_pos, self.cost):
                    self.deactivate()
                    return

                if self.get_validation_rect().collidepoint(mouse_pos):
                    self.callback(pygame.mouse.get_pos())
                    self.deactivate()
                    self.particle_system.spawn_box = Rect(
                        self.plant.x, self.get_validation_rect()[1] + 45, 0, 0
                    )
                    self.particle_system.activate()
                    self.finalize_shop_transaction()

    def activate(self):
        self.active = True

    def get_validation_rect(self):
        y = self.screen_size[1]/1.15 + self.plant.camera.offset_y
        return Rect(0, y, self.screen_size[0], self.screen_size[1])

    def deactivate(self):
        self.active = False

    def draw(self, screen):
        self.particle_system.draw(screen)
        if self.active:
            mouse_pos = pygame.mouse.get_pos()
            plant_x, plant_y = (
                self.plant.x,
                self.plant.y + 45 + self.plant.camera.offset_y,
            )
            # length = math.sqrt((plant_x-mouse_pos[0])**2+(plant_y-mouse_pos[1])**2)
            if self.get_validation_rect().collidepoint(mouse_pos):
                pygame.draw.line(
                    screen, config.WHITE, (plant_x, plant_y), mouse_pos, 3
                )
                pygame.draw.circle(screen, config.WHITE, mouse_pos, 10)
            else:
                pygame.draw.line(
                    screen, config.GRAY, (plant_x, plant_y), mouse_pos, 3
                )
                pygame.draw.circle(screen, config.GRAY, mouse_pos, 10)
