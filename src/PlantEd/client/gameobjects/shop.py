import pygame

from PlantEd import config
from PlantEd.client.camera import Camera
from PlantEd.client.utils.grid import Grid
from PlantEd.constants import (
    NITRATE_COST,
    WATERING_CAN_COST,
    SPRAYCAN_COST,
    ROOT_COST,
    LEAF_COST,
    BRANCH_COST,
    FLOWER_COST,
)
from PlantEd.data.assets import AssetHandler
from PlantEd.data.sound_control import SoundControl
from PlantEd.client.gameobjects.blue_grain import Blue_grain
from PlantEd.client.gameobjects.root_item import Root_Item
from PlantEd.client.gameobjects.spraycan import Spraycan
from PlantEd.client.gameobjects.water_reservoir import Water_Grid
from PlantEd.client.gameobjects.watering_can import Watering_can
from PlantEd.client.utils.animation import Animation

"""
shop holds items and interfaces actions to consumables
holds green thumbs, checks if buyable
shopitems have action and button and cost
"""


class FloatingShop:
    def __init__(self, camera, pos=(0, 0)):
        self.camera = camera
        self.asset_handler = AssetHandler.instance()
        self.pos = pos
        self.shop_items = []
        self.visible_shop_items = []
        self.animations = []
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

        # Todo make dynamic and append to items or search for cost in buy
        images = Animation.generate_rising_animation(
            "-1", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )
        images = Animation.generate_rising_animation(
            "-2", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )
        images = Animation.generate_rising_animation(
            "-3", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )

    def buy(self, cost):
        self.animations[max(0, cost - 1)].start(pygame.mouse.get_pos())

    def activate(self, pos):
        self.visible_shop_items = []
        for item in self.shop_items:
            self.visible_shop_items.append(item)
        for i in range(len(self.visible_shop_items)):
            self.visible_shop_items[i].set_pos(
                (self.margin + i * (64 + self.margin), self.margin)
            )
        self.active = True
        self.pos = pos
        self.rect = pygame.Rect(
            (
                0,
                0,
                len(self.visible_shop_items) * (64 + self.margin) + self.margin,
                64 + 2 * self.margin,
            )
        )

    def update(self, dt):
        for animation in self.animations:
            animation.update(dt)

    def deactivate(self):
        self.visible_shop_items = []
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
        return pygame.Rect(self.pos[0], self.pos[1], self.rect[2], self.rect[3])

    def handle_event(self, e: pygame.event.Event):
        if self.active:
            mouse_pos = pygame.mouse.get_pos()
            for item in self.visible_shop_items:
                item.handle_event(e, self.pos)
            if e.type == pygame.MOUSEMOTION:
                if not self.get_rect().collidepoint(mouse_pos):
                    self.active = False

    def draw(self, screen):
        for animation in self.animations:
            animation.draw(screen)
        if self.active:
            self.s.fill((0, 0, 0, 0))
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
            for item in self.visible_shop_items:
                item.draw(self.s)
            screen.blit(self.s, (self.pos[0], self.pos[1] - self.camera.offset_y))


class FloatingShopItem:
    def __init__(
        self,
        pos,
        callback,
        image,
        cost,
        plant,
        tag=None,
        return_pos=False,
        play_buy_sfx=None,
    ):

        self.tag = tag
        self.pos = pos
        self.rect = pygame.Rect(pos[0], pos[1], image.get_width(), image.get_height())
        self.callback = callback
        self.image = image
        self.cost = cost
        self.plant = plant
        self.return_pos = return_pos
        self.play_buy_sfx = play_buy_sfx
        self.shop_items = []
        self.floating_shop = None
        self.hover = False
        self.asset_handler = AssetHandler.instance()

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
                    self.play_buy_sfx()
                    if self.return_pos:
                        self.callback(mouse_pos)
                    else:
                        self.callback()
                    self.hover = False
                    self.floating_shop.deactivate()
                    self.floating_shop.buy(self.cost)

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
            green_thumb_size = (16, 16)
            margin = 3
            cost_label = self.asset_handler.FONT_24.render(
                f"{self.cost}", True, config.BLACK
            )

            rect_with = cost_label.get_width() + green_thumb_size[0] + 6 * margin
            rect_height = (
                max(green_thumb_size[1], cost_label.get_height()) + 2 * margin - 4
            )
            rect_x = self.rect[0] + self.image.get_width() / 2 - rect_with / 2
            rect_y = self.rect[1] + self.image.get_height() - rect_height / 2

            pygame.draw.rect(
                screen,
                color=config.WHITE_TRANSPARENT_LESS,
                rect=(rect_x, rect_y, rect_with, rect_height),
                border_radius=2,
            )
            pygame.draw.rect(
                screen,
                color=config.WHITE,
                rect=(rect_x, rect_y, rect_with, rect_height),
                border_radius=2,
                width=2,
            )

            screen.blit(
                cost_label,
                (
                    rect_x + rect_with / 4 - cost_label.get_width() / 2,
                    rect_y + rect_height / 2 - cost_label.get_height() / 2,
                ),
            )

            pygame.draw.circle(
                screen,
                config.GREEN_DARK,
                (rect_x + rect_with * 3 / 4, rect_y + rect_height / 2),
                green_thumb_size[0] / 2,
            )


