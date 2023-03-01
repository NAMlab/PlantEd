import pygame
from pygame.locals import *

from client import Client
from utils.particle import StillParticles
from utils.animation import Animation
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
    def __init__(self, plant,client:Client, water_grid, nitrate, water, gametime, activate_hawk=None):
        self.s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.w = SCREEN_WIDTH
        self.season = config.spring
        self.water_grid = water_grid
        self.gametime = gametime
        self.background = assets.img("soil.PNG").convert_alpha()
        #self.background_moist = pygame.transform.scale(assets.img("background_moist.png"), (SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
        self.h = SCREEN_HEIGHT
        self.sun_pos_spline = Beziere([(-100,800),(960,-200),(2020,800)],res=10000).points_to_draw
        self.sunpos = (0,0)
        self.rain_rate = 0.0003
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.plant = plant
        self.client = client
        self.wind_force = (0,0)
        self.wind_duration = 0 # at 60fps
        self.draw = True
        self.raining = False
        self.activate_hawk = activate_hawk
        self.sprites = pygame.sprite.Group()
        rain_images = [assets.img("gif_rain/frame_{index}_delay-0.05s.png".format(index=i)) for i in range(0, 21)]
        self.animations = [Animation(rain_images,10,(480,0),running=False)]
        self.weather_events = []
        self.state = SUN # mask for weather 0sun,1rain,2cloud
        self.star_pos_size = [((random.randint(0,SCREEN_WIDTH), random.randint(0,SCREEN_HEIGHT/2)), random.randint(0,10)) for i in range(0,50)]

        # init drop sprites
        #drops = [pygame.transform.scale(assets.img("rain/raindrop{}.png".format(i)), (16, 16)) for i in range(0, 3)]
        #splash = [pygame.transform.scale(assets.img("rain/raindrop_splash{}.png".format(i)), (16, 16)) for i in range(0, 4)]
        self.sun = assets.img("sun/sun.PNG", (256, 256))
        self.cloud = assets.img("clouds/cloud_0.PNG", (402, 230))
        self.cloud_dark = assets.img("clouds/cloud_dark_0.PNG", (402, 230))
        '''self.rain = ParticleSystem(50, spawn_box=Rect(SCREEN_WIDTH / 2-150, 100, 300, 30),
                                    boundary_box=Rect(SCREEN_WIDTH/2-150,0,300,SCREEN_HEIGHT-250),
                                    color=(0,0,100), apply_gravity=True, speed=[0, 180],
                                    active=False, images=drops, despawn_images=splash, despawn_animation=self.add_animation)'''
        '''self.rain = ParticleSystem(100, spawn_box=Rect(SCREEN_WIDTH/2-110, 110,
                                                      220, 20),
                                   boundary_box=Rect(SCREEN_WIDTH/2-self.cloud.get_width()/2-80, 20,
                                                     160,SCREEN_HEIGHT-250),
                                size=8, color=config.BLUE, apply_gravity=False,
                                   speed=[0, 150], spread=[0, 0], active=False, rectangle=True)'''

        self.nitrate = StillParticles(10, spawn_box=Rect(0,950,1920,300),
                                      boundary_box=Rect(0,950,1920,300),
                                      color=(0,0,0),
                                      images=[assets.img("nitrogen.PNG", (20, 20))],
                                      speed=[0, 0],

                                      # ToDo callback really needed scales only the particles?
                                      callback=self.client.get_nitrate_percentage,
                                      active=True, size=4, factor=100, once=True)
        self.weather_events = config.e


    def update(self, dt):
        #self.sun_pos_spline.update(dt)
        for animation in self.animations:
            animation.update(dt)
        self.handle_weather_events()
        #self.rain.update(dt)
        self.nitrate.update(dt)
        for sprite in self.sprites:
            # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite) # dumb to remove during iteration, maybe don't

        day_time = self.get_day_time_t()
        if day_time > 0 and day_time < 1:
            self.sunpos = self.sun_pos_spline[(int(day_time * 10000) - 1)]
            self.plant.organs[1].sunpos = self.sunpos

        days, hours, minutes = self.get_day_time()


        # spring
        if days < config.MAX_DAYS/6:
            self.season = config.spring

        # summer
        elif days < config.MAX_DAYS/3*2:
            self.season = config.summer

        # fall
        elif days < config.MAX_DAYS:
            self.season = config.fall

        else:
            self.season = config.winter

        #sun_intensity = self.get_sun_intensity()
        #x = (self.sun_pos_night[0] + (self.sun_pos_noon[0] - self.sun_pos_night[0]) * sun_intensity)
        #y = (self.sun_pos_night[1] + (self.sun_pos_noon[1] - self.sun_pos_night[1]) * sun_intensity)
        #self.sun_pos = (x, y)

    def get_r_humidity(self):
        days, hours, minutes = self.get_day_time()
        return config.get_y(hours, config.humidity)

    def get_temperature(self):
        days, hours, minutes = self.get_day_time()
        return config.get_y(hours, self.season)

    def calc_shadowmap(self, leaves, sun_dir=(0.5, 1), resolution=10):
        width = config.SCREEN_WIDTH
        height = config.SCREEN_HEIGHT

        res_width = int(width/resolution)
        res_height = int(height/resolution)

        map = np.zeros((res_width, res_height))


        sun_dir_x = sun_dir[0]
        sun_dir_y = sun_dir[1]

        # calc below shadows
        #print(sun_dir_x)
        for leaf in leaves:
            bottom_left = (leaf['x']-leaf['offset_x'],leaf['y']-leaf['offset_y']+leaf['image'].get_height())
            bottom_right = (bottom_left[0] + leaf['image'].get_width(),bottom_left[1])
            # check x below
            for i in range(map.shape[0]):
                for j in range(map.shape[1]):

                    # delta_x for angle
                    delta_x = (j*resolution - bottom_left[1])*sun_dir_x

                    if i*resolution > bottom_left[0]+delta_x and i*resolution < bottom_right[0]+delta_x and j*resolution > bottom_left[1]:
                        #print(bottom_right, bottom_left, i * resolution, j * resolution)
                        map[i,j] += 1
            # cast rays, mark each cell of subset below rect: x: min x + dir_x * delta_y, max x+width + dir_x * delta_y ->  divide by resolution

        # 00000000
        # 01110000
        # 01210000
        # 01210011
        # 01210011


        # the higher the number, the thicker the shadow -> less photon


        #for (x, y), value in np.ndenumerate(map):
        #    print(x, y)

        return map
        # sun_direction
        # leaves
        # 2d shadow array, resolution
        # thickness --> light reduction




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

        day_time = self.get_day_time_t()
        # self.sun_pos_spline.draw(s)
        if day_time > 0 and day_time < 1:
            #sunpos = self.sun_pos_spline.get_point(day_time)

            offset_sunpos = (self.sunpos[0] - self.sun.get_width() / 2, self.sunpos[1] - self.sun.get_height() / 2)
            self.s.blit(self.sun, offset_sunpos)

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
            self.s.blit(self.cloud, (430,-100))
            self.s.blit(self.cloud, (810,-140))
            self.s.blit(self.cloud, (1140,-110))
        if self.state == RAIN:
            self.s.blit(self.cloud_dark, (430,-100))
            self.s.blit(self.cloud_dark, (810,-140))
            self.s.blit(self.cloud_dark, (1140,-110))



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
        #self.draw_clock(screen)
        #self.rain.draw(screen)
        self.nitrate.draw(screen)
        self.sprites.draw(screen)
        for animation in self.animations:
            animation.draw(screen)

    def handle_weather_events(self):
        time = self.gametime.get_time()

        for event in self.weather_events:
            if event["start_time"] <= time:
                self.start_event(event)

    def start_event(self, event):
        self.state = event["type"]
        if self.state == RAIN:
            pygame.mixer.Sound.play(rain_sound, -1)
            self.raining = True
            self.animations[0].running = True
            self.water_grid.activate_rain()
        elif self.state == SUN:
            pygame.mixer.Sound.stop(rain_sound)
            self.raining = False
            self.animations[0].running = False
            self.water_grid.deactivate_rain()
        elif self.state == CLOUD:
            pygame.mixer.Sound.stop(rain_sound)
            self.raining = False
            self.animations[0].running = False
            self.water_grid.deactivate_rain()
        elif self.state == HAWK:
            pass
            #self.activate_hawk()

        self.weather_events.remove(event)

    def get_day_time(self):
        ticks = self.gametime.get_time()
        day = 1000*60*60*24
        hour = day/24
        min = hour/60
        days = int(ticks/day)
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return days, hours, minutes

    def get_sun_intensity(self):
        return -(np.sin(np.pi/2-np.pi/5+((self.gametime.get_time()/(1000 * 60 * 60 * 24)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    def get_day_time_t(self):
        return ((((self.gametime.get_time()/(1000*60*60*24))+0.5-0.333)%1)*2-1)

