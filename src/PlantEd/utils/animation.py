import pygame
from pygame import Rect

from PlantEd import config


class Animation:
    def __init__(self, images, duration, pos=[0, 0], running=True, once=False):
        self.pos = pos
        self.rect = Rect(pos[0], pos[1], 10, 10)
        self.images = images
        self.image = images[0]
        self.duration = duration
        self.timer = 0
        self.interval = duration / len(images)
        # delta time to switch images
        #self.start_interval = self.interval
        self.index = 0
        self.once = once
        self.running = running

    def start(self, pos=None, center=True):
        if pos:
            if center:
                pos = (pos[0]-self.images[0].get_width()/2,pos[1]-self.images[0].get_height()/2-50)
            self.pos = pos
        self.running = True

    def stop(self):
        self.running = False

    def update(self, dt):
        if self.running:
            self.timer += dt
            if self.timer >= self.interval:
                self.index += 1
                self.timer = 0
                if self.index >= len(self.images) - 1:
                    self.index = 0
                    if self.once:
                        self.running = False
                #self.interval += self.start_interval
            self.image = self.images[self.index]

    def draw(self, screen):
        if self.running:
            screen.blit(self.image, self.pos)

    @staticmethod
    def generate_rising_animation(text=None, color=config.RED, image=None, move_up = -3):
        images = []
        frames = 15
        width = 64
        height = 64 #if text is not None else image.get_height()
        increment = 3
        move_up = move_up

        currency_minus_one_surface = pygame.Surface(
            (width + increment * frames, height + increment * frames - move_up * frames * 2),
            pygame.SRCALPHA)

        if text is not None:
            scaleable_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            currency_minus_one_label = config.BIGGER_FONT.render(text, True, color)
            scaleable_surface.blit(currency_minus_one_label, (10, 10))
        if image is not None:
            scaleable_surface = image

        center_w = currency_minus_one_surface.get_width() / 2
        center_h = currency_minus_one_surface.get_height() / 2

        for i in range(0, frames):
            tmp_s = scaleable_surface.copy()
            tmp_s = pygame.transform.scale(
                tmp_s, (width + increment * i, height + increment * i)
            )
            currency_minus_one_surface.fill((255, 255, 255, 0))
            currency_minus_one_surface.blit(tmp_s, (
                center_w - tmp_s.get_width() / 2, center_h - tmp_s.get_height() / 2 + move_up * i))
            addable_s = currency_minus_one_surface.copy()
            images.append(addable_s)
        return images