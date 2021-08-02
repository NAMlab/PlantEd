import pygame
from pygame.locals import *
from particle import ParticleSystem
from animation import OneShotAnimation

SUN = USEREVENT + 1
RAIN = USEREVENT + 2
CLOUD = USEREVENT + 3
WIND = USEREVENT + 4

# Environment can be altered by 4 different events: Sun, Rain, Cloud, Wind
# altering: Temp, H2O, N, Photon_level
# caused by: time
# draw: background, clouds, sun, moon, wind, birds, rain


class Environment:
    def __init__(self, SCREEN_WIDTH, SCREEN_HEIGHT):
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT
        self.sprites = pygame.sprite.Group()
        self.animations = []
        # init drop sprites
        self.drops = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop{}.png".format(i)).convert_alpha(),(20, 20)) for i in range(0, 3)]
        self.splash = [pygame.transform.scale(pygame.image.load("../assets/rain/raindrop_splash{}.png".format(i)).convert_alpha(),(20, 20)) for i in range(0, 4)]
        self.sun = [pygame.transform.scale(pygame.image.load("../assets/sun/sun_face_{}.png".format(i)),(512, 512)).convert_alpha() for i in range(0, 5)]

        '''self.rain = ParticleSystem(100, Rect(SCREEN_WIDTH/2, 0, SCREEN_WIDTH/2, 0),
                                   Rect(SCREEN_WIDTH/2, 0, SCREEN_WIDTH/2, SCREEN_HEIGHT),
                                   None, direction=[0, 1], speed=[5,5], images=drops, despawn_animation=self.add_animation,
                                   despawn_images=splash, active=True)
        '''
        self.rain = ParticleSystem(100, spawn_box=Rect(SCREEN_WIDTH / 2, 0, SCREEN_WIDTH/3*2, 0),
                                    boundary_box=Rect(SCREEN_WIDTH/3,0,SCREEN_WIDTH/3*2,SCREEN_HEIGHT-250),
                                    color=(0,0,100), apply_gravity=False, speed=[0, 5],
                                    active=True, images=self.drops, despawn_images=self.splash, despawn_animation=self.add_animation)


    def update(self, dt, game_time, sun_intensity):
        self.sun_intensity = sun_intensity
        self.game_time = game_time
        for animation in self.animations:
            animation.update()
        self.rain.update(dt)
        for sprite in self.sprites:
            # sprites are able to cancle themselves, OneShotAnimation / Animation (loop)
            if not sprite.update():
                self.sprites.remove(sprite) # dumb to remove during iteration, maybe don't

    def draw_background(self, screen):
        # sun-->Photon_intensity, moon, water_lvl
        sun_index = 0#max(int(self.sun_intensity*len(sun)),4)
        screen.blit(self.sun[sun_index], (self.w/4*3, 0))

    def draw_foreground(self, screen):
        self.rain.draw(screen)
        self.sprites.draw(screen)

    def activate_rain(self):
        self.rain.deactivate()

    def deactivate_rain(self):
        self.rain.deactivate()


    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))

'''class WeatherSystem:
    def __init__(self, game):
        self.game = game
        self.index = 0
        self.event_list = self.build_example()
        self.last_event_time = pygame.time.get_ticks()
        self.current_event = self.event_list[self.index]
        event_time = int(self.event_list[self.index].duration / 4 * 60 * 1000)
        pygame.time.set_timer(self.event_list[self.index], event_time, True)  # 12h --> 6min

    def handle_event(self, event):
        if event.type == SUN or event.type == RAIN or event.type == CLOUD:
            if event.type == SUN:
                pass
            if event.type == RAIN:
                pass
            if event.type == CLOUD:
                pass
            # self.game.particle_systems.append(
            # ParticleSystem(50, Rect(0, 0, self.game.width, 20), Rect(0, 0, self.game.width, self.game.height), (0,0,0), lifetime=2000))
            self.post_next_event()

    def get_start_time(self, event_id=None, event=None):
        if event_id < self.index:
            return 0
        start_time = 0
        if event_id is None:
            event_id = self.event_list.index(event)
        for weather_event in self.event_list[self.index:event_id]:  # [range(self.index, event_id)]:
            if self.event_list.index(weather_event) == self.index:
                start_time = start_time + (self.current_event.duration / 4 * 60 * 1000 - pygame.time.get_ticks() - self.last_event_time)
            else:
                start_time = start_time + (weather_event.duration / 4 * 60 * 1000)
        return start_time

    def get_start_times(self):
        start_times = []
        for i in range(self.index, len(self.event_list)):
            start_times.append(self.event_list[i])

    def build_example(self):
        event_list = [pygame.event.Event(SUN, message="S1", duration=1),
                      pygame.event.Event(RAIN, message="R1", duration=2),
                      pygame.event.Event(SUN, message="S2", duration=1),
                      pygame.event.Event(CLOUD, message="C1", duration=1),
                      pygame.event.Event(RAIN, message="W2", duration=1),
                      pygame.event.Event(SUN, message="S2", duration=2),
                      pygame.event.Event(CLOUD, message="C2", duration=1)]

        return event_list

    def post_next_event(self):
        if self.index + 1 >= len(self.event_list):
            return
        self.index += 1
        self.last_event_time = pygame.time.get_ticks()
        self.current_event = self.event_list[self.index]
        event_time = int(self.event_list[self.index].duration / 4 * 60 * 1000)
        pygame.time.set_timer(self.event_list[self.index], event_time, True)  # 12h --> 6min
'''