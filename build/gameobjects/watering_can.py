import pygame

class watering_can:
    def __init__(self, pos, amount=0, rate=0.15, cost=1):
        self.pos = pos
        self.amount = amount
        self.rate = rate
        self.cost = cost
        self.active = False

    def activate(self, amount):
        self.active = True
        self.amount = amount

    def deactivate(self):
        self.amount = 0
        self.active = False

    def update(self):
        if self.active:
            if self.amount < 0:
                self.amount = 0
                self.active = False
            else:
                self.amount -= self.rate




'''
self.watering_can = {"active": False,
                             "button": Button(780, 270, 64, 64, [self.activate_watering_can], self.sfont,
                                              image=assets.img("watering_can_outlined.png", (64,64)), post_hover_message=self.post_hover_message,
                                              hover_message="Water Your Plant, Cost: 1",  hover_message_image=assets.img("green_thumb.png", (20, 20)), button_sound=assets.sfx('button_klick.mp3', 0.8)),
                             "image": assets.img("watering_can_outlined.png"),
                             "amount": 0,
                             "rate": 0.15,
                             "cost": 1,
                             "pouring": False}
'''