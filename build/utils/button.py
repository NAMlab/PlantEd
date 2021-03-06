import pygame

BLACK = (0, 0, 0)
WHITE_TRANSPARENT = (255, 255, 255, 128)
WHITE = (255, 255, 255)

clamp = lambda n, minn, maxn: max(min(maxn, n), minn)


# Button is a sprite subclass, that means it can be added to a sprite group.
# You can draw and update all sprites in a group by
# calling `group.update()` and `group.draw(screen)`.
class Button(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, callbacks, font=None, text='', button_color=WHITE_TRANSPARENT, text_color=BLACK,
                 image=None, border_w=None, post_hover_message=None, hover_message=None, hover_message_image=None, button_sound=None, active=True):
        super().__init__()
        self.posted = False
        self.button_sound = button_sound
        self.post_hover_message = post_hover_message
        self.hover_message_image = hover_message_image
        self.border_w = int(w / 10) if not border_w else border_w
        self.active = active
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)
        if image:
            self.button_image.blit(image.copy(), (0, 0))
            self.hover_image.blit(image.copy(), (0, 0))
            self.clicked_image.blit(image.copy(), (0, 0))
        else:
            self.button_image.fill(button_color)
            self.hover_image.fill(button_color)
            self.clicked_image.fill(button_color)
        pygame.draw.rect(self.hover_image, WHITE, self.hover_image.get_rect(), self.border_w)
        pygame.draw.rect(self.clicked_image, WHITE, self.clicked_image.get_rect(), self.border_w)
        if text and font:
            text_surf = font.render(text, True, text_color)
            self.button_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.hover_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.clicked_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.button_down = False
        if post_hover_message and hover_message:
            self.posted = False
            hover_message = font.render(hover_message, True, text_color)
            w = hover_message.get_width()+10
            if self.hover_message_image:
                w += hover_message_image.get_width() +10
            self.hover_message = pygame.Surface((w, hover_message.get_height()+10), pygame.SRCALPHA)
            self.hover_message.fill(WHITE_TRANSPARENT)
            self.hover_message.blit(hover_message, (5,5))
            if self.hover_message_image:
                self.hover_message.blit(self.hover_message_image,(hover_message.get_width()+10, 8))

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.image = self.clicked_image
                if self.button_sound:
                    pygame.mixer.Sound.play(self.button_sound)
                self.button_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(event.pos) and self.button_down:
                for callback in self.callbacks:
                    callback()  # Call the function.
                self.image = self.hover_image
            self.button_down = False
        elif event.type == pygame.MOUSEMOTION:
            collided = self.rect.collidepoint(event.pos)
            if collided and not self.button_down:
                self.image = self.hover_image
                if not self.posted and self.post_hover_message:
                    self.posted = True
                    self.post_hover_message(self.hover_message)
            elif not collided and not self.button_down:
                if self.post_hover_message and self.posted:
                    self.posted = False
                    self.post_hover_message(None)
                self.image = self.button_image

    def draw(self, screen):
        screen.blit(self.image, (self.rect[0],self.rect[1]))

    def set_pos(self, pos):
        self.x = pos[0]
        self.y = pos[1]


class ToggleButton(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, callback, font=None, text='', button_color=WHITE_TRANSPARENT, text_color=BLACK,
                 image=None, border_w=None, pressed=False, fixed=False, vertical=False):
        super().__init__()
        self.fixed = fixed
        self.border_w = int(5) if not border_w else border_w
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)
        if image:
            self.button_image.blit(image.copy(), (0, 0))
            self.hover_image.blit(image.copy(), (0, 0))
            self.clicked_image.blit(image.copy(), (0, 0))
        else:
            self.button_image.fill(button_color)
            self.hover_image.fill(button_color)
            self.clicked_image.fill(button_color)
        pygame.draw.rect(self.hover_image, WHITE_TRANSPARENT, self.hover_image.get_rect(), self.border_w)
        pygame.draw.rect(self.clicked_image, WHITE, self.clicked_image.get_rect(), self.border_w)
        if text and font:
            text_surf = font.render(text, True, text_color)
            if vertical:
                text_surf = pygame.transform.rotate(text_surf,90)
            self.button_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.hover_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.clicked_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callback = callback
        self.button_down = False
        if pressed:
            self.image = self.clicked_image
            self.button_down = True
            for callback in self.callback:
                callback()


    def handle_event(self, event):
        if self.fixed:
            return
        else:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    if self.button_down:
                        self.button_down = False
                        self.image = self.button_image
                    else:
                        self.image = self.clicked_image
                        self.button_down = True
                    for callback in self.callback:
                        callback()  # Call the function.

    def activate(self):
        self.button_down = True
        self.image = self.clicked_image
        for callback in self.callback:
            callback()

    def deactivate(self):
        self.button_down = False
        self.image = self.button_image
        for callback in self.callback:
            callback()

