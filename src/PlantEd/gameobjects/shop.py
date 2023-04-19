import pygame

from PlantEd import config
from PlantEd.client.client import Client
from PlantEd.data import assets
from PlantEd.gameobjects.blue_grain import Blue_grain
from PlantEd.gameobjects.root_item import Root_Item
from PlantEd.gameobjects.spraycan import Spraycan
from PlantEd.gameobjects.water_reservoir import Water_Grid
from PlantEd.gameobjects.watering_can import Watering_can
from PlantEd.utils.button import Button

"""
shop holds items and interfaces actions to consumables
holds green thumbs, checks if buyable

shopitems have action and button and cost
"""


class FloatingShop:
    def __init__(self, camera, pos=(0, 0)):
        self.camera = camera
        self.pos = pos
        self.shop_items = []
        self.margin = 16
        self.rect = pygame.Rect(
            (
                0,
                0,
                len(self.shop_items) * (64 + self.margin) + self.margin,
                64 + 2 * self.margin,
            )
        )
        self.active = False
        self.s = pygame.Surface(
            (self.margin + 3 * (self.margin + 64), 64 + self.margin * 2),
            pygame.SRCALPHA,
        )

    def activate(self, pos):
        for i in range(len(self.shop_items)):
            self.shop_items[i].set_pos(
                (self.margin + i * (64 + self.margin), self.margin)
            )
        self.active = True
        self.pos = pos
        self.rect = pygame.Rect(
            (
                0,
                0,
                len(self.shop_items) * (64 + self.margin) + self.margin,
                64 + 2 * self.margin,
            )
        )

    def deactivate(self):
        self.active = False

    def add_item(self, shop_item):
        self.shop_items.append(shop_item)
        self.shop_items[-1].shop_items = self.shop_items
        self.shop_items[-1].floating_shop = self
        self.rect = pygame.Rect(
            (
                0,
                0,
                len(self.shop_items) * (64 + self.margin) + self.margin,
                64 + 2 * self.margin,
            )
        )

    def get_rect(self):
        return pygame.Rect(
            self.pos[0], self.pos[1], self.rect[2], self.rect[3]
        )

    def handle_event(self, e: pygame.event.Event):
        if self.active:
            mouse_pos = pygame.mouse.get_pos()
            for item in self.shop_items:
                item.handle_event(e, self.pos)
            if e.type == pygame.MOUSEMOTION:
                print(self.get_rect(), mouse_pos)
                if not self.get_rect().collidepoint(mouse_pos):
                    self.active = False

    def draw(self, screen):
        if self.active:
            pygame.draw.rect(
                self.s,
                config.WHITE_TRANSPARENT,
                (0, 0, self.rect[2], self.rect[3]),
                border_radius=3,
            )
            pygame.draw.rect(
                self.s,
                config.WHITE,
                (0, 0, self.rect[2], self.rect[3]),
                width=2,
                border_radius=3,
            )
            for item in self.shop_items:
                item.draw(self.s)
            screen.blit(
                self.s, (self.pos[0], self.pos[1] - self.camera.offset_y)
            )


class FloatingShopItem:
    def __init__(self, pos, callback, image, cost, plant):
        self.pos = pos
        self.rect = pygame.Rect(
            pos[0], pos[1], image.get_width(), image.get_height()
        )
        self.callback = callback
        self.image = image
        self.cost = cost
        self.plant = plant
        self.shop_items = []
        self.floating_shop = None
        self.hover = False

    def set_pos(self, pos):
        self.pos = pos
        self.rect = pygame.Rect(
            pos[0], pos[1], self.image.get_width(), self.image.get_height()
        )

    def update(self, dt):
        pass

    def handle_event(self, e, shop_pos):
        if self.cost <= self.plant.upgrade_points:
            mouse_pos = pygame.mouse.get_pos()
            if e.type == pygame.MOUSEMOTION:
                if self.rect.collidepoint(
                    (mouse_pos[0] - shop_pos[0], mouse_pos[1] - shop_pos[1])
                ):
                    self.hover = True
                else:
                    self.hover = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(
                    (mouse_pos[0] - shop_pos[0], mouse_pos[1] - shop_pos[1])
                ):
                    self.plant.upgrade_points -= self.cost
                    self.callback()
                    self.hover = False
                    self.floating_shop.deactivate()

    def draw(self, screen):
        if self.cost <= self.plant.upgrade_points:
            screen.blit(self.image, (self.rect[0], self.rect[1]))
            if self.hover:
                pygame.draw.rect(
                    screen,
                    config.WHITE,
                    (self.rect[0], self.rect[1], self.rect[2], self.rect[3]),
                    width=2,
                )


