import pygame
from pygame.locals import *
from utils.particle import ParticleSystem, StillParticles
from utils.animation import OneShotAnimation, Animation
import numpy as np
import random
import config
from data import assets
from utils.spline import Beziere

SUN = 0
RAIN = 1
CLOUD = 2
WIND = 3
HAWK = 4

color = (0, 0, 0)
orange = (137, 77, 0)
blue = (118, 231, 255)

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Environment can be altered by 4 different events: Sun, Rain, Cloud, Wind
# altering: Temp, H2O, N, Photon_level
# caused by: time
# draw: background, clouds, sun, moon, wind, birds, rain
#gust = [pygame.transform.scale(pygame.image.load("../assets/wind/gust_{}.png".format(i)),(960,540)) for i in range(0,5)]
rain_sound = assets.sfx("rain/rain_sound.mp3")
rain_sound.set_volume(0.05)



class Environment:
    def __init__(self, plant, model, nitrate, water, gametime, activate_hawk=None):
        self.s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.w = SCREEN_WIDTH
        self.model = model
        self.gametime = gametime
        self.background = assets.img("soil.png").convert_alpha()
        #self.background_moist = pygame.transform.scale(assets.img("background_moist.png"), (SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
        self.h = SCREEN_HEIGHT
        self.sun_pos_spline = Beziere([(-100,800),(960,-200),(2020,800)])
        self.rain_rate = 0.0003
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.plant = plant
        self.wind_force = (0,0)
        self.wind_duration = 0 # at 60fps
        self.draw = True
        self.activate_hawk = activate_hawk
        self.sprites = pygame.sprite.Group()
        self.animations = []
        self.weather_events = []
        self.state = SUN # mask for weather 0sun,1rain,2cloud
        self.star_pos_size = [((random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT/2)), random.randint(0,10)) for i in range(0,50)]

        # init drop sprites
        #drops = [pygame.transform.scale(assets.img("rain/raindrop{}.png".format(i)), (16, 16)) for i in range(0, 3)]
        #splash = [pygame.transform.scale(assets.img("rain/raindrop_splash{}.png".format(i)), (16, 16)) for i in range(0, 4)]
        self.sun = assets.img("sun/sun.png", (256, 256))
        self.cloud = pygame.transform.scale(assets.img("cloud.png"), (420, 240)).convert_alpha()
        self.cloud_dark = pygame.transform.scale(assets.img("cloud_dark.png"), (420, 240)).convert_alpha()
        '''self.rain = ParticleSystem(50, spawn_box=Rect(SCREEN_WIDTH / 2-150, 100, 300, 30),
                                    boundary_box=Rect(SCREEN_WIDTH/2-150,0,300,SCREEN_HEIGHT-250),
                                    color=(0,0,100), apply_gravity=True, speed=[0, 180],
                                    active=False, images=drops, despawn_images=splash, despawn_animation=self.add_animation)'''
        self.rain = ParticleSystem(100, spawn_box=Rect(SCREEN_WIDTH/2-110, 110,
                                                      220, 20),
                                   boundary_box=Rect(SCREEN_WIDTH/2-self.cloud.get_width()/2-80, 20,
                                                     160,SCREEN_HEIGHT-250),
                                size=8, color=config.BLUE, apply_gravity=False,
                                   speed=[0, 150], spread=[0, 0], active=False, rectangle=True)

        self.nitrate = StillParticles(80, spawn_box=Rect(self.w/2-400,950,800,300),
                                    boundary_box=Rect(1200,900,400,300),
                                    color=(0,0,0), speed=[0, 0], callback=self.model.get_nitrate_percentage,
                                    active=True, size=4, once=True)
        self.weather_events = config.e


    def update(self, dt):
        #self.sun_pos_spline.update(dt)
        for animation in self.animations:
            animation.update()
        self.handle_weather_events()
        self.rain.update(dt)
        self.nitrate.update(dt)
        if self.rain.active:
            self.model.water_pool += self.rain_rate * self.gametime.GAMESPEED
        for sprite in self.sprites:
            # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite) # dumb to remove during iteration, maybe don't

        sun_intensity = self.get_sun_intensity()
        #x = (self.sun_pos_night[0] + (self.sun_pos_noon[0] - self.sun_pos_night[0]) * sun_intensity)
        #y = (self.sun_pos_night[1] + (self.sun_pos_noon[1] - self.sun_pos_night[1]) * sun_intensity)
        #self.sun_pos = (x, y)

    def draw_background(self, screen):
        #if self.draw:
        #    self.draw = False
        #    return
        #self.draw = True
        # sun-->Photon_intensity, moon, water_lvl

        sun_intensity = self.get_sun_intensity()

        if sun_intensity > 0:
            color = self.get_color(orange, blue, sun_intensity)
        else:
            color = self.get_color(orange, (0, 0, 0), abs(sun_intensity))

            for pos in self.star_pos_size:
                pygame.draw.circle(self.s, (255, 255, 255, abs(sun_intensity) * 128), pos[0], pos[1])
                pygame.draw.circle(self.s, (255, 255, 255, abs(sun_intensity) * 180), pos[0], max(pos[1] - 5, 0))
        self.s.fill(color)

        # self.sun_pos_spline.draw(s)
        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            sunpos = self.sun_pos_spline.get_point(day_time)
            sunpos = (sunpos[0] - self.sun.get_width() / 2, sunpos[1] - self.sun.get_height() / 2)
            self.s.blit(self.sun, sunpos)

        '''if sun_intensity > 0:
            color = self.get_color(orange, blue, sun_intensity)
            # sun_intensity 0, 1 -->
            sun_index = min(max(int(self.get_sun_intensity() * len(self.sun)), 0), 4)
            s.blit(self.sun[sun_index], self.sun_pos)

        else:
            color= self.get_color(orange, (0,0,0), abs(sun_intensity))

            for pos in self.star_pos_size:
                pygame.draw.circle(s, (255,255,255, abs(sun_intensity)*128), pos[0], pos[1])
                pygame.draw.circle(s, (255,255,255, abs(sun_intensity)*180), pos[0], max(pos[1]-5,0))
        '''
        if self.state == CLOUD:
            self.s.blit(self.cloud, (960-self.cloud.get_width()/2, 50))
        if self.state == RAIN:
            self.s.blit(self.cloud_dark, (960-self.cloud_dark.get_width()/2, 50))



        #for animation in self.animations:
        #    s.blit(animation.image, animation.pos)
        screen.blit(self.s, (0, 0))
        screen.blit(self.background, (0,-140))

        #if self.model.water_pool > 0:
        #    pygame.draw.circle(s, (50, 40, 20, min(int(self.model.water_pool / self.model.max_water_pool * 32), 255)),
        #                       (1430, 1000), min(1, self.model.water_pool / self.model.max_water_pool) * 40 + 70)
            # background_moist = self.background_moist.copy()
            # background_moist.set_alpha(int(self.model.water_pool/self.model.max_water_pool*255))
            # screen.blit(background_moist, (0,0))

    def get_color(self, color0, color1, grad):
        return (int(color0[0] * (1 - grad) + color1[0] * grad), int(color0[1] * (1 - grad) + color1[1] * grad),
                int(color0[2] * (1 - grad) + color1[2] * grad))

    def draw_foreground(self, screen):
        self.draw_clock(screen)
        self.rain.draw(screen)
        self.nitrate.draw(screen)
        self.sprites.draw(screen)

    def handle_weather_events(self):
        time = self.gametime.get_time()

        for event in self.weather_events:
            if event["start_time"] <= time:
                self.start_event(event)

    def start_event(self, event):
        self.state = event["type"]
        if self.state == RAIN:
            pygame.mixer.Sound.play(rain_sound, -1)
            self.rain.activate()
        elif self.state == SUN:
            pygame.mixer.Sound.stop(rain_sound)
            self.rain.deactivate()
        elif self.state == CLOUD:
            pygame.mixer.Sound.stop(rain_sound)
            self.rain.deactivate()
        elif self.state == HAWK:
            pass
            #self.activate_hawk()

        self.weather_events.remove(event)

    def get_day_time(self):
        ticks = self.gametime.get_time()
        day = 1000*60*6
        hour = day/24
        min = hour/60
        days = int(ticks/day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def draw_clock(self, screen):
        # clock
        days, hours, minutes = self.get_day_time()
        output_string = "Day {0} {1:02}:{2:02}".format(days, int(hours), int(minutes))
        clock_text = self.sfont.render(output_string, True, (0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255, 180), Rect(self.w/2-90, 10, 180, 30), border_radius=3)
        screen.blit(clock_text, clock_text.get_rect(center=(self.w / 2, 24)))
        # headbox

        '''
        day_time = self.get_sun_intensity()
        sun_intensity = self.sfont.render("{:.2}".format(day_time), True, (0, 0, 0))
        screen.blit(sun_intensity, sun_intensity.get_rect(center=(self.w / 2 + 150, 20)))
        '''

    def get_sun_intensity(self):
        return -(np.sin(np.pi/2-np.pi/5+((self.gametime.get_time()/(1000 * 60 * 6)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    def get_day_time_t(self):

        return ((((self.gametime.get_time()/1000/60/6)+0.5-0.333)%1)*2-1)

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))

