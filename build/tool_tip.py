import pygame
from button import Button


class ToolTipManager:
    def __init__(self, tool_tips, callback=None):
        self.tool_tips = tool_tips
        self.callback = callback
        self.active = False
        self.current_tip = 0 if tool_tips else -1

        if self.current_tip >= 0:
            self.tool_tips[self.current_tip].activate()

    def toggle_activate(self):
        self.active = not self.active

    def draw(self, screen):
        if self.active:
            for tip in self.tool_tips:
                tip.draw(screen)

    def update(self):
        if not self.tool_tips:
            return
        if self.callback:
            biomass = self.callback()
            if self.tool_tips[self.current_tip].done and len(self.tool_tips)-1 > self.current_tip:
                if self.tool_tips[self.current_tip+1].mass < biomass:
                    self.current_tip += 1
                    self.tool_tips[self.current_tip].activate()
            #for tip in self.tool_tips:
            #    if tip.mass < biomass and not tip.done:
            #        tip.activate()


class ToolTip:
    def __init__(self, x, y, w, h, lines, font, headfont=None, mass=-1, color=(245, 245, 245, 255), active=False, point=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.mass = mass
        self.color = color
        self.active = active
        self.done = False
        self.font = font
        self.headfont = headfont
        # maybe ugly, but smart to prevent ugly boxes, thus not ugly
        self.text, self.w, self.h = self.make_text(lines)
        self.triangle = []
        self.set_triangle(point) if point else None
        self.button = Button(self.x, self.y + (self.h - 50), self.w, 50, [self.deactivate], self.font,
                        text='OK', border_w=5)

    def update(self):
        pass

    def handle_event(self, e):
        if self.active:
            self.button.handle_event(e)

    def make_text(self, lines):
        text = []
        min_h = 0
        min_w = 0
        for i in range (0,len(lines)):
            if i == 0 and self.headfont:
                single_line = self.headfont.render(lines[i], True, (0, 0, 0))
            else:
                single_line = self.font.render(lines[i], True, (0, 0, 0))
            min_w = max(min_w,single_line.get_width())
            min_h = min_h + single_line.get_height()*1.1
            text.append(single_line)
        w = max(min_w, self.w)+10
        h = max(min_h, self.w)
        return text, w, h + 75

    def deactivate(self):
        self.active = False
        self.done = True

    def activate(self):
        self.active = True

    def set_triangle(self, point):
        if point[0] < 0:
            self.triangle.append((point[0] + 50, point[1]))
            self.triangle.append((50, self.h/3))
            self.triangle.append((50, self.h/3*2))
        else:
            self.triangle.append((point[0] + self.w + 50, point[1]))
            self.triangle.append((self.w+50, self.h/3))
            self.triangle.append((self.w+50, self.h/3*2))

    def draw(self, screen):
        if not self.active:
            return
        box = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(box,self.color, (0,0,self.w,self.h), border_radius=5)
        init_x = self.w/2
        init_y = int(self.text[0].get_height()*1.1/2)+10
        for text in self.text:
            text_rect = text.get_rect(center=(init_x, init_y))
            box.blit(text, text_rect)
            init_y += int(text.get_height()*1.1)
        if self.triangle:
            box_extra = pygame.Surface((self.w+100, self.h), pygame.SRCALPHA)
            pygame.draw.polygon(box_extra, self.color, self.triangle)
            screen.blit(box_extra, (self.x-50,self.y))
        screen.blit(box, (self.x, self.y))
        screen.blit(self.button.image, (self.button.rect[0], self.button.rect[1]))