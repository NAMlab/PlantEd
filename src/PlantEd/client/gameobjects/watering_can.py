import pygame
from pygame import Rect
from pygame.locals import MOUSEMOTION, MOUSEBUTTONDOWN, MOUSEBUTTONUP

from PlantEd import config
from PlantEd.client.gameobjects.water_reservoir import Water_Grid
from PlantEd.client.utils.particle import ParticleSystem
from PlantEd.client.utils.gametime import GameTime


class Watering_can:
    def __init__(
        self,
        pos,
        image_active,
        image_inactive,
        check_refund: callable,
        finalize_shop_transaction: callable,
        cost: int,
        water_grid: Water_Grid = None,
        amount: int = config.WATERING_CAN_AMOUNT,
        active=False,
        callback=None,
        play_sound=None,
        stop_sound=None,
    ):  # take from config
        self.gametime = GameTime.instance()
        self.pos = (pos[0] - 20, pos[1] - 120)
        self.water_grid = water_grid  # remove
        self.image_active = image_active
        self.image_inactive = image_inactive
        self.check_refund = check_refund
        self.finalize_shop_transaction = finalize_shop_transaction
        self.cost = cost
        self.image = self.image_inactive
        self.default_amount = amount  # default gamespeed 3s
        self.amount = amount if amount else self.default_amount
        self.rate = int(self.default_amount / 2)
        self.active = active
        self.pouring = False
        self.callback = callback
        self.play_sound = play_sound
        self.stop_sound = stop_sound
        self.rect = Rect(self.pos[0], self.pos[1], 20, 20)
        self.can_particle_system = ParticleSystem(
            290,
            spawn_box=self.rect,
            lifetime=1,
            color=config.BLUE,
            gravity=0.5,
            vel=(-300, 300),
            spread=(500, 500),
            active=False,
        )

    def activate(self, amount=None):
        self.pos = pygame.mouse.get_pos()
        self.active = True
        self.amount = self.default_amount if not amount else amount
        pygame.mouse.set_visible(False)
        self.can_particle_system.spawn_box = self.rect

    def deactivate(self):
        self.image = self.image_inactive
        self.can_particle_system.deactivate()
        self.amount = 0
        self.active = False
        self.pouring = False
        self.water_grid.pouring = False
        self.stop_sound()
        pygame.mouse.set_visible(True)

    def update(self, dt):
        self.can_particle_system.update(dt)
        if self.active and self.pouring:
            if self.water_grid:
                # self.model.water_pool += self.rate
                self.water_grid.pour(self.rate, dt, self.pos)
            if self.callback:
                self.callback(self.rate)
            if self.amount < 0:
                self.amount = 0
                self.deactivate()
            else:
                self.amount -= self.rate * dt

    def handle_event(self, e):
        if not self.active:
            return
        if e.type == MOUSEBUTTONDOWN:
            if self.amount >= self.default_amount:  # if used, cant refund
                if self.check_refund(pygame.mouse.get_pos(), self.cost):
                    self.deactivate()
                    return
            self.image = self.image_active
            self.pouring = True
            self.can_particle_system.activate()
            self.play_sound()
            self.finalize_shop_transaction()
        if e.type == MOUSEBUTTONUP:
            self.image = self.image_inactive
            self.can_particle_system.deactivate()
            self.stop_sound()
            self.pouring = False
        if e.type == MOUSEMOTION:
            x, y = pygame.mouse.get_pos()
            self.pos = (x, y)
            self.rect = Rect(self.pos[0], self.pos[1] + 100, 20, 20)
            self.can_particle_system.spawn_box = self.rect

    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, config.WHITE, self.pos, radius=10)
            screen.blit(self.image, self.pos)
            self.can_particle_system.draw(screen)
