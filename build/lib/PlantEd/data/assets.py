from pathlib import Path
from typing import Tuple, Optional

import pygame
from pygame.surface import Surface

# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

fileDir = Path(__file__)
data_dir = fileDir.parent
_image_library: dict[Tuple[str, Optional[Tuple[int, int]]], Surface] = {}
_sound_library = {}
_music_library = {}

# pygame.init()


true_res = (
    1920,
    1080,
)
# (ctypes.windll.user32.GetSystemMetrics(0),
# ctypes.windll.user32.GetSystemMetrics(1))

pygame.display.set_mode((1,1), pygame.NOFRAME)

def img(path, size: Optional[Tuple[int, int]] = None):
    # print(f"path: {path} scale: {size}")

    path = data_dir / "assets" / path
    global _image_library
    image = _image_library.get((path, size))

    # scaled image was already loaded
    if image is not None:
        return image.copy()

    # image wasn't loaded => load unscaled version
    image = pygame.image.load(path).convert_alpha()
    _image_library[(path, None)] = image.copy()

    # if unscaled was requested return
    if size is None:
        return image

    # scale image and return
    image = pygame.transform.scale(image, size).convert_alpha()
    _image_library[(path, size)] = image.copy()
    return image


def sfx(path, volume=None):
    path = data_dir / "assets" / path

    global _sound_library
    sound = _sound_library.get(path)
    if sound is None:
        # canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        sound = pygame.mixer.Sound(path)
        _sound_library[path] = sound
    if volume is not None:
        sound.set_volume(volume)
    return sound


def song(path, volume=None):
    path = data_dir / "assets" / path

    # canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
    pygame.mixer.music.load(path)
    if volume is not None:
        pygame.mixer.music.set_volume(volume)
