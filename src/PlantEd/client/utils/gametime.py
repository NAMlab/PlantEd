import pygame


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError("Singletons must be accessed through `instance()`.")

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


def get_time():
    return pygame.time.get_ticks()


@Singleton
class GameTime:
    def __init__(self):
        self.starttime = pygame.time.get_ticks()
        self.currenttime = self.starttime
        self.GAMESPEED = 360
        self.paused_speed = -1
        self.timediff = (
            0  # used to add sped up or slowed time to the current time
        )
        self.deltatime = self.starttime  # tmp time for states
        self.set_speed(self.GAMESPEED)

    def reset(self):
        self.starttime = pygame.time.get_ticks()
        self.currenttime = self.starttime
        self.GAMESPEED = 360
        self.paused_speed = -1
        self.timediff = (
            0  # used to add sped up or slowed time to the current time
        )
        self.deltatime = self.starttime  # tmp time for states
        self.set_speed(self.GAMESPEED)

    def set_speed(self, speed):
        ticks = pygame.time.get_ticks()
        self.timediff += (
            ticks - self.deltatime
        ) * self.GAMESPEED  # how long the gamespeed has beend altered
        self.deltatime = ticks  # set up
        self.GAMESPEED = speed

    def pause(self):
        self.paused_speed = self.GAMESPEED
        self.set_speed(-1)

    def unpause(self):
        self.set_speed(self.paused_speed)

    def play(self):
        self.set_speed(360)

    def faster(self):
        self.set_speed(2400)

    def fastest(self):
        self.set_speed(4800)

    def get_time(self):
        return (
            pygame.time.get_ticks()
            - self.starttime
            + self.timediff
            + ((pygame.time.get_ticks() - self.deltatime) * self.GAMESPEED)
        )

    @property
    def time_since_start_in_hours(self) -> float:
        """
        Method to get the number of hours elapsed in the game since the game was started.

        Returns: The passed hours as :py:class:`float`.

        """
        ticks = self.get_time()
        hour = 1000 * 60 * 60
        hours = ticks / hour

        return hours


