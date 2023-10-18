import pygame


class Camera:
    def __init__(self, offset_y):
        self.offset_y = offset_y
        self.target_offset = self.offset_y
        self.speed = 10

    def update(self, dt):
        diff = self.target_offset - self.offset_y
        if diff != 0:
            diff = diff / abs(diff)
            self.offset_y += diff * self.speed

    def handle_event(self, e: pygame.event.Event):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_w:
            self.target_offset = 0
        if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
            self.target_offset = -400

    def move_up(self):
        self.target_offset = 0

    def move_down(self):
        self.target_offset = -400
