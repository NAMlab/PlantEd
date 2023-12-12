import random

import pygame

from PlantEd import config
from PlantEd.client.utils.button import Button
from PlantEd.data.assets import AssetHandler


class IconHandler:
    def __init__(self, pos, image=None, image_size=(150, 150), button_size=(80, 80), margin=10, max_row=5):
        self.asset_handler = AssetHandler.instance()
        self.hover = False
        self.selected = False
        self.rect = pygame.Rect(pos[0], pos[1], image_size[0], image_size[1])
        self.button_size = button_size
        self.margin = margin
        self.max_row = max_row
        self.buttons = pygame.sprite.Group()
        self.icon_names = [
            "bird", "bear", "bunny", "cat", "chick", "cow", "dear", "elephant", "fox", "giraffe", "hippo", "hog",
            "horse", "koala", "monkey", "mouse", "owl", "panda", "pavian", "penguin", "pig", "racoon", "sheep", "tiger"]
        icon_name = config.load_options()["icon_name"]
        self.image = self.asset_handler.img(f"animal_icons/{icon_name}.PNG", image_size)

        self.button_window_height = self.margin + int((len(self.icon_names)+1) / self.max_row) * (self.margin + button_size[1])
        self.button_window_width = self.margin + max_row * (self.margin + button_size[0])

        for index, name in enumerate(self.icon_names):
            image = self.asset_handler.img(f"animal_icons/{name}.PNG", button_size)
            self.buttons.add(
                Button(
                    x=pos[0] + self.margin + index % self.max_row * (button_size[0]+ self.margin),
                    y=pos[1] + self.margin + (button_size[1] + self.margin) * int(index / self.max_row),
                    w=button_size[0],
                    h=button_size[1],
                    callbacks=[self.set_image],
                    image=image,
                    callback_var=name,
                    border_w=2
                    )
                )
        self.buttons.add(
            Button(
                x=pos[0] + self.margin + (self.max_row-1) * (button_size[0] + self.margin),
                y=pos[1] + self.margin + (button_size[1] + self.margin) * int(len(self.icon_names)/self.max_row),
                w=button_size[0],
                h=button_size[1],
                callbacks=[self.deactivate],
                image=self.asset_handler.img("none.PNG", button_size),
                border_w=2
                )
            )


    def deactivate(self):
        self.selected = False

    def randomize_image(self):
        icon_name = self.icon_names[random.randint(0, len(self.icon_names) - 1)]
        options = config.load_options()
        options["icon_name"] = icon_name
        config.write_options(options)
        self.image = self.asset_handler.img(
            f"animal_icons/{icon_name}.PNG", (self.rect[2], self.rect[3]))

    def set_image(self, image_name):
        self.image = self.asset_handler.img(f"animal_icons/{image_name}.PNG", (self.rect[2], self.rect[3]))
        self.selected = False
        options = config.load_options()
        options["icon_name"] = image_name
        config.write_options(options)

    def update(self, dt):
        pass

    def handle_event(self, e):
        if self.selected:
            for button in self.buttons:
                button.handle_event(e)
            return

        if e.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.hover = True
            else:
                self.hover = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.selected = True
                self.hover = False

    def draw(self, screen):
        pygame.draw.circle(screen, config.BLACK, (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
                           self.rect[2] / 2 - 10)
        if self.hover:
            pygame.draw.circle(screen, config.WHITE,
                               (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
                               self.rect[2] / 2 - 10, width=3)
        else:
            pygame.draw.circle(screen, config.WHITE_TRANSPARENT, (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
                               self.rect[2] / 2 - 10, width=3)
        screen.blit(self.image, (self.rect[0], self.rect[1]))

        if self.selected:
            pygame.draw.rect(screen, config.BLACK,
                             (self.rect[0], self.rect[1], self.button_window_width, self.button_window_height))
            pygame.draw.rect(screen, config.WHITE,
                             (self.rect[0], self.rect[1], self.button_window_width, self.button_window_height),
                             width=3)
            for button in self.buttons:
                button.draw(screen)
