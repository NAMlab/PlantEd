import pygame
from button import Button


class ToolTipManager:
    def __init__(self, tool_tips):
        self.tool_tips = tool_tips
        self.current_tip = 0 if tool_tips else -1
        if self.current_tip >= 0:
            self.tool_tips[self.current_tip].activate()

    def draw(self, screen):
        self.tool_tips[self.current_tip].draw(screen)

    def update(self):
        if self.tool_tips[self.current_tip].check_condition():
            if len(self.tool_tips) > self.current_tip:
                self.current_tip += 1
                self.tool_tips[self.current_tip].activate()


class ToolTip:
    def __init__(self, x, y, w, h, lines, font, button_group, callback=None, mass=-1, color=(255, 255, 255, 128), done=False, point=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.mass = mass
        self.color = color
        self.done = done
        self.font = font
        self.callback = callback    #has to return bool, good practice or stupid?
        # maybe ugly, but smart to prevent ugly boxes, thus not ugly
        self.text, self.w, min_h = self.make_text(lines)
        self.h = min_h * (len(self.text)+1) + 20    # h equals all lines, button and buffer 20
        self.triangle = []
        self.set_triangle(point) if point else None
        self.button = Button(self.x, self.y + (self.h - min_h), self.w, min_h, [self.deactivate], self.font,
                        text='Got it', border_w=5)
        self.button_group = button_group

    def update(self):
        pass

    def check_condition(self):
        result = False
        if self.done:
            if self.callback and self.mass > -1:
                result = True if self.callback() > self.mass else False
            else:
                result = True
        return result

    def make_text(self, lines):
        text = []
        min_h = self.h
        w = self.w
        for line in lines:
            single_line = self.font.render(line, True, (0, 0, 0))
            min_w = single_line.get_width() + 20
            min_h = single_line.get_height()
            w = min_w if min_w > w else w
            text.append(single_line)
        return text, w, min_h

    def deactivate(self):
        self.button_group.remove(self.button)
        self.done = True

    def activate(self):
        self.button_group.add(self.button)

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
        if self.done:
            return
        box = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        pygame.draw.rect(box,self.color, (0,0,self.w,self.h), border_radius=5)
        init_x = 10
        init_y = 10
        for text in self.text:
            text_rect = text.get_rect(topleft=(init_x, init_y))
            box.blit(text, text_rect)
            init_y += text.get_height()
        if self.triangle:
            box_extra = pygame.Surface((self.w+100, self.h), pygame.SRCALPHA)
            pygame.draw.polygon(box_extra, self.color, self.triangle)
            screen.blit(box_extra, (self.x-50,self.y))
        screen.blit(box, (self.x, self.y))