class Shop:
    def __init__(
        self,
        rect,
        shop_items,
        client: Client,
        water_grid: Water_Grid,
        plant,
        cols=2,
        margin=10,
        post_hover_message=None,
        active=True,
    ):
        # performance improve test
        self.s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        self.shop_label = config.BIG_FONT.render("Shop", True, (0, 0, 0))
        self.current_cost_label = config.BIG_FONT.render("0", False, (0, 0, 0))

        self.rect = rect
        self.shop_items = shop_items
        self.margin = margin
        self.post_hover_message = post_hover_message
        self.client = client
        self.water_grid = water_grid
        self.plant = plant
        self.active = active
        self.green_thumbs_icon = assets.img("green_thumb.PNG", (26, 26))
        self.current_cost = 0
        self.animations = []
        self.watering_can = Watering_can((0, 0), self.water_grid)
        self.blue_grain = Blue_grain(pos=(0, 0), client=self.client)
        self.spraycan = Spraycan(pos=(0, 0), amount=3, cost=2)
        self.root_item = Root_Item(
            self.plant.organs[2].create_new_root, self.plant
        )
        self.buy_button = Button(
            self.rect[2] - self.margin * 2 - 64,
            self.rect[3] - self.margin - 64,
            64,
            64,
            [self.buy],
            config.FONT,
            "BUY",
            offset=(rect[0], rect[1]),
        )
        self.init_layout()

    def init_layout(self):
        if len(self.shop_items) <= 0:
            return
        width = self.rect[2]
        height = self.rect[3]
        img_width = self.shop_items[0].image.get_width()
        columns = int(width / (img_width + self.margin * 2))
        if columns <= 0:
            return
        rows = int(
            0.5 + len(self.shop_items) / columns
        )  # 0.5 to get single items accounted for
        for i in range(0, rows):
            for j in range(0, columns):
                x = j * (width / columns) + ((width / columns) - img_width) / 2
                y = i + 1 * self.margin + img_width * i + self.margin * i
                # looks dirty, maybe zip?
                if len(self.shop_items) > i * columns + j:
                    self.shop_items[i * columns + j].rect = pygame.Rect(
                        x, y + 50, img_width, img_width
                    )
                    self.shop_items[i * columns + j].offset = (
                        self.rect[0],
                        self.rect[1],
                    )
        # self.buy_button.x = self.rect[2] - self.margin * 2 - 64
        # self.buy_button.y = self.rect[3] - self.margin - 64

    def add_shop_item(self, shop_item):
        self.shop_items.append(shop_item)
        for item in self.shop_items:
            item.shop_items = self.shop_items
        self.init_layout()

    def add_shop_item(self, keywords):
        for keyword in keywords:
            if keyword == "watering":
                self.shop_items.append(
                    Shop_Item(
                        assets.img("watering_can_tilted.PNG", (64, 64)),
                        self.watering_can.activate,
                        post_hover_message=self.post_hover_message,
                        message="Buy a watering can to increase availability.",
                    )
                )
            elif keyword == "blue_grain":
                self.shop_items.append(
                    Shop_Item(
                        assets.img("blue_grain_0.PNG", (64, 64)),
                        self.blue_grain.activate,
                        post_hover_message=self.post_hover_message,
                        message="Blue grain increases nitrate in the ground.",
                    )
                )
            elif keyword == "spraycan":
                self.shop_items.append(
                    Shop_Item(
                        assets.img("spraycan.PNG", (64, 64)),
                        self.spraycan.activate,
                        post_hover_message=self.post_hover_message,
                        message="Spray em!",
                    )
                )
        for item in self.shop_items:
            item.shop_items = self.shop_items
        self.init_layout()

    def buy(self):
        for item in self.shop_items:
            if item.selected:
                if self.plant.upgrade_points - item.cost >= 0:
                    if item.condition is not None:
                        if not item.condition():
                            # condition not met
                            if item.condition_not_met_message is not None:
                                item.post_hover_message(
                                    item.condition_not_met_message
                                )
                            return
                    self.plant.upgrade_points -= item.cost
                    item.callback()
                    item.selected = False
                    self.update_current_cost()
                else:
                    # throw insufficient funds, maybe post hover msg
                    pass

    def update(self, dt):
        self.watering_can.update(dt)
        self.blue_grain.update(dt)
        self.spraycan.update(dt)
        self.root_item.update(dt)
        self.buy_button.update(dt)

        for item in self.shop_items:
            item.update(dt)
        for anim in self.animations:
            anim.update()

    def update_current_cost(self):
        self.current_cost = 0
        for item in self.shop_items:
            if item.selected:
                self.current_cost += item.cost
        self.current_cost_label = config.BIG_FONT.render(
            "{}".format(self.current_cost), False, (0, 0, 0)
        )

    def handle_event(self, e: pygame.event.Event):
        if not self.active:
            return
        for item in self.shop_items:
            item.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.update_current_cost()
        self.watering_can.handle_event(e)
        self.blue_grain.handle_event(e)
        self.spraycan.handle_event(e)
        self.buy_button.handle_event(e)
        self.root_item.handle_event(e)

    def draw(self, screen):
        if not self.active:
            return
        # s should only be as big as rect, for the moment its fine
        pygame.draw.rect(
            self.s,
            config.WHITE_TRANSPARENT,
            (0, 45, self.rect[2], self.rect[3] - 45),
            border_radius=3,
        )
        # pygame.draw.rect(s, (255,255,255), self.rect, int(self.margin/2))
        pygame.draw.rect(
            self.s, config.WHITE, (0, 0, self.rect[2], 40), border_radius=3
        )
        self.s.blit(self.shop_label, (10, 5))
        green_thumbs_label = config.BIG_FONT.render(
            "{}".format(self.plant.upgrade_points), True, config.BLACK
        )
        self.s.blit(
            green_thumbs_label,
            (self.rect[2] - 90 - green_thumbs_label.get_width(), 5),
        )
        self.s.blit(
            assets.img("green_thumb.PNG", (26, 26)), (self.rect[2] - 80, 6)
        )
        for item in self.shop_items:
            item.draw(self.s)
        self.buy_button.draw(self.s)

        self.s.blit(
            self.green_thumbs_icon, (70, self.rect[3] - self.margin - 50)
        )
        self.s.blit(
            self.current_cost_label, (50, self.rect[3] - self.margin - 50)
        )

        # s.blit(self.green_thumbs_icon,(self.rect[0]+self.rect[2]-self.margin*4-self.green_thumbs_icon.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-self.green_thumbs_icon.get_height()))
        # s.blit(cost, (self.rect[0]+self.rect[2]-self.margin*5-self.green_thumbs_icon.get_width()-cost.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-cost.get_height()))
        screen.blit(self.s, (self.rect[0], self.rect[1]))
        self.watering_can.draw(screen)
        self.blue_grain.draw(screen)
        self.spraycan.draw(screen)
        self.root_item.draw(screen)


