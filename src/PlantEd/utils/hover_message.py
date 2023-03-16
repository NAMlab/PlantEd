import pygame
import config


class Hover_Message:
    def __init__(self, font, line_height, margin):
        self.rect = None
        self.font = font
        self.line_height = line_height
        self.margin = margin
        self.hover_surface = pygame.Surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA
        )
        self.timer = 1
        self.w = 0

    def update(self, dt):
        self.timer -= dt if self.timer > 0 else 0

    def set_message(self, message):
        self.hover_surface.fill((0, 0, 0, 0))
        lines = message.split("*")
        self.w, h = (
            0,
            len(lines) * (self.line_height + self.margin) + self.margin,
        )
        labels = []

        # init label and remember widest
        for i in range(len(lines)):
            config.FONT.render("ls", True, config.BLACK)
            label = self.font.render("{}".format(lines[i]), True, config.BLACK)
            self.w = (
                label.get_width() if self.w < label.get_width() else self.w
            )
            labels.append(label)
        self.w += 2 * self.margin
        pygame.draw.rect(
            self.hover_surface,
            config.WHITE,
            (0, 0, self.w, h),
            border_radius=2,
        )
        for i in range(len(labels)):
            self.hover_surface.blit(
                labels[i],
                (
                    self.margin,
                    (self.line_height + self.margin) * i + self.margin,
                ),
            )

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            self.timer = 1
            self.hover_surface.fill((0, 0, 0, 0))

    def draw(self, screen):
        if self.timer <= 0:
            x, y = pygame.mouse.get_pos()
            x -= self.w if x + self.w > config.SCREEN_WIDTH else 0
            screen.blit(self.hover_surface, (x, y))
