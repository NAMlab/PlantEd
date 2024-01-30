import pygame
from pygame import Surface
from pygame.event import Event
from pygame.mixer import Channel, Sound

from PlantEd import config
from PlantEd.client.gameobjects.plant import Plant
from PlantEd.client.weather import Environment
from PlantEd.data.assets import AssetHandler

END_LINE = pygame.USEREVENT + 2


class Voicebox:
    def __init__(
            self,
            voiceline: Sound,
            written_lines: Surface,
            queue_voicebox: callable,
            condition: callable,
            condition_parameter: int
            ):
        self.voiceline = voiceline
        self.written_lines = written_lines
        self.queue_voicebox = queue_voicebox
        self.condition = condition
        self.condition_parameter = condition_parameter
        self.played = False

        self.x = 10
        self.y = config.SCREEN_HEIGHT - 80
        self.hide = True
        self.hide_timer = 1
        self.hover = False
        self.hide_timer = 1

    def update(self, dt: float):
        if self.hide:
            if self.hide_timer - dt * 2 < 0:
                self.hide_timer = 0
            else:
                self.hide_timer -= dt * 2
        else:
            if self.hide_timer + dt * 2 < 1:
                self.hide_timer += dt * 2
            else:
                self.hide_timer = 1
        delta_x = 750 * (1 - self.hide_timer)
        self.x = 10 - delta_x
        if not self.played:
            if self.condition(self.condition_parameter):
                self.queue_voicebox(self)
                self.played = True

    def handle_event(self, e: pygame.event):
        if e.type == END_LINE:
            self.hide = True
        if e.type == pygame.MOUSEMOTION:
            if pygame.Rect(
                    self.x, self.y - self.written_lines.get_height(),
                    self.written_lines.get_width(), self.written_lines.get_height()
                    ).collidepoint(pygame.mouse.get_pos()):
                self.hover = True
            else:
                self.hover = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(
                    self.x, self.y - self.written_lines.get_height(),
                    self.written_lines.get_width(), self.written_lines.get_height()
                    ).collidepoint(pygame.mouse.get_pos()):
                self.toggle_hide()

    def draw(self, screen):
        if self.hover:
            pygame.draw.rect(
                screen,
                config.WHITE,
                (self.x, self.y - self.written_lines.get_height(),
                 self.written_lines.get_width(), self.written_lines.get_height()),
                width=3
                )
        screen.blit(
            self.written_lines,
            (self.x, self.y - self.written_lines.get_height()))

    def toggle_hide(self):
        # 850 to the left
        self.hide = not self.hide


class Narrator:
    def __init__(self, environment: Environment, plant: Plant):
        self.environment: Environment = environment
        self.plant: Plant = plant
        self.asset_handler: AssetHandler = AssetHandler.instance()
        self.active: bool = True
        self.queue: list[Voicebox] = []
        self.muted: bool = False
        self.channel: Channel = pygame.mixer.Channel(0)
        self.channel.set_endevent(END_LINE)
        options = config.load_options()
        self.volume: float = options["narator_volume"]
        self.channel.set_volume(self.volume)

        self.voiceboxes: list[Voicebox] = self.make_voiceboxes()
        self.active_voicebox: Voicebox = None

    def make_voiceboxes(self) -> list[Voicebox]:

        voiceboxes: list[Voicebox] = []

        # make timed boxes
        index_lines_to_play = [0, 4, 5, 7, 9, 11, 12]

        talking_times = [0, 5, 6, 10, 15, 20, 30]

        all_written_lines = config.load_tooltipps()

        for i in range(len(index_lines_to_play)):
            surface_written_lines = None
            for lines in all_written_lines:

                tag = int(lines["tag"]) if lines["tag"].isdigit() else lines["tag"]
                if tag == index_lines_to_play[i]:
                    written_lines = lines["lines"]
                    surface_written_lines = self.build_written_lines(written_lines)

            voiceboxes.append(Voicebox(
                voiceline=self.asset_handler.sfx(f"attenborough/{index_lines_to_play[i]}.mp3"),
                written_lines=surface_written_lines,
                queue_voicebox=self.queue_voicebox,
                condition=self.check_date,
                condition_parameter=talking_times[i]
                )
                )

        # make seed box
        surface_written_lines = None
        for lines in all_written_lines:
            if lines["tag"] == "seeds":
                written_lines = lines["lines"]
                surface_written_lines = self.build_written_lines(written_lines)

        voiceboxes.append(Voicebox(
            voiceline=self.asset_handler.sfx("attenborough/seeds.mp3"),
            written_lines=surface_written_lines,
            queue_voicebox=self.queue_voicebox,
            condition=self.check_seed_bought,
            condition_parameter=1
            )
            )

        return voiceboxes

    def check_seed_bought(self, useless_param):
        if len(self.plant.organs[3].flowers) > 0:
            return True
        else:
            return False

    def check_leaf_bought(self, useless_param):
        if len(self.plant.organs[0].leaves) > 1:
            return True
        else:
            return False

    def check_branch_bought(self, useless_param):
        if len(self.plant.organs[1].curve.branches) > 1:
            return True
        else:
            return False

    def check_root_bought(self, useless_param):
        if self.plant.organs[2].ls is not None:
            if len(self.plant.organs[2].ls.first_letters) > 1:
                return True
        return False

    def check_date(self, condition_day: int) -> bool:
        day, hour, minute = self.environment.get_day_time()
        if condition_day <= day and hour > 8:
            return True
        else:
            return False

    def toggle_mute(self):
        if self.muted:
            self.unmute()
        else:
            self.mute()

    def mute(self):
        self.muted = True
        self.channel.set_volume(0)

    def unmute(self):
        self.muted = False
        self.channel.set_volume(self.volume)

    def reload_options(self):
        options = config.load_options()
        self.volume = options["narator_volume"]
        if not self.muted:
            self.channel.set_volume(self.volume)

    def update(self, dt: float):
        if len(self.queue) > 0:
            if not self.channel.get_busy():
                self.active_voicebox = self.queue.pop(0)
                self.active_voicebox.hide = False
                self.channel.play(self.active_voicebox.voiceline)
        for voicebox in self.voiceboxes:
            voicebox.update(dt)

    def handle_event(self, e: Event):
        if self.active_voicebox is not None:
            self.active_voicebox.handle_event(e)

    def queue_voicebox(self, voicebox: Voicebox):
        self.queue.append(voicebox)

    def stop(self):
        self.channel.stop()

    def set_volume(self, volume: float = None):
        if not volume:
            volume = self.volume
        self.channel.set_volume(volume)

    def build_written_lines(self, lines: list[str]) -> Surface:

        rect_height = len(lines) * 22 + 20
        rect_width = 800

        box_surface: Surface = Surface((rect_width, rect_height), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 150))

        box_surface.blit(self.asset_handler.img("sir_david.jpeg", (100, 100)), (10, 10))
        for i, line in enumerate(lines):
            box_surface.blit(self.asset_handler.FONT.render(line, True, config.WHITE), (120, 10 + i * 22))

        return box_surface

    def draw(self, screen: Surface):
        if self.active_voicebox is not None:
            self.active_voicebox.draw(screen)
