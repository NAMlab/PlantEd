import random

import pygame

from PlantEd import config
from PlantEd.client.utils.button import Button, Textbox
from PlantEd.data.assets import AssetHandler
from PlantEd.data.sound_control import SoundControl


class IconHandler:
    def __init__(
        self,
        pos: tuple,
        sound_control: SoundControl,
        image=None,
        image_size=(150, 150),
        button_size=(80, 80),
        text_box_size=(300, 40),
        margin=10,
        max_row=5,
    ):
        self.asset_handler = AssetHandler.instance()
        self.sound_control = sound_control
        self.hover = False
        self.selected = False
        self.rect = pygame.Rect(pos[0], pos[1], image_size[0], image_size[1])
        self.button_size = button_size
        self.margin = margin
        self.max_row = max_row
        self.options = config.load_options()
        self.buttons = pygame.sprite.Group()
        self.icon_names = [
            "bird",
            "bear",
            "bunny",
            "cat",
            "chick",
            "cow",
            "dear",
            "elephant",
            "fox",
            "giraffe",
            "hippo",
            "hog",
            "horse",
            "koala",
            "monkey",
            "mouse",
            "owl",
            "panda",
            "pavian",
            "penguin",
            "pig",
            "racoon",
            "sheep",
            "tiger",
        ]
        icon_name = self.options.get("icon_name")
        if icon_name is None:
            self.randomize_image()
        else:
            self.image = self.asset_handler.img(
                f"animal_icons/{icon_name}.PNG", image_size
            )

        self.button_window_height = self.margin + int(
            (len(self.icon_names) + 1) / self.max_row
        ) * (self.margin + button_size[1])
        self.button_window_width = self.margin + max_row * (
            self.margin + button_size[0]
        )

        for index, name in enumerate(self.icon_names):
            image = self.asset_handler.img(f"animal_icons/{name}.PNG", button_size)
            self.buttons.add(
                Button(
                    x=pos[0]
                    + self.margin
                    + index % self.max_row * (button_size[0] + self.margin),
                    y=pos[1]
                    + self.margin
                    + (button_size[1] + self.margin) * int(index / self.max_row),
                    w=button_size[0],
                    h=button_size[1],
                    callbacks=[self.set_image],
                    image=image,
                    callback_var=name,
                    border_w=2,
                )
            )
        self.buttons.add(
            Button(
                x=pos[0]
                + self.margin
                + (self.max_row - 1) * (button_size[0] + self.margin),
                y=pos[1]
                + self.margin
                + (button_size[1] + self.margin)
                * int(len(self.icon_names) / self.max_row),
                w=button_size[0],
                h=button_size[1],
                callbacks=[self.deactivate],
                image=self.asset_handler.img("none.PNG", button_size),
                border_w=2,
            )
        )

        self.textbox = Textbox(
            x=self.rect[0] + self.rect[2],
            y=self.rect[1] + self.rect[3] / 2 - text_box_size[1] / 2,
            w=text_box_size[0],
            h=text_box_size[1],
            font=self.asset_handler.FONT_36,
            text=self.options.get("name") if self.options.get("name") else "Player",
            background_color=config.LIGHT_GRAY,
            textcolor=config.WHITE,
            highlight_color=config.WHITE,
        )

        # random button
        self.randomize = Button(
            x=self.rect[0] + self.rect[2] + text_box_size[0] + margin,
            y=self.rect[1] + self.rect[3] / 2 - text_box_size[1] / 2,
            w=text_box_size[1],
            h=text_box_size[1],
            callbacks=[self.set_random_name, self.randomize_image],
            button_color=config.LIGHT_GRAY,
            image=self.asset_handler.img("re.PNG", (40, 40)),
            border_w=2,
            play_confirm=self.sound_control.play_toggle_sfx,
        )

    def deactivate(self):
        self.selected = False

    def set_random_name(self):
        name = config.randomize_name()
        self.options["name"] = name
        config.write_options(self.options)
        self.textbox.update_text(name)

    def randomize_image(self):
        icon_name = self.icon_names[random.randint(0, len(self.icon_names) - 1)]
        options = config.load_options()
        options["icon_name"] = icon_name
        config.write_options(options)
        self.image = self.asset_handler.img(
            f"animal_icons/{icon_name}.PNG", (self.rect[2], self.rect[3])
        )

    def set_image(self, image_name):
        self.image = self.asset_handler.img(
            f"animal_icons/{image_name}.PNG", (self.rect[2], self.rect[3])
        )
        self.selected = False
        options = config.load_options()
        options["icon_name"] = image_name
        config.write_options(options)

    def update(self, dt):
        self.textbox.update(dt)

    def handle_event(self, e):
        if self.selected:
            for button in self.buttons:
                button.handle_event(e)
            return
        else:
            self.textbox.handle_event(e)
            self.randomize.handle_event(e)

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
        self.textbox.draw(screen)
        self.randomize.draw(screen)
        pygame.draw.circle(
            screen,
            config.BLACK,
            (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
            self.rect[2] / 2 - 10,
        )
        if self.hover:
            pygame.draw.circle(
                screen,
                config.WHITE,
                (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
                self.rect[2] / 2 - 10,
                width=3,
            )
        else:
            pygame.draw.circle(
                screen,
                config.WHITE_TRANSPARENT,
                (self.rect[0] + self.rect[2] / 2, self.rect[1] + self.rect[3] / 2),
                self.rect[2] / 2 - 10,
                width=3,
            )
        screen.blit(self.image, (self.rect[0], self.rect[1]))

        if self.selected:
            pygame.draw.rect(
                screen,
                config.BLACK,
                (
                    self.rect[0],
                    self.rect[1],
                    self.button_window_width,
                    self.button_window_height,
                ),
            )
            pygame.draw.rect(
                screen,
                config.WHITE,
                (
                    self.rect[0],
                    self.rect[1],
                    self.button_window_width,
                    self.button_window_height,
                ),
                width=3,
            )
            for button in self.buttons:
                button.draw(screen)
