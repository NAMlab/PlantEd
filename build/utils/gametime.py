import pygame


def get_time():
    return pygame.time.get_ticks()


class GameTime:
    def __init__(self):
        self.starttime = pygame.time.get_ticks()
        self.currenttime = self.starttime
        self.GAMESPEED = 1
        self.pause = False
        self.pause_start = 0
        self.timediff = 0  # used to add sped up or slowed time to the current time
        self.deltatime = self.starttime  # tmp time for states
        self.change_speed(1)

    def change_speed(self, factor=2):
        ticks = pygame.time.get_ticks()
        if self.pause:
            self.pause = False
            self.deltatime -= (ticks - self.pause_start)
        self.timediff += (ticks - self.deltatime) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = ticks  # set up
        self.GAMESPEED *= factor

    def set_speed(self, speed):
        ticks = pygame.time.get_ticks()
        if self.pause:
            self.pause = False
            self.timediff -= (ticks - self.pause_start)
        self.timediff += (ticks - self.deltatime) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = ticks  # set up
        self.GAMESPEED = speed

    def start_pause(self):
        self.GAMESPEED = 0
        self.pause = True
        self.pause_start = pygame.time.get_ticks()

    def play(self):
        self.set_speed(1)

    def faster(self):
        self.set_speed(10)

    def get_time(self):
        if self.pause:
            return self.pause_start - self.starttime + self.timediff + (
                    (pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)
        else:
            return pygame.time.get_ticks() - self.starttime + self.timediff + (
                    (pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)
