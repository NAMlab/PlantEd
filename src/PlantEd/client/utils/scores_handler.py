import pygame

from PlantEd import config
from PlantEd.data.assets import AssetHandler


class PlayerScore:
    def __init__(
            self,
            name,
            image,
            font: pygame.font,
            score,
            date,
            width,
            ):
        self.name = name
        self.image = image
        self.font: pygame.font = font
        self.score = score
        self.date = date
        self.width = width
        self.hover = False
        self.selected = False
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.surface = self.init_layout()


    def init_layout(self) -> pygame.Surface:
        name_label = self.font.render(f"{self.name}", True, config.WHITE)
        score_label = self.font.render(f"{self.score:.2f} gram", True, config.WHITE)
        date_label = self.font.render(f"{self.date}", True, config.WHITE)

        height = self.image.get_height()
        surface = pygame.Surface((self.width, height))
        center_height = height/2
        center_width = self.width/2
        surface.blit(self.image, (0, 0))
        surface.blit(name_label, (self.image.get_width() + 10, center_height - name_label.get_height()/2))
        surface.blit(score_label, (self.width - date_label.get_width() - 100 - score_label.get_width(), center_height - score_label.get_height()/2))
        surface.blit(date_label, (self.width - date_label.get_width() - 10, center_height - date_label.get_height()/2))
        self.rect = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
        return surface

    def update_pos(self, pos):
        self.rect = pygame.Rect(pos[0], pos[1], self.rect[2], self.rect[3])

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.hover = True
            else:
                self.hover = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            print(mouse_pos)
            print(self.rect)
            if self.rect.collidepoint(mouse_pos):
                self.selected = True
                self.hover = False
            else:
                self.selected = False

    def draw(self, screen):
        print(self.selected, self.hover)

        screen.blit(self.surface, (self.rect[0], self.rect[1]))
        if self.hover:
            pygame.draw.rect(screen, config.WHITE_TRANSPARENT, self.rect, width=3)
        if self.selected:
            pygame.draw.rect(screen, config.WHITE, self.rect, width=3)


class ScoreList:
    def __init__(
            self,
            pos,
            width,
            margin=10
            ):
        self.player_scores = []
        self.asset_handler: AssetHandler = AssetHandler.instance()
        self.pos = pos
        self.width = width
        self.margin = margin

        self.rect = pygame.Rect(0, 0, 0, 0)
        self.init_layout()

    def add_new_score(self, name, icon_name, score, date):
        image = self.asset_handler.img(f"animal_icons/{icon_name}.PNG", (60, 60))
        self.player_scores.append(
            PlayerScore(
                name=name,
                image=image,
                font=self.asset_handler.BIGGER_FONT,
                score=score,
                date=date,
                width=self.width
                )
            )
        self.init_layout()

    def init_layout(self):
        height = self.margin
        for score in self.player_scores:
            surface = score.init_layout()
            height += surface.get_height() + self.margin
            score.update_pos((self.pos[0], self.pos[1] + height))
        self.rect = pygame.Rect(self.pos[0], self.pos[1],self.width, height)

    def handle_event(self, e):
        for score in self.player_scores:
            score.handle_event(e)

    def draw(self, screen):
        score_height = self.rect[2]/max(len(self.player_scores), 1)

        for i, score in enumerate(self.player_scores):
            score.draw(screen)

