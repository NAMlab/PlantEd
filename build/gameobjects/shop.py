import pygame
from utils.button import Button
import config
from utils.animation import LabelAnimation
from gameobjects.watering_can import Watering_can
from gameobjects.blue_grain import Blue_grain
from gameobjects.spraycan import Spraycan
from data import assets
'''
shop holds items and interfaces actions to consumables
holds green thumbs, checks if buyable

shopitems have action and button and cost
'''

class Shop:
    def __init__(self, rect, shop_items, model, plant, cols=2, margin=10, post_hover_message=None):
        self.rect = rect
        self.shop_items = shop_items
        self.margin = margin
        self.post_hover_message = post_hover_message
        self.model = model
        self.plant = plant
        self.green_thumbs_icon = assets.img("green_thumb.png",(26,26))
        self.current_cost = 0
        self.animations = []
        self.watering_can = Watering_can((0,0), self.model)
        self.blue_grain = Blue_grain((0,0), self.model)
        self.spraycan = Spraycan((0,0), self.model,3,2)
        self.buy_button = Button(self.rect[0]+self.rect[2]-self.margin*2-64,self.rect[1]+self.rect[3]-self.margin-64,64,64,[self.buy],config.FONT,"BUY")
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
        rows = int(0.5+len(self.shop_items)/columns) # 0.5 to get single items accounted for
        for i in range(0,rows):
            for j in range(0,columns):
                x = j * (width/columns) + ((width / columns) - img_width) / 2
                y = i+1 * self.margin + img_width * i + self.margin * i
                # looks dirty, maybe zip?
                if len(self.shop_items) > i*columns+j:
                    self.shop_items[i*columns+j].rect = pygame.Rect(x+self.rect[0],y+self.rect[1]+50, img_width, img_width)

    def add_shop_item(self, shop_item):
        self.shop_items.append(shop_item)
        for item in self.shop_items:
            item.shop_items = self.shop_items

    def add_shop_item(self, keywords):
        for keyword in keywords:
            if keyword == "watering":
                self.shop_items.append(Shop_Item(assets.img("watering_can_outlined_tilted.png", (64, 64)), self.watering_can.activate,post_hover_message=self.post_hover_message, message="Buy a watering can to increase availability."))
            elif keyword == "blue_grain":
                self.shop_items.append(Shop_Item(assets.img("blue_grain_0.png", (64, 64)), self.blue_grain.activate, post_hover_message=self.post_hover_message, message="Blue grain increases nitrate in the ground."))
            elif keyword == "spraycan":
                self.shop_items.append(Shop_Item(assets.img("spraycan_icon.png", (64, 64)), self.spraycan.activate, post_hover_message=self.post_hover_message, message="Spray em!"))
        for item in self.shop_items:
            item.shop_items = self.shop_items
        self.init_layout()

    def buy(self):
        for item in self.shop_items:
            if item.selected:
                if self.plant.upgrade_points - item.cost >= 0:
                    self.plant.upgrade_points -= item.cost
                    item.callback()
                    item.selected = False
                    #cost = config.FONT.render("{}".format(self.current_cost), False, (255, 255, 255))
                    #self.animations.append(LabelAnimation(cost, item.cost, 120, self.cost_label_pos))
                else:
                    # throw insufficient funds, maybe post hover msg
                    pass

    def update(self, dt):
        self.current_cost = 0
        self.watering_can.update(dt)
        self.blue_grain.update(dt)
        self.spraycan.update(dt)
        self.buy_button.update(dt)
        for item in self.shop_items:
            if item.selected:
                self.current_cost += item.cost
        for item in self.shop_items:
            item.update(dt)
        for anim in self.animations:
            anim.update()

    def handle_event(self, e):
        x,y = pygame.mouse.get_pos()
        #if self.rect.collidepoint(x,y):
            #self.confirm_button.handle_event(e)
        for item in self.shop_items:
            item.handle_event(e)
        self.watering_can.handle_event(e)
        self.blue_grain.handle_event(e)
        self.spraycan.handle_event(e)
        self.buy_button.handle_event(e)

    def draw(self, screen):
        # s should only be as big as rect, for the moment its fine
        s = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(s, config.WHITE_TRANSPARENT, (self.rect[0],self.rect[1]+45,self.rect[2],self.rect[3]-45), border_radius=3)
        #pygame.draw.rect(s, (255,255,255), self.rect, int(self.margin/2))
        pygame.draw.rect(s,config.WHITE,(self.rect[0],self.rect[1],self.rect[2],40),border_radius=3)
        shop_label = config.BIG_FONT.render("Shop",True,(0,0,0))
        s.blit(shop_label,dest=(self.rect[0]+self.rect[2]/2-shop_label.get_width()/2,self.rect[1]+5))
        for item in self.shop_items:
            item.draw(s)
        self.buy_button.draw(s)
        cost = config.BIG_FONT.render("{}".format(self.current_cost),False,(0,0,0))
        s.blit(self.green_thumbs_icon,(self.rect[0]+self.rect[2]-self.margin*4-self.green_thumbs_icon.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-self.green_thumbs_icon.get_height()))
        s.blit(cost, (self.rect[0]+self.rect[2]-self.margin*5-self.green_thumbs_icon.get_width()-cost.get_width()-64,self.rect[1]+self.rect[3]-self.margin*3-cost.get_height()))
        screen.blit(s,(0,0))
        self.watering_can.draw(screen)
        self.blue_grain.draw(screen)
        self.spraycan.draw(screen)


class Shop_Item:
    def __init__(self, image, callback, cost=1, info_text=None, rect=(0,0,0,0), selected_color=(255,255,255), hover_color = (128,128,128,128), border_width=3, post_hover_message=None, message=None):
        self.image = image
        self.callback = callback
        self.cost = cost
        self.info_text = info_text
        self.post_hover_message = post_hover_message
        self.message = message
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
                if self.post_hover_message is not None:
                    self.post_hover_message(self.message)
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