class Shop:
    def __init__(
        self,
        screen_size: tuple[int, int],
        rect,
        shop_items,
        water_grid: Water_Grid,
        nitrate_grid: Grid,
        plant,
        camera: Camera,
        cols=2,
        margin=18,
        post_hover_message=None,
        active=True,
        sound_control: SoundControl = None,
    ):
        # performance improve test
        self.screen_size = screen_size
        self.asset_handler = AssetHandler.instance()
        self.s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        self.shop_label = self.asset_handler.FONT_28.render("Shop", True, (0, 0, 0))
        self.current_cost_label = self.asset_handler.FONT_28.render(
            "0", False, (0, 0, 0)
        )

        self.rect = rect
        self.shop_items = shop_items
        self.margin = margin
        self.post_hover_message = post_hover_message
        self.water_grid = water_grid
        self.nitrate_grid = nitrate_grid
        self.plant = plant
        self.camera = camera
        self.plant.organs[1].check_refund = self.check_refund
        self.plant.organs[1].finalize_shop_transaction = self.finalize_shop_transaction
        self.plant.organs[1].leaf_cost = LEAF_COST
        self.plant.organs[1].branch_cost = BRANCH_COST
        self.plant.organs[1].flower_cost = FLOWER_COST
        self.active = active
        self.animations = []
        self.sound_control = sound_control
        self.asset_handler = AssetHandler.instance()
        self.green_thumbs_icon = self.asset_handler.img("green_thumb.PNG", (26, 26))
        self.current_cost = 0
        self.watering_can = Watering_can(
            pos=(0, 0),
            image_active=self.asset_handler.img("watering_can_tilted.PNG", (182, 148)),
            image_inactive=self.asset_handler.img("watering_can.PNG", (214, 147)),
            water_grid=self.water_grid,
            play_sound=self.sound_control.play_watering_can_sfx,
            stop_sound=self.sound_control.stop_watering_can_sfx,
            check_refund=self.check_refund,
            cost=WATERING_CAN_COST,
            finalize_shop_transaction=self.finalize_shop_transaction,
        )
        self.blue_grain = Blue_grain(
            screen_size=self.screen_size,
            pos=(0, 0),
            play_sound=self.sound_control.play_nitrogen_sfx,
            nitrate_grid=self.nitrate_grid,
            check_refund=self.check_refund,
            cost=NITRATE_COST,
            finalize_shop_transaction=self.finalize_shop_transaction,
        )
        self.spraycan = Spraycan(
            pos=(0, 0),
            amount=3,
            image_active=self.asset_handler.img("spraycan_active.PNG", (128, 128)),
            image_inactive=self.asset_handler.img("spraycan.PNG", (128, 128)),
            camera=self.camera,
            play_sound=self.sound_control.play_spraycan_sfx,
            check_refund=self.check_refund,
            cost=SPRAYCAN_COST,
            finalize_shop_transaction=self.finalize_shop_transaction,
        )
        self.root_item = Root_Item(
            screen_size=self.screen_size,
            callback=self.plant.organs[2].create_new_root,
            plant=self.plant,
            check_refund=self.check_refund,
            cost=ROOT_COST,
            finalize_shop_transaction=self.finalize_shop_transaction,
        )

        self.init_layout()

        images = Animation.generate_rising_animation(
            "-0", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )
        images = Animation.generate_rising_animation(
            "-1", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )
        images = Animation.generate_rising_animation(
            "-2", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )
        images = Animation.generate_rising_animation(
            "-3", self.asset_handler.FONT_36, config.RED
        )
        self.animations.append(
            Animation(
                images=images, duration=0.2, pos=(500, 500), running=False, once=True
            )
        )

        self.refund_available = False
        self.refund_image = pygame.Surface((self.rect[2], 50), pygame.SRCALPHA)
        self.refund_image.fill((0, 0, 0, 0))
        pygame.draw.rect(
            self.refund_image,
            config.WHITE_TRANSPARENT,
            (0, 0, self.rect[2], 50),
            border_radius=3,
        )
        pygame.draw.rect(
            self.refund_image,
            config.WHITE,
            (0, 0, self.rect[2], 50),
            border_radius=3,
            width=3,
        )
        refund_label = self.asset_handler.FONT_36.render("Refund", True, config.BLACK)
        self.refund_image.blit(
            refund_label,
            (
                self.refund_image.get_width() / 2 - refund_label.get_width() / 2,
                self.refund_image.get_height() / 2 - refund_label.get_height() / 2,
            ),
        )

    def init_layout(self):
        if len(self.shop_items) <= 0:
            return
        width = self.rect[2]
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

    def add_shop_item(self, keywords):
        for keyword in keywords:
            if keyword == "watering":
                self.shop_items.append(
                    Shop_Item(
                        self.asset_handler.img("watering_can_tilted.PNG", (64, 64)),
                        self.watering_can.activate,
                        buy=self.buy,
                        post_hover_message=self.post_hover_message,
                        message="Buy a watering can to increase availability.",
                        play_selected=self.sound_control.play_select_sfx,
                        cost=WATERING_CAN_COST,
                        cost_label=self.asset_handler.FONT_24.render(
                            f"{WATERING_CAN_COST}", True, config.BLACK
                        ),
                    )
                )
            elif keyword == "blue_grain":
                self.shop_items.append(
                    Shop_Item(
                        self.asset_handler.img("blue_grain_0.PNG", (64, 64)),
                        self.blue_grain.activate,
                        buy=self.buy,
                        post_hover_message=self.post_hover_message,
                        message="Blue grain increases nitrate in the ground.",
                        play_selected=self.sound_control.play_select_sfx,
                        cost=NITRATE_COST,
                        cost_label=self.asset_handler.FONT_24.render(
                            f"{NITRATE_COST}", True, config.BLACK
                        ),
                    )
                )
            elif keyword == "spraycan":
                self.shop_items.append(
                    Shop_Item(
                        self.asset_handler.img("spraycan.PNG", (64, 64)),
                        self.spraycan.activate,
                        buy=self.buy,
                        post_hover_message=self.post_hover_message,
                        message="Spray em!",
                        play_selected=self.sound_control.play_select_sfx,
                        cost=SPRAYCAN_COST,
                        cost_label=self.asset_handler.FONT_24.render(
                            f"{SPRAYCAN_COST}", True, config.BLACK
                        ),
                    )
                )
        for item in self.shop_items:
            item.shop_items = self.shop_items
        self.init_layout()

    def buy(self, item):
        if self.plant.upgrade_points - item.cost >= 0:
            self.plant.upgrade_points -= item.cost
            self.animations[max(0, item.cost)].start(pygame.mouse.get_pos())
            item.callback()
            self.sound_control.play_buy_sfx()
            self.update_current_cost()
            self.refund_available = True

    def update(self, dt):
        self.watering_can.update(dt)
        self.blue_grain.update(dt)
        self.spraycan.update(dt)
        self.root_item.update(dt)
        for animation in self.animations:
            animation.update(dt)
        for item in self.shop_items:
            item.update(dt)

    def check_refund(self, mouse_pos, cost):
        if pygame.Rect(
            self.rect[0],
            self.rect[1] + self.rect[3],
            self.refund_image.get_width(),
            self.refund_image.get_height(),
        ).collidepoint(mouse_pos):
            self.plant.upgrade_points += cost
            self.refund_available = False
            return True

    def finalize_shop_transaction(self):
        self.refund_available = False

    def update_current_cost(self):
        self.current_cost = 0
        for item in self.shop_items:
            if item.selected:
                self.current_cost += item.cost
        self.current_cost_label = self.asset_handler.FONT_28.render(
            "{}".format(self.current_cost), False, (0, 0, 0)
        )

    def handle_event(self, e: pygame.event.Event):
        if not self.active:
            return
        if not self.refund_available:  # can't buy new items while refund is available
            for item in self.shop_items:
                item.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.update_current_cost()
        self.watering_can.handle_event(e)
        self.blue_grain.handle_event(e)
        self.spraycan.handle_event(e)
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
        green_thumbs_label = self.asset_handler.FONT_28.render(
            "{}".format(self.plant.upgrade_points), True, config.BLACK
        )
        self.s.blit(
            green_thumbs_label,
            (self.rect[2] - 90 - green_thumbs_label.get_width(), 5),
        )

        self.s.blit(
            self.asset_handler.img("green_thumb.PNG", (26, 26)), (self.rect[2] - 80, 6)
        )
        for item in self.shop_items:
            item.draw(self.s)

        """self.s.blit(
            self.green_thumbs_icon, (70, self.rect[3] - self.margin - 50)
        )
        self.s.blit(
            self.current_cost_label, (50, self.rect[3] - self.margin - 50)
        )
"""
        # s.blit(self.green_thumbs_icon,(self.rect[0]+self.rect[2]-self.margin*4-self.green_thumbs_icon.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-self.green_thumbs_icon.get_height()))
        # s.blit(cost, (self.rect[0]+self.rect[2]-self.margin*5-self.green_thumbs_icon.get_width()-cost.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-cost.get_height()))
        screen.blit(self.s, (self.rect[0], self.rect[1]))

        if self.refund_available:
            screen.blit(
                self.refund_image, (self.rect[0], self.rect[1] + self.rect[3] + 10)
            )

        self.watering_can.draw(screen)
        self.blue_grain.draw(screen)
        self.spraycan.draw(screen)
        self.root_item.draw(screen)
        for animation in self.animations:
            animation.draw(screen)


