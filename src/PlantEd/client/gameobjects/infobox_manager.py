import pygame

from PlantEd import config
from PlantEd.client.utils.button import Button
from PlantEd.data.assets import AssetHandler


class InfoBoxManager:
    def __init__(self, boxes=[]):
        self.boxes: list[InfoBox] = boxes
        self.active_box = 0
        self.visible = True
        self.asset_handler = AssetHandler.instance()

        self.show_button = Button(
            x=260,
            y=config.SCREEN_HEIGHT - 50,
            w=64,
            h=32,
            callbacks=[self.show],
            text="Help",
            font=self.asset_handler.FONT,
            border_w=2
        )

    def to_dict(self) -> dict:
        infoboxes = {
            "boxes": [box.to_dict() for box in self.boxes]
        }
        return infoboxes

    def from_dict(self, boxes: dict):
        for box in boxes["boxes"]:
            self.create_infobox(
                pos=box["pos"],
                window_width=box["window_width"],
                window_height=box["window_height"],
                margin=box["margin"],
                lines=box["lines"]
            )

    def create_infobox(
            self,
            pos=(0, 0),
            window_width=250,
            window_height=120,
            margin=10,
            lines=None
    ):
        self.boxes.append(InfoBox(
            next_infobox=self.next_infobox,
            previous_infobox=self.previous_infobox,
            hide=self.hide,
            pos=pos,
            window_width=window_width,
            window_height=window_height,
            margin=margin,
            lines=lines,
        ))

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    def next_infobox(self):
        self.active_box += 1
        if self.active_box >= len(self.boxes):
            self.active_box = 0
            self.visible = False

    def previous_infobox(self):
        self.active_box -= 1
        if self.active_box < 0:
            self.active_box = len(self.boxes)-1

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_q:
            config.write_infobox(self.to_dict())
        if len(self.boxes) > 0:
            self.boxes[self.active_box].handle_event(e)
        self.show_button.handle_event(e)

    def draw(self, screen):
        self.show_button.draw(screen)
        if self.visible:
            if len(self.boxes) > 0:
                self.boxes[self.active_box].draw(screen)


class InfoBox:
    def __init__(
            self,
            next_infobox,
            previous_infobox,
            hide,
            pos,
            window_width,
            window_height,
            margin,
            lines):
        self.asset_handler = AssetHandler.instance()
        self.pos: tuple[float, float] = pos
        self.window_width: int = window_width
        self.window_height: int = window_height
        self.margin = margin
        self.lines_text = lines
        self.lines: list[pygame.Surface] = [self.asset_handler.FONT.render(line, True, config.BLACK) for line in lines]
        self.buttons = []
        self.button_height = 30
        self.button_width = 60

        if self.lines is not None:
            line_height = len(self.lines)*self.lines[0].get_height()
        else:
            line_height = 0

        self.button_previous_infobox = Button(
            x=self.pos[0] + self.window_width/2 - (self.button_width/2)*3 - self.margin,
            y=self.pos[1]+self.window_height+line_height+self.margin,
            w=self.button_width,
            h=self.button_height,
            text="back",
            font=self.asset_handler.FONT,
            callbacks=[previous_infobox],
            border_w=2
        )
        self.button_hide = Button(
            x=self.pos[0] + self.window_width/2 - self.button_width/2,
            y=self.pos[1] + self.window_height + line_height+self.margin,
            w=self.button_width,
            h=self.button_height,
            text="hide",
            font=self.asset_handler.FONT,
            callbacks=[hide],
            border_w=2
        )
        self.button_next_infobox = Button(
            x=self.pos[0] + self.window_width/2 + self.button_width/2 + self.margin,
            y=self.pos[1] + self.window_height + line_height + self.margin,
            w=self.button_width,
            h=self.button_height,
            text="next",
            font=self.asset_handler.FONT,
            callbacks=[next_infobox],
            border_w=2
        )
        self.buttons.append(self.button_next_infobox)
        self.buttons.append(self.button_previous_infobox)
        self.buttons.append(self.button_hide)

    def to_dict(self) -> dict:
        return {
            "pos": self.pos,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "margin": self.margin,
            "lines": self.lines_text
        }

    def handle_event(self, e):
        for button in self.buttons:
            button.handle_event(e)

    def draw(self, screen):
        # make window rect based on window sizes
        if self.lines is not None:
            line_height = len(self.lines)*self.lines[0].get_height()
        else:
            line_height = 0

        pygame.draw.rect(
            surface=screen,
            color=config.WHITE_TRANSPARENT_LESS,
            rect=(self.pos[0], self.pos[1], self.window_width, self.window_height),
            width=self.margin
        )
        pygame.draw.rect(
            surface=screen,
            color=config.WHITE,
            rect=(self.pos[0]+self.margin, self.pos[1]+self.margin, self.window_width-self.margin*2, self.window_height-self.margin*2),
            width=2,
            border_radius=3
        )
        pygame.draw.rect(
            surface=screen,
            color=config.WHITE_TRANSPARENT_LESS,
            rect=(self.pos[0], self.pos[1]+self.window_height, self.window_width, self.button_height+self.margin*2+line_height),
        )
        pygame.draw.rect(
            surface=screen,
            color=config.WHITE,
            rect=(self.pos[0], self.pos[1], self.window_width, self.window_height+self.button_height+self.margin*2+line_height),
            width=2,
            border_radius=3
        )
        for index, line in enumerate(self.lines):
            screen.blit(line, (self.pos[0] + self.window_width/2 - line.get_width()/2, self.pos[1] + self.window_height + index * line.get_height()))

        for button in self.buttons:
            button.draw(screen)
        # make rect below based on lines and standard buttons
        '''pygame.draw.rect(
            surface=screen,
            color=config.WHITE_TRANSPARENT,
            rect=(self.pos[0],self.pos[1])
        )'''