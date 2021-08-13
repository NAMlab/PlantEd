import pygame
from pygame.locals import *
from particle import ParticleSystem
from animation import OneShotAnimation
import numpy as np

SUN = USEREVENT + 1
RAIN = USEREVENT + 2
CLOUD = USEREVENT + 3
WIND = USEREVENT + 4

# Environment can be altered by 4 different events: Sun, Rain, Cloud, Wind
# altering: Temp, H2O, N, Photon_level
# caused by: time
# draw: background, clouds, sun, moon, wind, birds, rain


class Environment:
    def __init__(self, SCREEN_WIDTH, SCREEN_HEIGHT, plant, nitrate, water):
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.plant = plant
        self.sprites = pygame.sprite.Group()
        self.animations = []

        # init drop sprites
        drops = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop{}.png".format(i)).convert_alpha(), (20, 20)) for i in range(0, 3)]
        splash = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop_splash{}.png".format(i)).convert_alpha(), (20, 20)) for i in range(0, 4)]
        self.sun = [pygame.transform.scale(pygame.image.load("../assets/sun/sun_face_{}.png".format(i)), (512, 512)).convert_alpha() for i in range(0, 5)]

        self.rain = ParticleSystem(100, spawn_box=Rect(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH/3*2, 0),
                                    boundary_box=Rect(SCREEN_WIDTH/3,0,SCREEN_WIDTH/3*2,SCREEN_HEIGHT-250),
                                    color=(0,0,100), apply_gravity=True, speed=[0, 8],
                                    active=False, images=drops, despawn_images=splash, despawn_animation=self.add_animation)


    def update(self, dt):
        for animation in self.animations:
            animation.update()
        self.rain.update(dt)
        for sprite in self.sprites:
            # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite) # dumb to remove during iteration, maybe don't

    def draw_background(self, screen):
        # sun-->Photon_intensity, moon, water_lvl
        sun_index = min(int((self.get_sun_intensity()+1)/2*len(self.sun)),4)
        screen.blit(self.sun[sun_index], (self.w/4*3, 0))

    def draw_foreground(self, screen):
        self.draw_clock(screen)
        self.rain.draw(screen)
        self.sprites.draw(screen)

    def activate_rain(self):
        self.rain.deactivate()

    def get_day_time(self):
        ticks = pygame.time.get_ticks()
        day = 1000*60
        hour = day/24
        min = hour/60
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return hours, minutes

    '''def darken_display_daytime(self, screen):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        day_time = (((self.get_sun_intensity() + 1) / 2) * 128)
        return day_time'''

    def draw_clock(self, screen):
        # clock
        hours, minutes = self.get_day_time()
        output_string = "{0:02}:{1:02}".format(int(hours), int(minutes))
        clock_text = self.sfont.render(output_string, True, (0, 0, 0))
        screen.blit(clock_text, clock_text.get_rect(center=(self.w / 2, 20)))

        day_time = ((self.get_sun_intensity() + 1) / 2)
        sun_intensity = self.sfont.render("{:.2}".format(day_time), True, (0, 0, 0))
        screen.blit(sun_intensity, sun_intensity.get_rect(center=(self.w / 2 + 100, 20)))


    def get_sun_intensity(self):
        return (np.sin(np.pi/2-np.pi/5+((pygame.time.get_ticks()/(1000 * 60)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    def deactivate_rain(self):
        self.rain.deactivate()

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))
