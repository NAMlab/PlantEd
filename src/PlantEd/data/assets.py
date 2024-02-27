from pathlib import Path
from typing import Tuple, Optional

import pygame
from pygame.surface import Surface

from PlantEd.client.utils.gametime import Singleton
from PlantEd.constants import SCREEN_WIDTH, SCREEN_HEIGHT

# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

fileDir = Path(__file__)
data_dir = fileDir.parent


# (ctypes.windll.user32.GetSystemMetrics(0),
# ctypes.windll.user32.GetSystemMetrics(1))

@Singleton
class AssetHandler:
    def __init__(self):
        #pygame.display.set_mode((1, 1), pygame.NOFRAME)
        pygame.font.init()
        self._image_library: dict[Tuple[str, Optional[Tuple[int, int]]], Surface] = {}
        self._sound_library = {}
        self._music_library = {}

        ###############################################################################
        # FONTS
        ###############################################################################
        self.FONT_16 = pygame.font.SysFont("timesnewroman", 16)
        self.FONT_20 = pygame.font.SysFont("timesnewroman", 20)
        self.FONT_24 = pygame.font.SysFont("timesnewroman", 24)
        self.FONT_28 = pygame.font.SysFont("timesnewroman", 28)
        self.FONT_32 = pygame.font.SysFont("timesnewroman", 32)
        self.FONT_36 = pygame.font.SysFont("timesnewroman", 36)
        self.MENU_TITLE = pygame.font.SysFont("timesnewroman", 72)
        self.MENU_SUBTITLE = pygame.font.SysFont("timesnewroman", 56)

    def img(self, path, size: Optional[Tuple[int, int]] = None) -> Surface:
        # print(f"path: {path} scale: {size}")

        path = data_dir / "assets" / path
        image = self._image_library.get((path, size))

        # scaled image was already loaded
        if image is not None:
            return image.copy()

        # image wasn't loaded => load unscaled version
        image = pygame.image.load(path).convert_alpha()
        self._image_library[(path, None)] = image.copy()

        # if unscaled was requested return
        if size is None:
            return image

        # scale image and return
        image = pygame.transform.scale(image, size).convert_alpha()
        self._image_library[(path, size)] = image.copy()
        return image

    def sfx(self, path, volume=None):
        path = data_dir / "assets" / path

        sound = self._sound_library.get(path)
        if sound is None:
            # canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
            sound = pygame.mixer.Sound(path)
            self._sound_library[path] = sound
        if volume is not None:
            sound.set_volume(volume)
        return sound

    def song(self, path, volume=None):
        path = data_dir / "assets" / path
        # canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        pygame.mixer.music.load(path)
        if volume is not None:
            pygame.mixer.music.set_volume(volume)
