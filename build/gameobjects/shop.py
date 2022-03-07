import pygame
from utils.button import Button
import config
from utils.animation import LabelAnimation
'''
shop holds items and interfaces actions to consumables
holds green thumbs, checks if buyable

shopitems have action and button and cost
'''

class Shop:
    def __init__(self, pos, shop_items, cols=2, green_thumbs=0):
        self.pos = pos
        self.shop_items = shop_items
        for item in self.shop_items:
            item.shop_items = self.shop_items
        self.cols = cols
        self.green_thumbs = green_thumbs
        self.current_cost = 0
        self.animations = []
        self.cost_label_pos = None
        self.init_layout()


    def add_shop_item(self, shop_item):
        self.shop_items.append(shop_item)

    def buy(self):
        for item in self.shop_items:
            if item.selected:
                if self.green_thumbs - item.cost >= 0:
                    item.callback()
                    item.selected = False
                    print(item.cost, self.green_thumbs)
                    cost = config.FONT.render("{}".format(self.current_cost), False, (255, 255, 255))
                    self.animations.append(LabelAnimation(cost, item.cost, 120, self.cost_label_pos))
                else:
                    # throw insufficient funds, maybe post hover msg
                    pass
        pass

    def update(self, dt):
        self.current_cost = 0
        for item in self.shop_items:
            if item.selected:
                self.current_cost += item.cost
        for item in self.shop_items:
            item.update(dt)
        for anim in self.animations:
            anim.update()

    def handle_event(self, e):
        x,y = pygame.mouse.get_pos()
        if self.rect.collidepoint(x,y):
            self.confirm_button.handle_event(e)
        for item in self.shop_items:
            item.handle_event(e)

    def draw(self, screen):
        pygame.draw.rect(screen, (255,255,255), self.rect, int(self.margin/2))
        for item in self.shop_items:
            item.draw(screen)
        self.buttons.draw(screen)
        cost = config.FONT.render("{}".format(self.current_cost),False,(255,255,255))
        screen.blit(cost, (int(self.cost_label_pos[0]-cost.get_width()/2), int(self.cost_label_pos[1]-cost.get_height()/2)))

    # layout
    def init_layout(self):
        self.margin = 10
        self.cost_label_pos = (0, 0)
        self.align_items()  # align all gobal x and y
        x, y, w, h = self.align_confirm_button()  # get confirm button position
        self.confirm_button = Button(x, y, w, h, [self.buy], font=config.FONT, text="buy")
        self.rect = self.get_rect()
        # old but still working, maybe nonsense for just one
        self.buttons = pygame.sprite.Group()
        self.buttons.add(self.confirm_button)

    def align_cost_label(self):
        pass

    def align_confirm_button(self):
        # align confirm button
        w = self.shop_items[0].image.get_width()
        h = self.shop_items[0].image.get_height()
        x = self.pos[0] + self.cols * (self.margin + w) - w
        y = self.pos[1] + self.margin + int((h + self.margin) * int((len(self.shop_items) + 1) / self.cols))

        self.cost_label_pos = (int(self.pos[0] + (self.cols - 1) * (self.margin + w) - w / 2),
                               int(self.pos[1] + self.margin + int(
                                   (h + self.margin) * int((len(self.shop_items) + 1) / self.cols))) + h / 2)
        return x, y, w, h

    # align all shop items to global x,y
    def align_items(self):
        w, h = self.shop_items[0].image.get_width(), self.shop_items[0].image.get_height()
        for i in range(0, len(self.shop_items)):
            x = self.pos[0] + int((i % self.cols)) * self.margin + (i % self.cols) * w + self.margin
            y = self.pos[1] + int((i / self.cols)) * self.margin + int(i / self.cols) * h + self.margin
            self.shop_items[i].rect = pygame.Rect(x, y, w, h)

    # get shop rect global
    def get_rect(self):
        width = self.margin + int((self.shop_items[0].image.get_width() + self.margin) * self.cols)
        height = self.margin + int(
            (self.shop_items[0].image.get_height() + self.margin) * int((len(self.shop_items) + 1) / self.cols))
        height += self.margin + self.confirm_button.rect[3]
        return pygame.Rect(self.pos[0], self.pos[1], width, height)


class Shop_Item:
    def __init__(self, image, callback, cost=1, info_text=None, rect=(0,0,0,0), selected_color=(255,255,255), hover_color = (128,128,128), border_width=5):
        self.image = image
        self.callback = callback
        self.cost = cost
        self.info_text = info_text
        self.rect = pygame.Rect(rect[0],rect[1],rect[2],rect[3]) # ugly
        self.selected_color = selected_color
        self.hover_color = hover_color
        self.border_width = border_width
        self.hover = False
        self.selected = False
        self.shop_items = []

    def update(self, dt):
        pass

    # pass event to buttons to check if bought, also handle hover
    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            x,y = pygame.mouse.get_pos()
            if self.rect.collidepoint(x,y):
                if not self.selected:
                    self.hover = True
            else:
                self.hover = False

        if e.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if self.rect.collidepoint(x, y):
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
            pygame.draw.rect(screen, self.hover_color, self.rect, self.border_width)
        if self.selected:
            pygame.draw.rect(screen, self.selected_color, self.rect, self.border_width)