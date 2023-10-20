import pygame
from PlantEd import config
from PlantEd.data.assets import AssetHandler

END_LINE = pygame.USEREVENT + 2


# holds all voicelines
# buffers lines, plays lines
# provide trigger functions to check
class Narrator:
    def __init__(self, environment):
        self.environment = environment
        self.asset_handler = AssetHandler.instance()
        self.active = True
        self.queue = []
        self.muted = False
        self.channel = pygame.mixer.Channel(0)
        self.channel.set_endevent(END_LINE)
        options = config.load_options()
        self.volume = options["narator_volume"]
        self.channel.set_volume(self.volume)
        self.written_lines = Written_Lines(self.asset_handler.img("sir_david.jpeg", (100, 100)), self.asset_handler.FONT)

        self.lines = [
            self.asset_handler.sfx("attenborough/{}.mp3".format(i)) for i in range(12)
        ]
        self.voicelines = []
        self.talking_times = [0, 2, 4, 6, 8, 11, 14, 17, 20, 23, 27, 31]
        for i in range(len(self.lines)):
            self.voicelines.append(
                VoiceLine(
                    self.lines[i],
                    self.queue_voiceline,
                    self.written_lines.queue_written_lines,
                    self.check_date,
                    self.talking_times[i],
                    self.written_lines.get_line(i),
                )
            )
        # surrender.mp3
        # warning.mp3
        # end.mp3
        # end_3_days.mp3
        # seeds.mp3
        # soil.mp3
        # self.voicelines.append(VoiceLine())

    def check_plant_has_leaf(self):
        if len(self.plant.organs[0].leaves) > 0:
            return True
        else:
            return False

    def check_date(self, condition_day):
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

    def update(self, dt):
        if len(self.queue) > 0:
            if not self.channel.get_busy():
                voiceline = self.queue.pop(0)
                self.channel.play(voiceline)
                self.written_lines.pop_queue()
        for line in self.voicelines:
            line.update(dt)
        self.written_lines.upddate(dt)

    def handle_event(self, e):
        self.written_lines.handle_event(e)

    def queue_voiceline(self, voiceline):
        self.queue.append(voiceline)

    def stop(self):
        self.channel.stop()

    def set_volume(self, volume=None):
        if not volume:
            volume = self.volume
        self.channel.set_volume(volume)

    def draw(self, screen):
        self.written_lines.draw(screen)


class VoiceLine:
    def __init__(
        self,
        voiceline,
        queue_voiceline,
        queue_written_lines,
        condition,
        condition_parameter,
        written_line,
    ):
        self.voiceline = voiceline
        self.queue_voiceline = queue_voiceline
        self.queue_written_lines = queue_written_lines
        self.condition = condition
        self.condition_parameter = condition_parameter
        self.written_line = written_line
        self.played = False

    def update(self, dt):
        if not self.played:
            if self.condition(self.condition_parameter):
                self.queue_voiceline(self.voiceline)
                self.queue_written_lines(self.written_line)
                self.played = True


class Written_Lines:
    def __init__(self, david_image, font):
        self.sir_david = david_image
        self.hide = False
        self.hide_timer = 1
        self.x = 10
        self.y = 1000
        self.hover = False
        self.width = 800
        self.height = 500
        self.font = font
        all_labels = config.load_tooltipps()
        self.labels = self.make_labels(all_labels[0])
        self.rect_heigth = 0
        self.queue = []
        self.lines = []
        self.s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def upddate(self, dt):
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

    def handle_event(self, e):
        if e.type == END_LINE:
            self.hide = True
        if e.type == pygame.MOUSEMOTION:
            if pygame.Rect(
                self.x, self.y - self.rect_heigth, self.width, self.rect_heigth
            ).collidepoint(pygame.mouse.get_pos()):
                self.hover = True
            else:
                self.hover = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            if pygame.Rect(
                self.x, self.y - self.rect_heigth, self.width, self.rect_heigth
            ).collidepoint(pygame.mouse.get_pos()):
                self.toggle_hide()

    def get_line(self, index):
        return self.labels[index]

    def toggle_hide(self):
        # 850 to the left
        self.hide = not self.hide

    def make_labels(self, tipps):
        labels = []
        for i in range(len(tipps)):
            lines = []
            for j in range(len(tipps[i]["lines"])):
                lines.append(
                    self.font.render(
                        tipps[i]["lines"][j], True, (255, 255, 255)
                    )
                )
            labels.append(lines)
        return labels

    def queue_written_lines(self, written_lines):
        self.queue.append(written_lines)

    def pop_queue(self):
        if len(self.queue) > 0:
            self.lines = self.queue.pop(0)
            self.rect_heigth = len(self.lines) * 20 + 20
            self.s.fill((0, 0, 0, 0))
            self.hide = False

    def draw(self, screen):
        if len(self.lines) > 0:
            pygame.draw.rect(
                self.s,
                (0, 0, 0, 150),
                (0, 0, self.width, self.rect_heigth),
                border_radius=5,
            )
            if self.hover:
                pygame.draw.rect(
                    self.s,
                    config.WHITE,
                    (0, 0, self.width, self.rect_heigth),
                    border_radius=5,
                    width=2,
                )
            self.s.blit(self.sir_david, (10, 10))
            for i in range(len(self.lines)):
                self.s.blit(self.lines[i], (120, 10 + i * 20))
            screen.blit(self.s, (self.x, self.y - self.rect_heigth))
