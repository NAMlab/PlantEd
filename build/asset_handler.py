import os
import pygame
import ctypes
# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

fileDir = os.path.dirname(os.path.realpath('__file__'))
assets_dir = os.path.join(fileDir, './assets/')
_image_library = {}
_sound_library = {}

pygame.init()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)

def get_image(path):
    path = os.path.join(assets_dir, path)
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path).convert_alpha()
        _image_library[path] = image
    return image

def get_sound(path):
    path = os.path.join(assets_dir, path)
    global _sound_library
    sound = _sound_library.get(path)
    if sound == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        sound = pygame.mixer.Sound(canonicalized_path)
        _sound_library[path] = sound
    return sound

def get_music(path):
    path = os.path.join(assets_dir, path)
    global _music_library
    music = _music_library.get(path)
    if music == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        music = pygame.mixer.music.load(canonicalized_path)
        _music_library[path] = music
    return sound