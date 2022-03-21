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

def img(path, size=None, direction=None):
    path = os.path.join("../assets", path)
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path).convert_alpha()
        _image_library[path] = image
    if size is not None:
        return pygame.transform.scale(image, size).convert_alpha()
    if direction is not None:
        rad = angle_between((0,1),direction)
        deg = rad/math.pi * 180
        return rot_center(image, deg)
    return image

def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::
            angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            angle_between((1, 0, 0), (1, 0, 0))
            0.0
            angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

def rot_center(image, angle):
    x = image.get_width()/2
    y = image.get_height()/2
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)

    return rotated_image, new_rect

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
    global _music_library
    music = _music_library.get(path)
    if music == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        music = pygame.mixer.music.load(canonicalized_path)
        _music_library[path] = music
    if volume is not None:
        music.set_volume(volume)
    return sound
