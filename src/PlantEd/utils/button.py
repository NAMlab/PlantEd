import pygame

from PlantEd import config

BLACK = (0, 0, 0)
WHITE_TRANSPARENT = (255, 255, 255, 128)
WHITE = (255, 255, 255)

clamp = lambda n, minn, maxn: max(min(maxn, n), minn)


# Button is a sprite subclass, that means it can be added to a sprite group.
# You can draw and update all sprites in a group by
# calling `group.update()` and `group.draw(screen)`.
class Button(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callbacks,
            font=None,
            text="",
            button_color=WHITE_TRANSPARENT,
            text_color=BLACK,
            image=None,
            border_w=None,
            post_hover_message=None,
            hover_message=None,
            hover_message_image=None,
            button_sound=None,
            active=True,
            offset=(0, 0),
            callback_var=None,
            play_confirm=None,
    ):
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
        self.offset = offset
        self.play_confirm = play_confirm
        if image:
            self.button_image.blit(image.copy(), (0, 0))
            self.hover_image.blit(image.copy(), (0, 0))
            self.clicked_image.blit(image.copy(), (0, 0))
        else:
            self.button_image.fill(button_color)
            self.hover_image.fill(button_color)
            self.clicked_image.fill(button_color)
        pygame.draw.rect(
            self.hover_image, WHITE, self.hover_image.get_rect(), self.border_w
        )
        pygame.draw.rect(
            self.clicked_image,
            WHITE,
            self.clicked_image.get_rect(),
            self.border_w,
        )
        if text and font:
            text_surf = font.render(text, True, text_color)
            self.button_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.hover_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.clicked_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.callback_var = callback_var
        self.button_down = False
        if post_hover_message and hover_message:
            self.posted = False
            hover_message = font.render(hover_message, True, text_color)
            w = hover_message.get_width() + 10
            if self.hover_message_image:
                w += hover_message_image.get_width() + 10
            self.hover_message = pygame.Surface(
                (w, hover_message.get_height() + 10), pygame.SRCALPHA
            )
            self.hover_message.fill(WHITE_TRANSPARENT)
            self.hover_message.blit(hover_message, (5, 5))
            if self.hover_message_image:
                self.hover_message.blit(
                    self.hover_message_image,
                    (hover_message.get_width() + 10, 8),
                )

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            if self.rect.collidepoint(pos):
                self.image = self.clicked_image
                if self.button_sound:
                    pygame.mixer.Sound.play(self.button_sound)
                self.button_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(pos) and self.button_down:
                for callback in self.callbacks:
                    if self.callback_var:
                        callback(self.callback_var)
                    else:
                        callback()
                if len(self.callbacks) > 0 and self.play_confirm is not None:
                    self.play_confirm()
                self.image = self.hover_image
            self.button_down = False
        elif event.type == pygame.MOUSEMOTION:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            collided = self.rect.collidepoint(pos)
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
        screen.blit(self.image, (self.rect[0], self.rect[1]))

    def set_pos(self, pos):
        self.x = pos[0]
        self.y = pos[1]


