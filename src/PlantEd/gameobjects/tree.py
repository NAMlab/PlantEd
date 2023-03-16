import config
import pygame


class Tree:
    def __init__(self, pos, images, environment):
        self.pos = pos
        self.images = images
        self.image = images[0]
        self.environment = environment
        self.index = 0

    def apply_shading(self):
        self.image = self.shaded_image(self.image, (0, 0, 0, 10))

    def ghost_image(self, image, color):
        shaded = image.copy()
        shaded.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        return shaded

    def shaded_image(self, image, color):
        copied = image.copy()
        ghost = self.ghost_image(image, color)
        copied.blit(ghost, (0, 0))
        return copied

    def update(self, dt):
        pass
        # days, hours, minutes = self.environment.get_day_time()
        # self.image = self.images[int(days * len(self.images)/config.MAX_DAYS)]

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
            self.apply_shading()
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
            print(self.index)
            # self.image = self.images[self.index]

    def draw(self, screen):
        screen.blit(self.image, self.pos)
