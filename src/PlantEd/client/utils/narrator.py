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
        pos: tuple[int, int],
        voiceline: Sound,
        written_lines: Surface,
        queue_voicebox: callable,
        condition: callable = None,
        condition_time: callable = None,
        condition_parameter_time: int = None,
    ):
        self.pos = pos
        self.voiceline = voiceline
        self.written_lines = written_lines
        self.queue_voicebox = queue_voicebox
        self.condition_time = condition_time
        self.condition_parameter_time = condition_parameter_time
        self.condition = condition
        self.played = False

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
        delta_x = self.written_lines.get_width() * 0.9 * (1 - self.hide_timer)
        self.x = 10 - delta_x
        if not self.played:
            if self.handle_conditions():
                self.queue_voicebox(self)
                self.played = True

    def handle_conditions(self) -> bool:
        play = True
        if self.condition is not None:
            if not self.condition():
                play = False
        if self.condition_time is not None:
            if self.condition_parameter_time is not None:
                if not self.condition_time(self.condition_parameter_time):
                    play = False
        return play

    def handle_event(self, e: pygame.event):
        if e.type == END_LINE:
            self.hide = True
        if e.type == pygame.MOUSEMOTION:
            if pygame.Rect(
                self.x,
                self.pos[1] - self.written_lines.get_height(),
                self.written_lines.get_width(),
                self.written_lines.get_height(),
            ).collidepoint(pygame.mouse.get_pos()):
                self.hover = True
            else:
                self.hover = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(
                self.x,
                self.pos[1] - self.written_lines.get_height(),
                self.written_lines.get_width(),
                self.written_lines.get_height(),
            ).collidepoint(pygame.mouse.get_pos()):
                self.toggle_hide()

    def draw(self, screen):
        if self.hover:
            pygame.draw.rect(
                screen,
                config.WHITE,
                (
                    self.x,
                    self.pos[1] - self.written_lines.get_height(),
                    self.written_lines.get_width(),
                    self.written_lines.get_height(),
                ),
                width=3,
            )
        screen.blit(
            self.written_lines, (self.x, self.pos[1] - self.written_lines.get_height())
        )

    def toggle_hide(self):
        # 850 to the left
        self.hide = not self.hide