# image size has to be = w,h
class RadioButton(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, callbacks, font=None, text='', button_color=WHITE_TRANSPARENT, text_color=BLACK,
                 image=None, border_w=None, target=None, callback_var=None, border_radius=0):
        super().__init__()
        self.callback_var = callback_var
        self.target = target if target else None
        self.border_w = 5 if not border_w else border_w
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)
        if image:
            self.button_image.blit(image.copy(), (0, 0))
            self.hover_image.blit(image.copy(), (0, 0))
            self.clicked_image.blit(image.copy(), (0, 0))
        else:
            self.button_image.fill(button_color)
            self.hover_image.fill(button_color)
            self.clicked_image.fill(button_color)
        pygame.draw.rect(self.hover_image, WHITE_TRANSPARENT, self.hover_image.get_rect(), self.border_w, border_radius=border_radius)
        pygame.draw.rect(self.clicked_image, WHITE, self.clicked_image.get_rect(), self.border_w, border_radius=border_radius)
        if text and font:
            text_surf = font.render(text, True, text_color)
            self.button_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.hover_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
            self.clicked_image.blit(text_surf, text_surf.get_rect(center=(w // 2, h // 2)))
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.button_down = False

    def setRadioButtons(self, buttons):
        self.buttons = buttons

    def handle_event(self, event):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover and event.button == 1:
                if self.buttons:
                    for rb in self.buttons:
                        rb.button_down = False
                self.button_down = True
                for callback in self.callbacks:
                    if self.callback_var:
                        callback(self.callback_var)
                    else:
                        callback()
        self.image = self.button_image
        if self.button_down:
            self.image = self.clicked_image
        elif hover:
            self.image = self.hover_image


class OptionBox:
    def __init__(self, x, y, w, h, color, highlight_color, font, option_list, selected=0):
        self.color = color
        self.highlight_color = highlight_color
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.option_list = option_list
        self.selected = selected
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.highlight_color if self.menu_active else self.color, self.rect)
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[self.selected], 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, self.highlight_color if i == self.active_option else self.color, rect)
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center=rect.center))
            outer_rect = (
                self.rect.x, self.rect.y + self.rect.height, self.rect.width, self.rect.height * len(self.option_list))
            pygame.draw.rect(surf, (0, 0, 0), outer_rect, 2)

    def update(self, event_list):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)

        self.active_option = -1
        for i in range(len(self.option_list)):
            rect = self.rect.copy()
            rect.y += (i + 1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.selected = self.active_option
                    self.draw_menu = False
                    return self.active_option
        return -1

# Todo include slider to mouse offset when clicked to avoid jumping
class Slider():
    def __init__(self, rect, font, slider_size, organ=None, plant=None, color=None, slider_color=None, callback=None, percent=0, active=True, visible=True):
        super().__init__()
        self.color = color if color else (255, 255, 255, 128)
        self.slider_color = slider_color if slider_color else (self.color[0], self.color[1], self.color[2])
        self.drag = False
        self.font = font
        self.visible = visible
        self.active = active
        self.organ = organ
        self.plant = plant
        self.x, self.y, self.w, self.h = rect
        self.slider_y = 100
        self.slider_w = slider_size[0] if slider_size else self.w
        self.slider_h = slider_size[1] if slider_size else self.w
        self.callback = callback
        self.rect = rect
        self.set_percentage(percent)


    def update(self):
        if self.organ is not None:
            if self.organ.active:
                self.active = True
        if not self.active:
            return


    def get_percentage(self):
        line_height = self.h - self.slider_h
        slider_length = self.slider_y
        percent = slider_length/line_height*100
        return 100-percent

    def get_slider_rect_global(self):
        return pygame.Rect(self.x, self.y+self.slider_y, self.slider_w, self.slider_h)

    def get_slider_rect_local(self):
        return pygame.Rect(0, self.slider_y, self.slider_w, self.slider_h)

    def set_percentage(self, percent):
        line_height = self.h - self.slider_h
        slider_length = (100-percent)*line_height/100
        self.slider_y = slider_length
        self.organ.percentage = self.get_percentage()

    def sub_percentage(self, percent):
        delta = self.get_percentage() - percent
        if delta < 0:
            self.set_percentage(0)
            return delta
        else:
            self.set_percentage(delta)
            return 0

    def draw(self, screen):
        if not self.visible:
            return
        slider_color = self.slider_color if self.active else (150,150,150,128)
        w = self.w if self.w >= self.slider_w else self.slider_w
        border = pygame.Surface((w, self.h), pygame.SRCALPHA)
        # line
        pygame.draw.rect(border, self.color, (w / 2 - self.w / 2, self.slider_h/2, self.w, self.h-self.slider_h))

        # draw slider
        pygame.draw.rect(border, slider_color, self.get_slider_rect_local())
        msg = self.font.render("{:02.0f}".format(self.get_percentage()), 1, (0, 0, 0))
        border.blit(msg, msg.get_rect(center=self.get_slider_rect_local().center))
        screen.blit(border, (self.x, self.y))

    def handle_event(self, event):
        if not self.active:
            return
        rect = self.get_slider_rect_global()
        hover = rect.collidepoint(pygame.mouse.get_pos())

        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover and event.button == 1:
                #print(event.type, "Hopefully a slider move", hover, self.drag)
                self.drag = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drag:
                self.drag = False
                if self.organ is not None:
                    self.organ.set_percentage(self.get_percentage())
                if self.callback:
                    self.callback(self)
        if event.type == pygame.MOUSEMOTION:
            if self.drag:
                # clamp the slider pos between min y and max, subtract slider_h/2 to not clip
                self.slider_y = clamp(pygame.mouse.get_pos()[1], self.y, self.y - self.slider_h + self.h) - self.y


class SliderGroup:
    def __init__(self, sliders, max_sum):
        self.sliders = sliders
        self.sliders_zero = []
        self.max_sum = max_sum

        for slider in self.sliders:
            slider.callback= self.change_percentage
            # slider.set_percentage(self.max_sum/len(self.sliders))

    def slider_sum(self):
        return sum([slider.get_percentage() for slider in self.sliders])

    def change_percentage(self, slider):
        # @slider: slider that changed
        while self.max_sum < self.slider_sum()-0.1 or self.max_sum > self.slider_sum()+1:
            # special case, if max is smaller than 100%
            if slider.get_percentage() > self.max_sum:
                slider.set_percentage(self.max_sum)
            # slider that called and zero sliders aren't able to reduce --> available_sliders
            available_sliders = (len(self.sliders) - len(self.sliders_zero)) - 1
            delta = (self.slider_sum() - self.max_sum) / (available_sliders)
            for s in self.sliders:
                if s == slider or s in self.sliders_zero:
                    pass
                else:
                    # extra: extra = s.get_percentage() - delta
                    extra = s.sub_percentage(delta)
                    if extra > 0:
                        self.sliders_zero.append(s)

class Textbox:
    def __init__(self, x,y,w,h, font, text="name", color=(240,240,240,180), highlight_color=(255,255,255,255)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x,y,w,h)
        self.text = text
        self.font = font
        self.render_text = self.font.render(self.text, True, (0,0,0))
        self.color = color
        self.higlight_color = highlight_color
        self.active = False
        self.max_chars = 10

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(e.pos):
                self.active = True
                #print(self.active)
            else:
                self.active = False
        if not self.active:
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_chars:
                    self.text += e.unicode
        self.render_text = self.font.render(self.text, True, (0,0,0))

    def draw(self, screen):
        if self.active:
            pygame.draw.rect(screen, self.higlight_color, self.rect, border_radius=3)
        else:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=3)
        #pygame.draw.rect(screen, self.border_color, self.rect, border_radius=3, width=3)
        screen.blit(self.render_text, (self.x+self.w/2-self.render_text.get_width()/2,self.y+self.h/2-self.render_text.get_height()/2))




