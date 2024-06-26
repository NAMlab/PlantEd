import pygame


class Camera:
    def __init__(self, offset_y, min_y=None, max_y=None):
        self.offset_y = offset_y
        self.target_offset = self.offset_y
        self.speed = 10

        self.min_y = min_y
        self.max_y = max_y

    def update(self, dt):
        diff = self.target_offset - self.offset_y
        if diff != 0:
            if abs(diff) < self.speed:
                self.offset_y += diff
            else:
                diff = diff / abs(diff)
                self.offset_y += diff * self.speed

    def handle_event(self, e: pygame.event.Event):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_w:
            self.target_offset = self.min_y
        if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
            self.target_offset = self.max_y

    def move_up(self):
        self.target_offset = self.min_y

    def move_down(self):
        self.target_offset = self.max_y
