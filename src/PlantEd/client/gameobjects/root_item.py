import pygame
from pygame import Rect

from PlantEd import config
from PlantEd.client.utils.particle import ParticleSystem


class Root_Item:
    def __init__(self, callback, plant, cost=1):  # take from config
        self.plant = plant
        self.dir = [0, 0]
        self.cost = cost
        self.callback = callback
        self.active = False
        self.particle_system = ParticleSystem(
            100,
            spawn_box=Rect(self.plant.x, self.plant.y + 45, 0, 0),
            lifetime=8,
            color=config.WHITE,
            apply_gravity=False,
            speed=[0, 0],
            spread=[20, 20],
            active=False,
            once=True,
        )

    def update(self, dt):
        self.particle_system.update(dt)

    def handle_event(self, e):
        if self.active:
            if e.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if self.get_validation_rect().collidepoint(mouse_pos):
                    self.callback(pygame.mouse.get_pos())
                    self.deactivate()
                    self.particle_system.spawn_box = Rect(
                        self.plant.x, self.get_validation_rect()[1] + 45, 0, 0
                    )
                    self.particle_system.activate()

    def activate(self):
        self.active = True

    def get_validation_rect(self):
        y = 880 + self.plant.camera.offset_y
        return Rect(0, y, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

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
                pygame.draw.circle(screen, config.WHITE, mouse_pos, 3)
            else:
                pygame.draw.line(
                    screen, config.GRAY, (plant_x, plant_y), mouse_pos, 3
                )
                pygame.draw.circle(screen, config.GRAY, mouse_pos, 3)
