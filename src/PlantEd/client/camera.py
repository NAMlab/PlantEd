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
            diff = diff / abs(diff)
            self.offset_y += diff * self.speed

    def handle_event(self, e: pygame.event.Event):
        if e.type == pygame.MOUSEWHEEL:
            self.offset_y -= e.y*20
            if self.min_y is not None and self.max_y is not None:
                self.offset_y = min(max(self.offset_y, self.min_y), self.max_y)

        if e.type == pygame.KEYDOWN and e.key == pygame.K_w:
            self.target_offset = 0
        if e.type == pygame.KEYDOWN and e.key == pygame.K_s:
            self.target_offset = -400

    def move_up(self):
        self.target_offset = 0

    def move_down(self):
        self.target_offset = -400