class Button_Once(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callbacks,
            font=None,
            text="",
            button_color=WHITE_TRANSPARENT,
            text_color=BLACK,
            image=None,
            border_w=None,
            post_hover_message=None,
            hover_message=None,
            hover_message_image=None,
            button_sound=None,
            active=True,
            offset=(0, 0),
            callback_var=None,
    ):
        super().__init__()
        self.posted = False
        self.button_sound = button_sound
        self.post_hover_message = post_hover_message
        self.hover_message_image = hover_message_image
        self.border_w = int(w / 10) if not border_w else border_w
        self.active = active
        self.visible = True
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.offset = offset
        if image:
            self.button_image.blit(image.copy(), (0, 0))
            self.hover_image.blit(image.copy(), (0, 0))
            self.clicked_image.blit(image.copy(), (0, 0))
        else:
            self.button_image.fill(button_color)
            self.hover_image.fill(button_color)
            self.clicked_image.fill(button_color)
        pygame.draw.rect(
            self.hover_image, WHITE, self.hover_image.get_rect(), self.border_w
        )
        pygame.draw.rect(
            self.clicked_image,
            WHITE,
            self.clicked_image.get_rect(),
            self.border_w,
        )
        if text and font:
            text_surf = font.render(text, True, text_color)
            self.button_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.hover_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.clicked_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.callback_var = callback_var
        self.button_down = False
        if post_hover_message and hover_message:
            self.posted = False
            hover_message = font.render(hover_message, True, text_color)
            w = hover_message.get_width() + 10
            if self.hover_message_image:
                w += hover_message_image.get_width() + 10
            self.hover_message = pygame.Surface(
                (w, hover_message.get_height() + 10), pygame.SRCALPHA
            )
            self.hover_message.fill(WHITE_TRANSPARENT)
            self.hover_message.blit(hover_message, (5, 5))
            if self.hover_message_image:
                self.hover_message.blit(
                    self.hover_message_image,
                    (hover_message.get_width() + 10, 8),
                )

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            if self.rect.collidepoint(pos):
                self.image = self.clicked_image
                if self.button_sound:
                    pygame.mixer.Sound.play(self.button_sound)
                self.button_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(pos) and self.button_down:
                for callback in self.callbacks:
                    if self.callback_var:
                        callback(self.callback_var)
                    else:
                        callback()
                self.image = self.hover_image
                self.active = False
                self.visible = False
            self.button_down = False
        elif event.type == pygame.MOUSEMOTION:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            collided = self.rect.collidepoint(pos)
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
        if self.visible:
            screen.blit(self.image, (self.rect[0], self.rect[1]))

    def set_pos(self, pos):
        self.x = pos[0]
        self.y = pos[1]