class Shop_Item:
    def __init__(
        self,
        image,
        callback,
        buy,
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
        play_selected=None,
        offset=(0, 0),
        cost_label=None,
    ):
        self.image = image
        self.callback = callback
        self.buy = buy
        self.cost = cost
        self.info_text = info_text
        self.post_hover_message = post_hover_message
        self.message = message
        self.play_selected = play_selected
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
        self.cost_label = cost_label

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
                self.hover = True

        if e.type == pygame.MOUSEBUTTONDOWN:
            pos = (e.pos[0] - self.offset[0], e.pos[1] - self.offset[1])
            if self.rect.collidepoint(pos):
                self.selected = True

        if e.type == pygame.MOUSEBUTTONUP:
            self.selected = False
            pos = (e.pos[0] - self.offset[0], e.pos[1] - self.offset[1])
            if self.rect.collidepoint(pos):
                if self.condition is not None:
                    if self.condition():
                        self.buy(self)
                else:
                    self.buy(self)

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        if self.hover:
            pygame.draw.rect(screen, self.hover_color, self.rect, self.border_width)
        if self.selected:
            pygame.draw.rect(screen, self.selected_color, self.rect, self.border_width)
        green_thumb_size = (16, 16)
        margin = 3
        cost_label = self.cost_label

        rect_with = cost_label.get_width() + green_thumb_size[0] + 6 * margin
        rect_height = max(green_thumb_size[1], cost_label.get_height()) + 2 * margin - 4
        rect_x = self.rect[0] + self.image.get_width() / 2 - rect_with / 2
        rect_y = self.rect[1] + self.image.get_height() - rect_height / 2

        pygame.draw.rect(
            screen,
            color=config.WHITE_TRANSPARENT_LESS,
            rect=(rect_x, rect_y, rect_with, rect_height),
            border_radius=2,
        )
        pygame.draw.rect(
            screen,
            color=config.WHITE,
            rect=(rect_x, rect_y, rect_with, rect_height),
            border_radius=2,
            width=2,
        )

        screen.blit(
            cost_label,
            (
                rect_x + rect_with / 4 - cost_label.get_width() / 2,
                rect_y + rect_height / 2 - cost_label.get_height() / 2,
            ),
        )

        pygame.draw.circle(
            screen,
            config.GREEN_DARK,
            (rect_x + rect_with * 3 / 4, rect_y + rect_height / 2),
            green_thumb_size[0] / 2,
        )
