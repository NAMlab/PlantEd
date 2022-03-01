'''

shop holds buttons and interfaces actions to consumables
has ability to change green thumbs

shopitems have action and button and cost


'''

#no visuals, just functional, plus draw, components are set to default visuals, maybe in future implement dynamic sizing
class Shop:
    def __init__(self, shop_items, green_thumbs=0, pos=(0,0)):
        self.pos = pos
        self.green_thumbs = green_thumbs
        self.shop_items = []

    def add_shop_item(self, shop_item):
        self.shop_items.append(shop_item)

    def update(self, dt):
        for item in self.shop_items:
            item.update()

    def handle_event(self, e):
        for item in self.shop_items:
            item.handle_event(e)

    def draw(self, screen):
        for item in self.shop_items:
            item.draw()

class Shop_Item:
    def __init__(self, image, button, cost, pos=(0,0)):
        self.image = image
        self.button = button
        self.cost = cost
        self.pos = pos

    def update(self, dt):
        pass

    def handle_event(self, e):
        self.button.handle_event(e)

    def draw(self, screen):
        pass