class Arrow_Button(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callbacks,
            arrow_dir,
            font=None,
            text="",
            arrow_color=WHITE,
            border_w=None,
            post_hover_message=None,
            hover_message=None,
            hover_message_image=None,
            button_sound=None,
            active=True,
            offset=(0, 0),
            callback_var=None,
    ):
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
        self.offset = offset

        if arrow_dir == 0:
            pygame.draw.line(
                self.button_image,
                arrow_color,
                (0 + border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w,
            )
            pygame.draw.line(
                self.button_image,
                arrow_color,
                (w - border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w,
            )
            pygame.draw.line(
                self.hover_image,
                arrow_color,
                (0 + border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w + 2,
            )
            pygame.draw.line(
                self.hover_image,
                arrow_color,
                (w - border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w + 2,
            )
            pygame.draw.line(
                self.clicked_image,
                arrow_color,
                (0 + border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w + 4,
            )
            pygame.draw.line(
                self.clicked_image,
                arrow_color,
                (w - border_w, h - border_w),
                (w / 2, 0 + border_w),
                width=border_w + 4,
            )
        else:
            pygame.draw.line(
                self.button_image,
                arrow_color,
                (0 + border_w, border_w),
                (w / 2, h - border_w),
                width=border_w,
            )
            pygame.draw.line(
                self.button_image,
                arrow_color,
                (w - border_w, border_w),
                (w / 2, h - border_w),
                width=border_w,
            )
            pygame.draw.line(
                self.hover_image,
                arrow_color,
                (0 + border_w, border_w),
                (w / 2, h - border_w),
                width=border_w + 2,
            )
            pygame.draw.line(
                self.hover_image,
                arrow_color,
                (w - border_w, border_w),
                (w / 2, h - border_w),
                width=border_w + 2,
            )
            pygame.draw.line(
                self.clicked_image,
                arrow_color,
                (0 + border_w, border_w),
                (w / 2, h - border_w),
                width=border_w + 4,
            )
            pygame.draw.line(
                self.clicked_image,
                arrow_color,
                (w - border_w, border_w),
                (w / 2, h - border_w),
                width=border_w + 4,
            )

        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.callback_var = callback_var
        self.button_down = False
        if post_hover_message and hover_message:
            self.posted = False
            hover_message = font.render(hover_message, True, text_color)
            w = hover_message.get_width() + 10
            if self.hover_message_image:
                w += hover_message_image.get_width() + 10
            self.hover_message = pygame.Surface(
                (w, hover_message.get_height() + 10), pygame.SRCALPHA
            )
            self.hover_message.fill(WHITE_TRANSPARENT)
            self.hover_message.blit(hover_message, (5, 5))
            if self.hover_message_image:
                self.hover_message.blit(
                    self.hover_message_image,
                    (hover_message.get_width() + 10, 8),
                )

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            if self.rect.collidepoint(pos):
                self.image = self.clicked_image
                if self.button_sound:
                    pygame.mixer.Sound.play(self.button_sound)
                self.button_down = True
        elif event.type == pygame.MOUSEBUTTONUP:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            # If the rect collides with the mouse pos.
            if self.rect.collidepoint(pos) and self.button_down:
                for callback in self.callbacks:
                    if self.callback_var:
                        callback(self.callback_var)
                    else:
                        callback()
                self.image = self.hover_image
            self.button_down = False
        elif event.type == pygame.MOUSEMOTION:
            pos = (
                event.pos[0] - self.offset[0],
                event.pos[1] - self.offset[1],
            )
            collided = self.rect.collidepoint(pos)
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
        screen.blit(self.image, (self.rect[0], self.rect[1]))

    def set_pos(self, pos):
        self.x = pos[0]
        self.y = pos[1]


class ToggleButton(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callback,
            font=None,
            text="",
            button_color=WHITE_TRANSPARENT,
            text_color=BLACK,
            image=None,
            border_w=None,
            border_radius=None,
            pressed=False,
            fixed=False,
            vertical=False,
            cross=False,
            cross_size=None
    ):
        super().__init__()
        self.fixed = fixed
        self.border_w = 5 if not border_w else border_w
        self.border_radius = 0 if not border_radius else border_radius
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)

        pygame.draw.rect(
            self.button_image,
            button_color,
            self.button_image.get_rect(),
            border_radius=self.border_radius
        )
        pygame.draw.rect(
            self.hover_image,
            button_color,
            self.hover_image.get_rect(),
            border_radius=self.border_radius
        )
        pygame.draw.rect(
            self.clicked_image,
            button_color,
            self.clicked_image.get_rect(),
            border_radius=self.border_radius
        )

        if image:
            image_x = w / 2 - image.get_width() / 2
            image_y = h / 2 - image.get_height() / 2
            self.button_image.blit(image.copy(), (image_x, image_y))
            self.hover_image.blit(image.copy(), (image_x, image_y))
            self.clicked_image.blit(image.copy(), (image_x, image_y))

        pygame.draw.rect(
            self.hover_image,
            WHITE_TRANSPARENT,
            self.hover_image.get_rect(),
            self.border_w,
            border_radius=self.border_radius
        )
        if cross:
            if not cross_size:
                cross_size = (0, 0, w, h)

            pygame.draw.line(
                self.clicked_image, WHITE, (cross_size[0], cross_size[1]), (cross_size[2], cross_size[3]), self.border_w
            )
            pygame.draw.line(
                self.clicked_image, WHITE, (cross_size[0], cross_size[2]), (cross_size[2], cross_size[1]), self.border_w
            )
        else:
            pygame.draw.rect(
                self.clicked_image,
                WHITE,
                self.clicked_image.get_rect(),
                self.border_w,
            )

        if text and font:
            text_surf = font.render(text, True, text_color)
            if vertical:
                text_surf = pygame.transform.rotate(text_surf, 90)
            self.button_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.hover_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.clicked_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callback = callback
        self.button_down = False
        if pressed:
            self.image = self.clicked_image
            self.button_down = True
            if self.callback:
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
                    if self.callback:
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

    def draw(self, screen):
        screen.blit(self.image, (self.rect[0], self.rect[1]))


# image size has to be = w,h
class RadioButton(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callbacks,
            font=None,
            text="",
            button_color=WHITE_TRANSPARENT,
            text_color=BLACK,
            image=None,
            border_w=None,
            target=None,
            callback_var=None,
            border_radius=0,
    ):
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
            pygame.draw.rect(
                self.button_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            pygame.draw.rect(
                self.hover_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            pygame.draw.rect(
                self.clicked_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            # self.button_image.fill(button_color)
            # self.hover_image.fill(button_color)
            # self.clicked_image.fill(button_color)
        pygame.draw.rect(
            self.hover_image,
            WHITE_TRANSPARENT,
            self.hover_image.get_rect(),
            self.border_w,
            border_radius=border_radius,
        )
        pygame.draw.rect(
            self.clicked_image,
            WHITE,
            self.clicked_image.get_rect(),
            self.border_w,
            border_radius=border_radius,
        )
        if text and font:
            text_surf = font.render(text, True, text_color)
            self.button_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.hover_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
            self.clicked_image.blit(
                text_surf, text_surf.get_rect(center=(w // 2, h // 2))
            )
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


# image size has to be = w,h
class DoubleRadioButton(pygame.sprite.Sprite):
    def __init__(
            self,
            x,
            y,
            w,
            h,
            callbacks,
            button_color=WHITE_TRANSPARENT,
            border_w=None,
            callback_var=None,
            border_radius=0,
            preset=None,
    ):
        super().__init__()
        self.w = w
        self.h = h
        self.button_color = button_color
        self.callback_var = callback_var
        self.border_radius = border_radius
        self.border_w = 2 if not border_w else border_w
        self.button_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.hover_selected_image = pygame.Surface((w, h), pygame.SRCALPHA)
        if preset:
            self.generate_image_from_preset(preset)
        else:
            pygame.draw.rect(
                self.button_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            pygame.draw.rect(
                self.hover_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            pygame.draw.rect(
                self.clicked_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            pygame.draw.rect(
                self.hover_selected_image,
                button_color,
                (0, 0, w, h),
                border_radius=border_radius,
            )
            # self.button_image.fill(button_color)
            # self.hover_image.fill(button_color)
            # self.clicked_image.fill(button_color)
        pygame.draw.rect(
            self.hover_image,
            WHITE,
            self.hover_image.get_rect(),
            self.border_w,
            border_radius=border_radius,
        )
        pygame.draw.rect(
            self.clicked_image,
            WHITE,
            self.clicked_image.get_rect(),
            self.border_w,
            border_radius=border_radius,
        )
        pygame.draw.rect(
            self.hover_selected_image,
            config.GREEN,
            self.clicked_image.get_rect(),
            self.border_w,
            border_radius=self.border_radius,
        )

        self.image = self.button_image
        self.rect = pygame.Rect(x, y, w, h)
        # This function will be called when the button gets pressed.
        self.callbacks = callbacks
        self.button_down = False

    def setRadioButtons(self, buttons):
        self.buttons = buttons

    def generate_image_from_preset(self, preset):
        self.button_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.hover_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.clicked_image = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        self.hover_selected_image = pygame.Surface(
            (self.w, self.h), pygame.SRCALPHA
        )

        pygame.draw.rect(
            self.button_image,
            self.button_color,
            (0, 0, self.w, self.h),
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            self.hover_image,
            self.button_color,
            (0, 0, self.w, self.h),
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            self.clicked_image,
            self.button_color,
            (0, 0, self.w, self.h),
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            self.hover_selected_image,
            self.button_color,
            (0, 0, self.w, self.h),
            border_radius=self.border_radius,
        )

        line_width = self.w / 4

        leaf_height = preset["leaf_slider"] / 100
        stem_height = preset["stem_slider"] / 100
        root_height = preset["root_slider"] / 100
        starch_height = preset["starch_slider"] / 100

        images = [
            self.button_image,
            self.hover_image,
            self.clicked_image,
            self.hover_selected_image,
        ]

        h = self.h * 0.8
        margin = self.h * 0.1

        for i in range(0, len(images)):
            pygame.draw.line(
                images[i],
                (255, 255, 255),
                (0 * line_width, self.h - h * leaf_height - margin),
                (1 * line_width, self.h - h * leaf_height - margin),
                4,
            )
            pygame.draw.line(
                images[i],
                (255, 255, 255),
                (1 * line_width, self.h - h * stem_height - margin),
                (2 * line_width, self.h - h * stem_height - margin),
                4,
            )
            pygame.draw.line(
                images[i],
                (255, 255, 255),
                (2 * line_width, self.h - h * root_height - margin),
                (3 * line_width, self.h - h * root_height - margin),
                4,
            )
            pygame.draw.line(
                images[i],
                (255, 255, 255),
                (3 * line_width, self.h - h * starch_height - margin),
                (4 * line_width, self.h - h * starch_height - margin),
                4,
            )

        pygame.draw.rect(
            self.hover_image,
            WHITE,
            self.hover_image.get_rect(),
            self.border_w,
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            self.clicked_image,
            WHITE,
            self.clicked_image.get_rect(),
            self.border_w,
            border_radius=self.border_radius,
        )
        pygame.draw.rect(
            self.hover_selected_image,
            config.GREEN,
            self.clicked_image.get_rect(),
            self.border_w,
            border_radius=self.border_radius,
        )

    def handle_event(self, event):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover and event.button == 1:
                if self.button_down == True:
                    preset = self.callbacks[1](self.callback_var)
                    self.generate_image_from_preset(preset)
                else:
                    if self.callback_var is not None:
                        self.callbacks[0](self.callback_var)
                    else:
                        self.callbacks[0]()

                if self.buttons:
                    for rb in self.buttons:
                        rb.button_down = False
                self.button_down = True
        self.image = self.button_image
        if self.button_down:
            self.image = self.clicked_image
        if hover:
            if self.button_down:
                self.image = self.hover_selected_image
            else:
                self.image = self.hover_image


class OptionBox:
    def __init__(
            self, x, y, w, h, color, highlight_color, font, option_list, selected=0
    ):
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
        pygame.draw.rect(
            surf,
            self.highlight_color if self.menu_active else self.color,
            self.rect,
        )
        pygame.draw.rect(surf, (0, 0, 0), self.rect, 2)
        msg = self.font.render(self.option_list[self.selected], 1, (0, 0, 0))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.option_list):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(
                    surf,
                    self.highlight_color
                    if i == self.active_option
                    else self.color,
                    rect,
                )
                msg = self.font.render(text, 1, (0, 0, 0))
                surf.blit(msg, msg.get_rect(center=rect.center))
            outer_rect = (
                self.rect.x,
                self.rect.y + self.rect.height,
                self.rect.width,
                self.rect.height * len(self.option_list),
            )
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
class Slider:
    def __init__(
            self,
            rect,
            font,
            slider_size,
            organ=None,
            plant=None,
            color=None,
            slider_color=None,
            callback=None,
            percent=0,
            active=True,
            visible=True,
    ):
        super().__init__()
        self.color = color if color else (255, 255, 255, 128)
        self.slider_color = (
            slider_color
            if slider_color
            else (self.color[0], self.color[1], self.color[2])
        )
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
        if self.plant is not None:
            if self.plant.get_biomass() > self.plant.seedling.max:
                self.active = True
        """if self.organ is not None:
            if self.organ.active:
                self.active = True
        #whats that?
        if not self.active:
            return"""

    def get_percentage(self):
        line_height = self.h - self.slider_h
        slider_length = self.slider_y
        percent = slider_length / line_height * 100
        return 100 - percent

    def get_slider_rect_global(self):
        return pygame.Rect(
            self.x, self.y + self.slider_y, self.slider_w, self.slider_h
        )

    def get_slider_rect_local(self):
        return pygame.Rect(0, self.slider_y, self.slider_w, self.slider_h)

    def set_percentage(self, percent):
        line_height = self.h - self.slider_h
        slider_length = (100 - percent) * line_height / 100
        self.slider_y = slider_length
        if self.organ:
            self.organ.percentage = self.get_percentage()

    def sub_percentage(self, percent):
        delta = self.get_percentage() - percent
        if delta < 0:
            self.set_percentage(0)
            return delta
        elif delta > 100:
            self.set_percentage(100)
            return delta - 100
        else:
            self.set_percentage(delta)
            return 0

    def draw(self, screen):
        if not self.visible:
            return
        slider_color = (
            self.slider_color if self.active else (150, 150, 150, 128)
        )
        w = self.w if self.w >= self.slider_w else self.slider_w
        border = pygame.Surface((w, self.h), pygame.SRCALPHA)
        # line
        pygame.draw.rect(
            border,
            self.color,
            (
                w / 2 - self.w / 2,
                self.slider_h / 2,
                self.w,
                self.h - self.slider_h,
            ),
        )

        # draw slider
        pygame.draw.rect(border, slider_color, self.get_slider_rect_local())
        msg = self.font.render(
            "{:02.0f}".format(self.get_percentage()), 1, (0, 0, 0)
        )
        border.blit(
            msg, msg.get_rect(center=self.get_slider_rect_local().center)
        )
        screen.blit(border, (self.x, self.y))

    def handle_event(self, event):
        if not self.active:
            return
        rect = self.get_slider_rect_global()
        hover = rect.collidepoint(pygame.mouse.get_pos())

        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover and event.button == 1:
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
                self.slider_y = (
                        clamp(
                            pygame.mouse.get_pos()[1],
                            self.y,
                            self.y - self.slider_h + self.h,
                        )
                        - self.y
                )


class NegativeSlider:
    def __init__(
            self,
            rect,
            font,
            slider_size,
            organ=None,
            plant=None,
            color=None,
            slider_color=None,
            callback=None,
            percent=0,
            active=True,
            visible=True,
    ):
        super().__init__()
        self.color = color if color else (255, 255, 255, 128)
        self.slider_color = (
            slider_color
            if slider_color
            else (self.color[0], self.color[1], self.color[2])
        )
        self.drag = False
        self.font = font
        self.visible = visible
        self.active = active
        self.organ = organ
        self.callback = callback
        self.plant = plant
        self.x, self.y, self.w, self.h = rect
        self.slider_y = 100
        self.slider_w = slider_size[0] if slider_size else self.w
        self.slider_h = slider_size[1] if slider_size else self.w
        self.rect = rect
        self.set_percentage(percent)

    def update(self):
        if self.plant is not None:
            if self.plant.get_biomass() > self.plant.seedling.max:
                self.active = True

    def get_percentage(self):
        line_height = self.h - self.slider_h
        slider_length = self.slider_y
        percent = slider_length / line_height * 100
        return (50 - percent) * 2

    def get_slider_rect_global(self):
        return pygame.Rect(
            self.x, self.y + self.slider_y, self.slider_w, self.slider_h
        )

    def get_slider_rect_local(self):
        return pygame.Rect(0, self.slider_y, self.slider_w, self.slider_h)

    def set_percentage(self, percent):
        line_height = self.h - self.slider_h
        slider_length = (100 - percent) * line_height / 100
        self.slider_y = slider_length
        if self.organ:
            self.organ.set_percentage(self.get_percentage())

    # can subtract negative numbers -> add
    def sub_percentage(self, percent):
        if self.get_percentage() < 0:
            return - percent
        # slider is in positive area
        delta = self.get_percentage() - percent
        if delta < 0:
            self.set_percentage(50)
            return delta
        elif delta > 100:
            self.set_percentage(100)
            return delta - 100
        else:
            # delta 0 .. 100 -> 50 .. 100
            self.set_percentage((delta / 2) + 50)
            return 0

    def draw(self, screen):
        if not self.visible:
            return
        slider_color = (
            self.slider_color if self.active else (150, 150, 150, 128)
        )
        w = self.w if self.w >= self.slider_w else self.slider_w
        border = pygame.Surface((w, self.h), pygame.SRCALPHA)
        # line
        pygame.draw.rect(
            border,
            self.color,
            (
                w / 2 - self.w / 2,
                self.slider_h / 2,
                self.w,
                self.h - self.slider_h,
            ),
        )

        # show zero
        pygame.draw.line(
            border,
            config.GRAY,
            (0, self.h / 2),
            (self.slider_w, self.h / 2),
            width=2,
        )

        # draw slider
        pygame.draw.rect(border, slider_color, self.get_slider_rect_local())
        msg = self.font.render(
            "{:02.0f}".format(abs(self.get_percentage())), 1, (0, 0, 0)
        )
        border.blit(
            msg, msg.get_rect(center=self.get_slider_rect_local().center)
        )
        screen.blit(border, (self.x, self.y))

    def handle_event(self, event):
        if not self.active:
            return
        rect = self.get_slider_rect_global()
        hover = rect.collidepoint(pygame.mouse.get_pos())

        if event.type == pygame.MOUSEBUTTONDOWN:
            if hover and event.button == 1:
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
                self.slider_y = (
                        clamp(
                            pygame.mouse.get_pos()[1],
                            self.y,
                            self.y - self.slider_h + self.h,
                        )
                        - self.y
                )


class SliderGroup:
    def __init__(self, sliders, max_sum):
        self.sliders = sliders
        self.sliders_zero = []
        self.max_sum = max_sum

        for slider in self.sliders:
            slider.callback = self.change_percentage
            # slider.set_percentage(self.max_sum/len(self.sliders))

    def slider_sum(self):
        sum = 0
        for slider in self.sliders:
            percent = slider.get_percentage()
            # percent = percent if percent > 0 else 0
            percent = 0 if percent < 0 else percent
            sum += percent
        return sum
        # return sum([slider.get_percentage() for slider in self.sliders])

    def change_percentage(self, slider_changed: Slider):
        tries: int = 100
        delta: float = self.max_sum - self.slider_sum()
        # negative delta -> one slider has gone up, others must be lowered
        available_sliders: list[Slider] = [slider for slider in self.sliders]
        available_sliders.remove(slider_changed)

        while not -0.1 < delta < 0.1:
            if len(available_sliders) <= 0:
                break
            if tries <= 0:
                break
            delta_each_slider = delta / len(available_sliders)
            for slider in available_sliders:
                # excess will be negative
                # weird to sub a negative negative -> add?
                excess = slider.sub_percentage(-delta_each_slider)
                delta -= (delta_each_slider - excess)
                if excess != 0:
                    available_sliders.remove(slider)
            tries = tries - 1


'''


        # @slider: slider that changed
        while (
            self.max_sum < self.slider_sum() - 0.1
            or self.max_sum > self.slider_sum() + 1
        ):
            # special case, if max is smaller than 100%
            if slider.get_percentage() > self.max_sum:
                slider.set_percentage(self.max_sum)
            # slider that called and zero sliders aren't able to reduce --> available_sliders
            available_sliders = (
                len(self.sliders) - len(self.sliders_zero)
            ) - 1
            delta = (self.slider_sum() - self.max_sum) / (available_sliders)
            for s in self.sliders:
                if s == slider or s in self.sliders_zero:
                    pass
                else:
                    # extra: extra = s.get_percentage() - delta
                    extra = s.sub_percentage(delta)
                    if extra > 0:
                        self.sliders_zero.append(s)
'''


class Textbox:
    def __init__(
            self,
            x,
            y,
            w,
            h,
            font,
            text="name",
            background_color=(240, 240, 240, 180),
            highlight_color=(255, 255, 255),
            textcolor=(0, 0, 0),
    ):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.textcolor = textcolor
        self.render_text = self.font.render(self.text, True, self.textcolor)
        self.cursor = self.font.render("I", True, self.textcolor)
        self.background_color = background_color
        self.higlight_color = highlight_color
        self.active = False
        self.hover = False
        self.max_chars = 10
        self.cursor_timer = 0
        self.max_cursor_timer = 60

    def handle_event(self, e):
        if e.type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(e.pos):
                self.hover = True
            else:
                self.hover = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(e.pos):
                self.active = True
            else:
                self.active = False
        if not self.active:
            return
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN:
                self.active = False
                return
            if e.key == pygame.K_BACKSPACE:
                if len(self.text) > 0:
                    self.text = self.text[:-1]
            else:
                if len(self.text) < self.max_chars:
                    self.text += e.unicode
        self.render_text = self.font.render(self.text, True, self.textcolor)

    def update(self, dt):
        if self.active:
            self.cursor_timer += 1
            if self.cursor_timer == self.max_cursor_timer:
                self.cursor_timer = 0

    def draw(self, screen):
        pygame.draw.rect(
            screen, self.background_color, self.rect, border_radius=3
        )

        # pygame.draw.rect(screen, self.border_color, self.rect, border_radius=3, width=3)
        screen.blit(
            self.render_text,
            (
                self.x + self.w / 2 - self.render_text.get_width() / 2,
                self.y + self.h / 2 - self.render_text.get_height() / 2,
            ),
        )
        if self.active:
            if self.cursor_timer > self.max_cursor_timer / 2:
                screen.blit(
                    self.cursor,
                    (
                        self.x
                        + self.w / 2
                        + self.render_text.get_width() / 2
                        + 1,
                        self.y
                        + self.h / 2
                        - self.render_text.get_height() / 2,
                    ),
                )
            pygame.draw.line(
                screen,
                self.higlight_color,
                (self.rect[0], self.rect[1] + self.rect[3]),
                (self.rect[0] + self.rect[2], self.rect[1] + self.rect[3]),
                width=3,
            )

        elif self.hover:
            pygame.draw.line(
                screen,
                self.higlight_color,
                (self.rect[0], self.rect[1] + self.rect[3]),
                (self.rect[0] + self.rect[2], self.rect[1] + self.rect[3]),
                width=3,
            )


class ButtonArray:
    def __init__(
            self,
            rect,
            amount,
            resolution,
            margin,
            callback,
            set_hover_message,
            border_w=5,
            pressed=False,
            start_color=None,
            end_color=None,
            select_sound=None,
    ):
        self.toggle_buttons = []
        self.callback = callback
        self.set_hover_message = set_hover_message
        self.hours = 0
        self.color = config.RED
        self.border_w = border_w
        self.label = config.BIG_FONT.render("Stomata:", True, config.BLACK)
        self.hover_message = "Select wich hours to open or close the plants stomata. *Hot days increase transpiration. Try closing them to save water"
        self.gradient = None
        if start_color and end_color:
            gradient_early = self.get_color_gradient(end_color, start_color, int(amount / 2))
            gradient_late = self.get_color_gradient(start_color, end_color, int((amount / 2) + 0.5))
            self.gradient = gradient_early + gradient_late
        set_all_width = 50

        self.rect = pygame.Rect(
            rect[0],
            rect[1],
            (rect[2] + margin) * amount - margin + set_all_width + margin,
            rect[3] + 60,
        )

        self.set_all_button = Button(
            rect[0],
            rect[1] + 50,
            set_all_width,
            30,
            [select_sound, self.toggle_all],
            config.FONT,
            "All",
            hover_message="Activate/Deactivate all buttons",
            border_w=border_w,
        )

        for i in range(0, amount):
            color = config.WHITE_TRANSPARENT
            if self.gradient:
                color = self.gradient[i]
            self.toggle_buttons.append(
                ToggleButton(
                    rect[0] + i * (rect[2] + margin) + set_all_width + margin,
                    rect[1] + 50,
                    rect[2],
                    rect[3],
                    [],
                    font=config.FONT,
                    button_color=color,
                    text="{}".format(i * resolution),
                    pressed=pressed,
                    border_w=border_w,
                )
            )

            # self, x, y, w, h, callback, font=None, text='', button_color=WHITE_TRANSPARENT, text_color=BLACK,
            # image=None, border_w=None, pressed=False, fixed=False, vertical=False, cross=False):

    def update(self, hours):
        self.hours = hours

    def handle_event(self, e):
        self.set_all_button.handle_event(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                for button in self.toggle_buttons:
                    button.handle_event(e)
                self.callback(self.get_bool_list())
        if e.type == pygame.MOUSEMOTION:
            pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                for button in self.toggle_buttons:
                    button.handle_event(e)
                self.set_hover_message(self.hover_message)

    def toggle_all(self):
        sum_true = 0
        for bool in self.get_bool_list():
            if bool:
                sum_true += 1
        if len(self.toggle_buttons) / 2 > sum_true:
            for button in self.toggle_buttons:
                button.activate()
            # self.go_green()
        else:
            for button in self.toggle_buttons:
                button.deactivate()
            # self.go_red()
        self.callback(self.get_bool_list())

    def get_bool_list(self):
        return [
            True if button.button_down else False
            for button in self.toggle_buttons
        ]

    def press_all(self):
        for button in self.toggle_buttons:
            button.pressed = True

    def go_green(self):
        self.color = config.GREEN

    def go_red(self):
        self.color = config.RED

    def get_rect(self):
        return self.rect

    def get_color_gradient(self, start_color, end_color, iterations):
        r_delta = (start_color[0] - end_color[0]) / iterations
        g_delta = (start_color[1] - end_color[1]) / iterations
        b_delta = (start_color[2] - end_color[2]) / iterations

        gradient = []
        for i in range(iterations):
            gradient.append((
                start_color[0] - r_delta * i,
                start_color[1] - g_delta * i,
                start_color[2] - b_delta * i))
        return gradient

    def draw(self, screen):
        # pygame.draw.rect(screen, config.WHITE_TRANSPARENT, self.rect)
        pygame.draw.rect(
            screen,
            self.color,
            (
                (self.rect[2] - 50) / 24 * self.hours + self.rect[0] + 50,
                self.rect[1] + 32 + 50,
                10,
                10,
            ),
            border_radius=5,
        )
        pygame.draw.rect(
            screen,
            config.WHITE,
            (self.rect[0], self.rect[1], 470, 40),
            border_radius=3,
        )
        if self.color == config.GREEN:
            open_closed = config.BIG_FONT.render("Open", True, self.color)
        else:
            open_closed = config.BIG_FONT.render("Closed", True, self.color)
        screen.blit(self.label, (self.rect[0] + 5, self.rect[1] + 5))
        screen.blit(open_closed, (self.rect[0] + 120, self.rect[1] + 5))
        self.set_all_button.draw(screen)
        for button in self.toggle_buttons:
            button.draw(screen)
