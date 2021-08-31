import os
import pygame

# assets is supposed to allow access to images, sounds
# assets also handles options like volume, lists of songs to play or

fileDir = os.path.dirname(os.path.realpath('__file__'))
assets_dir = os.path.join(fileDir, '../assets/')
_image_library = {}


def get_image(path):
    path = os.path.join(assets_dir, path)
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path).convert_alpha()
        _image_library[path] = image
    return image