class Shop_Item:
    def __init__(
        self,
        image,
        callback,
        cost=1,
        info_text=None,
        rect=(0, 0, 0, 0),
        selected_color=(255, 255, 255),
        hover_color=(128, 128, 128, 128),
        border_width=3,
        condition=None,
        condition_not_met_message=None,
        post_hover_message=None,
        message=None,
        offset=(0, 0),
    ):
        self.image = image
        self.callback = callback
        self.cost = cost
        self.info_text = info_text
        self.post_hover_message = post_hover_message
        self.message = message
        self.rect = pygame.Rect(rect[0], rect[1], rect[2], rect[3])  # ugly
        self.selected_color = selected_color
        self.hover_color = hover_color
        self.border_width = border_width
        self.hover = False
        self.selected = False
        self.condition = condition
        self.condition_not_met_message = condition_not_met_message
        self.shop_items = []
        self.offset = offset

    def update(self, dt):
        pass

    # pass event to buttons to check if bought, also handle hover
    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            pos = (e.pos[0] - self.offset[0], e.pos[1] - self.offset[1])
            self.hover = False
            if self.rect.collidepoint(pos):
                if self.post_hover_message is not None:
                    self.post_hover_message(self.message)
                if not self.selected:
                    self.hover = True

        if e.type == pygame.MOUSEBUTTONDOWN:
            pos = (e.pos[0] - self.offset[0], e.pos[1] - self.offset[1])
            if self.rect.collidepoint(pos):
                if self.selected:
                    self.selected = False
                    self.hover = True
                else:
                    for item in self.shop_items:
                        item.selected = False
                    self.selected = True

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.hover:
            pygame.draw.rect(
                screen, self.hover_color, self.rect, self.border_width
            )
        if self.selected:
            pygame.draw.rect(
                screen, self.selected_color, self.rect, self.border_width
            )
