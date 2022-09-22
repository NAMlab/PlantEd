import os
import pygame
import ctypes
import numpy as np
import math
# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

#fileDir = os.path.dirname(os.path.realpath('__file__'))
#assets_dir = os.path.join(fileDir, 'assets')
_image_library = {}
_sound_library = {}
_music_library = {}

pygame.init()



true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)

def img(path, size=None):
    path = os.path.join("../assets", path)
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path).convert_alpha()
        _image_library[path] = image
    if size is not None:
        if not (image.get_width() == size[0] and image.get_height() == size[1]):
            return pygame.transform.scale(image, size).convert_alpha()
    return image

def sfx(path, volume=None):
    path = os.path.join("../assets", path)
    global _sound_library
    sound = _sound_library.get(path)
    if sound == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        sound = pygame.mixer.Sound(canonicalized_path)
        _sound_library[path] = sound
    if volume is not None:
        sound.set_volume(volume)
    return sound

def song(path, volume=None):
    path = os.path.join("../assets", path)
    canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
    pygame.mixer.music.load(canonicalized_path)
    if volume is not None:
        pygame.mixer.music.set_volume(volume)
