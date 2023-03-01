import os
from pathlib import Path

import pygame
#import ctypes
import numpy as np
import math
# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

fileDir = Path(__file__)
data_dir = fileDir.parent
_image_library = {}
_sound_library = {}
_music_library = {}

pygame.init()



true_res = (1920,1080)#(ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)

def img(path, size=None):
    path = data_dir / "assets" / path
    global _image_library
    image = _image_library.get(path)
    if image == None:
        #canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(path).convert_alpha()
        _image_library[path] = image
    if size is not None:
        if not (image.get_width() == size[0] and image.get_height() == size[1]):
            return pygame.transform.scale(image, size).convert_alpha()
    return image

def sfx(path, volume=None):
    path = data_dir / "assets" / path

    global _sound_library
    sound = _sound_library.get(path)
    if sound == None:
        #canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        sound = pygame.mixer.Sound(path)
        _sound_library[path] = sound
    if volume is not None:
        sound.set_volume(volume)
    return sound

def song(path, volume=None):
    path = data_dir / "assets" / path

    #canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
    pygame.mixer.music.load(path)
    if volume is not None:
        pygame.mixer.music.set_volume(volume)
