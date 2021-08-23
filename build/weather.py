import pygame
from pygame.locals import *
from particle import ParticleSystem, StillParticles
from animation import OneShotAnimation, Animation
import numpy as np
import gradient
import random

SUN = 0
RAIN = 1
CLOUD = 2

color = (0, 0, 0)
orange = (137, 77, 0)
blue = (118, 231, 255)

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Environment can be altered by 4 different events: Sun, Rain, Cloud, Wind
# altering: Temp, H2O, N, Photon_level
# caused by: time
# draw: background, clouds, sun, moon, wind, birds, rain
gust = [pygame.transform.scale(pygame.image.load("../assets/wind/gust_{}.png".format(i)),(960,540)) for i in range(0,5)]



class Environment:
    def __init__(self, get_image, SCREEN_WIDTH, SCREEN_HEIGHT, plant, model, nitrate, water):
        self.w = SCREEN_WIDTH
        self.model = model
        self.background = pygame.transform.scale(get_image("background_empty_sky.png"), (SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
        self.h = SCREEN_HEIGHT
        self.sun_pos_noon = (1300,0)
        self.sun_pos_night = (500,SCREEN_HEIGHT-200)
        self.sun_pos = (0,0)
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.plant = plant
        self.sprites = pygame.sprite.Group()
        self.animations = []
        self.state = SUN # mask for weather 0sun,1rain,2cloud
        self.star_pos_size = [((random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT/2)), random.randint(0,10)) for i in range(0,50)]

        # init drop sprites
        drops = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop{}.png".format(i)).convert_alpha(), (20, 20)) for i in range(0, 3)]
        splash = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop_splash{}.png".format(i)).convert_alpha(), (20, 20)) for i in range(0, 4)]
        self.sun = [pygame.transform.scale(pygame.image.load("../assets/sun/sun_face_{}.png".format(i)), (512, 512)).convert_alpha() for i in range(0, 5)]

        self.rain = ParticleSystem(100, spawn_box=Rect(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH/3*2, 0),
                                    boundary_box=Rect(SCREEN_WIDTH/3,0,SCREEN_WIDTH/3*2,SCREEN_HEIGHT-250),
                                    color=(0,0,100), apply_gravity=True, speed=[0, 8],
                                    active=False, images=drops, despawn_images=splash, despawn_animation=self.add_animation)

        self.nitrate = StillParticles(100, spawn_box=Rect(1200,900,400,190),
                                    boundary_box=Rect(1200,900,400,190),
                                    color=(0,0,0), speed=[0, 0], callback=self.model.get_nitrate_pool,
                                    active=True, size=5, once=True)
        self.blow_wind()


    def update(self, dt):
        for animation in self.animations:
            animation.update()
        #self.rain.update(dt)
        self.nitrate.update(dt)
        for sprite in self.sprites:
            # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite) # dumb to remove during iteration, maybe don't

        if self.state == SUN:
            sun_intensity = self.get_sun_intensity()
            x = (self.sun_pos_night[0] + (self.sun_pos_noon[0]-self.sun_pos_night[0])*sun_intensity)
            y = (self.sun_pos_night[1] + (self.sun_pos_noon[1]-self.sun_pos_night[1])*sun_intensity)
            self.sun_pos = (x,y)


    def draw_background(self, screen):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        # sun-->Photon_intensity, moon, water_lvl
        sun_intensity = self.get_sun_intensity()
        if sun_intensity > 0:
            color = gradient.get_color(orange, blue, sun_intensity)
            if self.state == SUN:
                # sun_intensity 0, 1 -->

                sun_index = min(max(int(self.get_sun_intensity() * len(self.sun)),0),4)
                s.blit(self.sun[sun_index], self.sun_pos)
        else:
            color= gradient.get_color(orange, (0,0,0), abs(sun_intensity))

            for pos in self.star_pos_size:
                pygame.draw.circle(s, (255,255,255, abs(sun_intensity)*128), pos[0], pos[1])
                pygame.draw.circle(s, (255,255,255, abs(sun_intensity)*180), pos[0], max(pos[1]-5,0))
        screen.fill(color)
        #for animation in self.animations:
        #    s.blit(animation.image, animation.pos)
        screen.blit(s, (0, 0))
        screen.blit(self.background, (0, 0))


    def draw_foreground(self, screen):
        self.draw_clock(screen)
        self.rain.draw(screen)
        self.nitrate.draw(screen)
        self.sprites.draw(screen)

    def activate_rain(self):
        self.state = 1
        self.rain.activate()

    def deactivate_rain(self):
        self.rain.deactivate()

    def activate_clouds(self):
        self.state = 2
        pass

    def deactivate_clouds(self):
        pass

    def activate_sun(self):
        self.state = 0
        pass

    def deactivate_sun(self):
        pass

    def blow_wind(self):
        pass
        #self.animations.append(Animation(gust, 2000, (500,400)))
        #decrease temp
        # wind animation

    # on event
    # deactivate all -> acitvate selected filter
    #
    def handle_weather_event(self):
        pass

    def get_day_time(self):
        ticks = pygame.time.get_ticks()
        day = 1000*60*6
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

        day_time = self.get_sun_intensity()
        sun_intensity = self.sfont.render("{:.2}".format(day_time), True, (0, 0, 0))
        screen.blit(sun_intensity, sun_intensity.get_rect(center=(self.w / 2 + 100, 20)))


    def get_sun_intensity(self):
        return -(np.sin(np.pi/2-np.pi/5+((pygame.time.get_ticks()/(1000 * 60 * 6)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))