class Narrator:
    def __init__(
        self,
        pos: tuple[int, int],
        environment: Environment,
        plant: Plant,
        img_size: tuple[int, int] = (100, 100),
        width: int = 100,
        font=None,
    ):
        self.pos = pos
        self.img_size = img_size
        self.width = width
        self.margin = 10
        self.font = font
        self.environment: Environment = environment
        self.plant: Plant = plant
        self.asset_handler: AssetHandler = AssetHandler.instance()
        if self.font is None:
            self.font = self.asset_handler.FONT_24
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
        self.used_fluxes = None
        self.low_growth_counter = 0

    def make_voiceboxes(self) -> list[Voicebox]:

        voiceboxes: list[Voicebox] = []

        # make timed boxes
        index_lines_to_play = [0, 4, 5, 20, 30]

        talking_times = [0, 5, 6, 10, 15, 20, 30]

        all_written_lines = config.load_tooltipps()

        for i in range(len(index_lines_to_play)):
            surface_written_lines = None
            for lines in all_written_lines:

                tag = int(lines["tag"]) if lines["tag"].isdigit() else lines["tag"]
                if tag == index_lines_to_play[i]:
                    written_lines = lines["lines"]
                    surface_written_lines = self.build_written_lines(written_lines)

            voiceboxes.append(
                Voicebox(
                    pos=self.pos,
                    voiceline=self.asset_handler.sfx(
                        f"attenborough/{index_lines_to_play[i]}.mp3"
                    ),
                    written_lines=surface_written_lines,
                    queue_voicebox=self.queue_voicebox,
                    condition_time=self.check_date,
                    condition_parameter_time=talking_times[i],
                )
            )

        # make seed box
        surface_written_lines = None
        for lines in all_written_lines:
            if lines["tag"] == "seed":
                written_lines_seed = lines["lines"]
                surface_written_lines_seed = self.build_written_lines(
                    written_lines_seed
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/seed.mp3"),
                        written_lines=surface_written_lines_seed,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_seed_bought,
                    )
                )
            if lines["tag"] == "branch":
                written_lines_branch = lines["lines"]
                surface_written_lines_branch = self.build_written_lines(
                    written_lines_branch
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/branch.mp3"),
                        written_lines=surface_written_lines_branch,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_branch_bought,
                    )
                )
            if lines["tag"] == "leaf":
                written_lines_leaf = lines["lines"]
                surface_written_lines_leaf = self.build_written_lines(
                    written_lines_leaf
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/leaf.mp3"),
                        written_lines=surface_written_lines_leaf,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_leaf_bought,
                    )
                )
            if lines["tag"] == "root":
                written_lines_root = lines["lines"]
                surface_written_lines_root = self.build_written_lines(
                    written_lines_root
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/root.mp3"),
                        written_lines=surface_written_lines_root,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_root_bought,
                    )
                )

            if lines["tag"] == "water":
                written_lines_root = lines["lines"]
                surface_written_lines_root = self.build_written_lines(
                    written_lines_root
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/water.mp3"),
                        written_lines=surface_written_lines_root,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_water_pool_empty,
                    )
                )

            if lines["tag"] == "nutrient":
                written_lines_root = lines["lines"]
                surface_written_lines_root = self.build_written_lines(
                    written_lines_root
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/nutrient.mp3"),
                        written_lines=surface_written_lines_root,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_nitrate_intake_zero,
                    )
                )

            if lines["tag"] == "warning":
                written_lines_root = lines["lines"]
                surface_written_lines_root = self.build_written_lines(
                    written_lines_root
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/warning.mp3"),
                        written_lines=surface_written_lines_root,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_no_growth,
                    )
                )

            if lines["tag"] == "bloom":
                written_lines_root = lines["lines"]
                surface_written_lines_root = self.build_written_lines(
                    written_lines_root
                )
                voiceboxes.append(
                    Voicebox(
                        pos=self.pos,
                        voiceline=self.asset_handler.sfx("attenborough/bloom.mp3"),
                        written_lines=surface_written_lines_root,
                        queue_voicebox=self.queue_voicebox,
                        condition=self.check_bloom,
                    )
                )

        return voiceboxes

    def check_seed_bought(self) -> bool:
        if len(self.plant.organs[3].flowers) > 0:
            return True
        else:
            return False

    def check_leaf_bought(self) -> bool:
        if len(self.plant.organs[0].leaves) > 1:
            return True
        else:
            return False

    def check_branch_bought(self) -> bool:
        if len(self.plant.organs[1].curve.branches) > 1:
            return True
        else:
            return False

    def check_root_bought(self) -> bool:
        if self.plant.organs[2].root_drawer is not None:
            if len(self.plant.organs[2].root_drawer.roots) > 1:
                return True
        return False

    def check_water_pool_empty(self) -> bool:
        if self.plant.water_pool <= 0:
            return True
        else:
            return False

    def check_nitrate_intake_zero(self) -> bool:
        if self.used_fluxes is not None:
            if self.used_fluxes["nitrate_available"] <= 0:
                return True
        return False

    def check_no_growth(self) -> bool:
        if self.used_fluxes is not None:
            if (
                self.used_fluxes["starch_in_used"] <= 0
                and self.used_fluxes["photon_used"] <= 0
            ):
                self.low_growth_counter += 1
                return False
        return False

    def check_bloom(self) -> bool:
        if len(self.plant.organs[3].flowers) > 0:
            for flower in self.plant.organs[3].flowers:
                if flower["mass"] >= flower["maximum_mass"]:
                    return True
        return False

    def check_date(self, condition_day: int) -> bool:
        day, hour, minute = self.environment.get_day_time()
        if condition_day <= day and hour > 1:
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

    def pause(self):
        self.channel.pause()

    def unpause(self):
        self.channel.unpause()

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

        rect_height = max(self.img_size[1], len(lines) * 22) + 20
        rect_width = self.width

        box_surface: Surface = Surface((rect_width, rect_height), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 150))

        box_surface.blit(
            self.asset_handler.img("professor.PNG", self.img_size), (10, 10)
        )
        font_height = self.font.get_height()
        for i, line in enumerate(lines):
            box_surface.blit(
                self.font.render(line, True, config.WHITE),
                (
                    self.img_size[0] + self.img_size[0] / 5,
                    self.margin + i * font_height,
                ),
            )

        return box_surface

    def draw(self, screen: Surface):
        if self.active_voicebox is not None:
            self.active_voicebox.draw(screen)
